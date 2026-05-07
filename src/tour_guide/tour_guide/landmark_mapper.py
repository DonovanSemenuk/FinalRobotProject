from __future__ import annotations

import argparse
import math
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Optional, Tuple

import rclpy
import yaml
from geometry_msgs.msg import Twist, TwistStamped
from rclpy.duration import Duration
from rclpy.node import Node
from ros2_aruco_interfaces.msg import ArucoMarkers
from tf2_ros import Buffer, TransformException, TransformListener


@dataclass
class LandmarkStats:
    marker_id: int
    samples: int = 0
    marker_x_sum: float = 0.0
    marker_y_sum: float = 0.0
    stop_x_sum: float = 0.0
    stop_y_sum: float = 0.0
    yaw_x_sum: float = 0.0
    yaw_y_sum: float = 0.0

    def add(self, marker_x: float, marker_y: float, stop_x: float, stop_y: float, yaw: float) -> None:
        self.samples += 1
        self.marker_x_sum += marker_x
        self.marker_y_sum += marker_y
        self.stop_x_sum += stop_x
        self.stop_y_sum += stop_y
        self.yaw_x_sum += math.cos(yaw)
        self.yaw_y_sum += math.sin(yaw)

    def as_landmark(self) -> dict:
        yaw = math.atan2(self.yaw_y_sum, self.yaw_x_sum)
        return {
            'name': f'Landmark {self.marker_id}',
            'marker_id': self.marker_id,
            'x': round(self.stop_x_sum / self.samples, 3),
            'y': round(self.stop_y_sum / self.samples, 3),
            'yaw': round(yaw, 3),
            'samples': self.samples,
            'description': f'Detected ArUco marker {self.marker_id}',
        }


class LandmarkMapper(Node):
    def __init__(self, args):
        super().__init__('landmark_mapper')
        self.output = Path(args.output).expanduser().resolve()
        self.topic = args.topic
        self.map_frame = args.map_frame
        self.base_frame = args.base_frame
        self.stop_offset = args.stop_offset
        self.no_tf = args.no_tf
        self.min_samples = max(1, args.min_samples)
        self.landmarks: dict[int, LandmarkStats] = {}

        self.tf_buffer = Buffer(cache_time=Duration(seconds=10.0))
        self.tf_listener = TransformListener(self.tf_buffer, self)
        self.create_subscription(ArucoMarkers, self.topic, self.callback, 10)
        self.create_timer(args.write_period, self.write_yaml)

        self.sweep_enabled = args.sweep
        self.sweep_started_at: Optional[float] = None
        self.sweep_duration = 0.0
        self.sweep_speed = abs(args.angular_speed)
        self.sweep_done_logged = False
        self.cmd_vel_stamped = not args.unstamped_cmd_vel
        self.cmd_vel_topic = args.cmd_vel_topic
        msg_type = TwistStamped if self.cmd_vel_stamped else Twist
        self.cmd_pub = self.create_publisher(msg_type, self.cmd_vel_topic, 10)
        if self.sweep_enabled:
            if self.sweep_speed <= 0.0:
                raise ValueError('--angular-speed must be greater than zero')
            self.sweep_duration = abs((2.0 * math.pi * args.sweep_revolutions) / self.sweep_speed)
            self.create_timer(0.1, self.sweep_step)
            self.get_logger().info(
                f'Sweep enabled: {args.sweep_revolutions:.2f} rev at {self.sweep_speed:.2f} rad/s '
                f'for about {self.sweep_duration:.1f} s using '
                f'{"TwistStamped" if self.cmd_vel_stamped else "Twist"} on {self.cmd_vel_topic}'
            )

        self.get_logger().info(f'Listening on {self.topic}')
        self.get_logger().info(f'Writing to {self.output}')

    @staticmethod
    def yaw_from_quaternion(q) -> float:
        return math.atan2(
            2.0 * (q.w * q.z + q.x * q.y),
            1.0 - 2.0 * (q.y * q.y + q.z * q.z),
        )

    def make_cmd_vel(self, angular_z: float):
        if self.cmd_vel_stamped:
            msg = TwistStamped()
            msg.header.stamp = self.get_clock().now().to_msg()
            msg.header.frame_id = self.base_frame
            msg.twist.angular.z = angular_z
            return msg

        msg = Twist()
        msg.angular.z = angular_z
        return msg

    def publish_stop(self) -> None:
        self.cmd_pub.publish(self.make_cmd_vel(0.0))

    def lookup_transform(self, target: str, source: str):
        return self.tf_buffer.lookup_transform(
            target,
            source,
            rclpy.time.Time(),
            timeout=Duration(seconds=0.25),
        )

    def transform_xy_to_map(self, msg, pose) -> Optional[Tuple[float, float]]:
        if self.no_tf:
            return pose.position.x, pose.position.y

        if not msg.header.frame_id:
            self.get_logger().warn('ArUco message has empty frame_id', throttle_duration_sec=5.0)
            return None

        try:
            tf = self.lookup_transform(self.map_frame, msg.header.frame_id)
        except TransformException as exc:
            self.get_logger().warn(
                f'No TF {self.map_frame} <- {msg.header.frame_id}: {exc}',
                throttle_duration_sec=5.0,
            )
            return None

        yaw = self.yaw_from_quaternion(tf.transform.rotation)
        tx = tf.transform.translation.x
        ty = tf.transform.translation.y
        x = pose.position.x
        y = pose.position.y
        return (
            tx + math.cos(yaw) * x - math.sin(yaw) * y,
            ty + math.sin(yaw) * x + math.cos(yaw) * y,
        )

    def robot_xy_in_map(self) -> Tuple[float, float]:
        if self.no_tf:
            return 0.0, 0.0

        candidate_frames = [self.base_frame]
        if self.base_frame != 'base_footprint':
            candidate_frames.append('base_footprint')
        if self.base_frame != 'base_link':
            candidate_frames.append('base_link')

        last_error = None
        for frame in candidate_frames:
            try:
                tf = self.lookup_transform(self.map_frame, frame)
                return tf.transform.translation.x, tf.transform.translation.y
            except TransformException as exc:
                last_error = exc

        raise TransformException(f'No robot base TF available: {last_error}')

    def compute_stop_pose(self, marker_x: float, marker_y: float) -> Optional[Tuple[float, float, float]]:
        try:
            robot_x, robot_y = self.robot_xy_in_map()
        except TransformException as exc:
            self.get_logger().warn(f'Cannot place stop pose without robot pose: {exc}', throttle_duration_sec=5.0)
            return None

        dx = marker_x - robot_x
        dy = marker_y - robot_y
        distance = math.hypot(dx, dy)
        if distance < 1e-3:
            self.get_logger().warn('Marker and robot positions are nearly identical; skipping sample')
            return None

        ux = dx / distance
        uy = dy / distance
        stop_x = marker_x - self.stop_offset * ux
        stop_y = marker_y - self.stop_offset * uy
        yaw = math.atan2(marker_y - stop_y, marker_x - stop_x)
        return stop_x, stop_y, yaw

    def callback(self, msg):
        if not msg.marker_ids or not msg.poses:
            return

        count = min(len(msg.marker_ids), len(msg.poses))
        updated = False
        for i in range(count):
            marker_id = int(msg.marker_ids[i])
            marker_xy = self.transform_xy_to_map(msg, msg.poses[i])
            if marker_xy is None:
                continue

            marker_x, marker_y = marker_xy
            stop_pose = self.compute_stop_pose(marker_x, marker_y)
            if stop_pose is None:
                continue

            stop_x, stop_y, yaw = stop_pose
            stats = self.landmarks.setdefault(marker_id, LandmarkStats(marker_id=marker_id))
            stats.add(marker_x, marker_y, stop_x, stop_y, yaw)
            updated = True

        if updated:
            ids = ', '.join(f'{k}({self.landmarks[k].samples})' for k in sorted(self.landmarks))
            self.get_logger().info(f'Detected markers with sample counts: {ids}', throttle_duration_sec=2.0)

    def sweep_step(self):
        if not self.sweep_enabled:
            return

        now = time.monotonic()
        if self.sweep_started_at is None:
            self.sweep_started_at = now

        elapsed = now - self.sweep_started_at
        if elapsed < self.sweep_duration:
            self.cmd_pub.publish(self.make_cmd_vel(self.sweep_speed))
            return

        self.publish_stop()
        self.sweep_enabled = False
        self.write_yaml()
        if not self.sweep_done_logged:
            self.sweep_done_logged = True
            self.get_logger().info('Sweep complete. Stop the mapper with Ctrl+C or run the tour node.')

    def write_yaml(self):
        usable = [stats.as_landmark() for _, stats in sorted(self.landmarks.items()) if stats.samples >= self.min_samples]
        if not usable:
            return

        self.output.parent.mkdir(parents=True, exist_ok=True)
        data = {'landmarks': usable}
        with self.output.open('w', encoding='utf-8') as f:
            yaml.safe_dump(data, f, sort_keys=False)
        self.get_logger().info(f'Wrote {len(usable)} landmarks to {self.output}')


def main(args=None):
    parser = argparse.ArgumentParser(description='Discover ArUco landmarks and save Nav2 stop poses.')
    parser.add_argument('--topic', default='/aruco_markers')
    parser.add_argument('--output', default='~/ros2_ws/FinalRobotProject/landmarks/discovered_locations.yaml')
    parser.add_argument('--map-frame', default='map')
    parser.add_argument('--base-frame', default='base_link')
    parser.add_argument('--stop-offset', type=float, default=0.65)
    parser.add_argument('--min-samples', type=int, default=3)
    parser.add_argument('--write-period', type=float, default=2.0)
    parser.add_argument('--no-tf', action='store_true')
    parser.add_argument('--sweep', action='store_true', help='Slowly rotate the robot while collecting marker detections.')
    parser.add_argument('--sweep-revolutions', type=float, default=1.0)
    parser.add_argument('--angular-speed', type=float, default=0.35)
    parser.add_argument('--cmd-vel-topic', default='/cmd_vel')
    parser.add_argument(
        '--unstamped-cmd-vel',
        action='store_true',
        help='Publish geometry_msgs/Twist instead of TwistStamped for older command-velocity bridges.',
    )
    parsed = parser.parse_args(args)

    rclpy.init(args=args)
    node = LandmarkMapper(parsed)
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.publish_stop()
        node.write_yaml()
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
