from __future__ import annotations

import argparse
import math
from pathlib import Path

import rclpy
import yaml
from geometry_msgs.msg import PoseStamped
from rclpy.duration import Duration
from rclpy.node import Node
from ros2_aruco_interfaces.msg import ArucoMarkers
from tf2_ros import Buffer, TransformException, TransformListener


class LandmarkMapper(Node):
    def __init__(self, args):
        super().__init__('landmark_mapper')
        self.output = Path(args.output).expanduser().resolve()
        self.topic = args.topic
        self.map_frame = args.map_frame
        self.stop_offset = args.stop_offset
        self.no_tf = args.no_tf
        self.landmarks = {}

        self.tf_buffer = Buffer(cache_time=Duration(seconds=10.0))
        self.tf_listener = TransformListener(self.tf_buffer, self)
        self.create_subscription(ArucoMarkers, self.topic, self.callback, 10)
        self.create_timer(args.write_period, self.write_yaml)

        self.get_logger().info(f'Listening on {self.topic}')
        self.get_logger().info(f'Writing to {self.output}')

    def pose_to_map_xy(self, msg, pose):
        if self.no_tf:
            return pose.position.x, pose.position.y

        if not msg.header.frame_id:
            self.get_logger().warn('ArUco message has empty frame_id', throttle_duration_sec=5.0)
            return None

        try:
            tf = self.tf_buffer.lookup_transform(
                self.map_frame,
                msg.header.frame_id,
                rclpy.time.Time(),
                timeout=Duration(seconds=0.25),
            )
        except TransformException as exc:
            self.get_logger().warn(
                f'No TF {self.map_frame} <- {msg.header.frame_id}: {exc}',
                throttle_duration_sec=5.0,
            )
            return None

        theta = 2.0 * math.atan2(tf.transform.rotation.z, tf.transform.rotation.w)
        tx = tf.transform.translation.x
        ty = tf.transform.translation.y
        x = pose.position.x
        y = pose.position.y
        map_x = tx + math.cos(theta) * x - math.sin(theta) * y
        map_y = ty + math.sin(theta) * x + math.cos(theta) * y
        return map_x, map_y

    def callback(self, msg):
        if not msg.marker_ids or not msg.poses:
            return

        count = min(len(msg.marker_ids), len(msg.poses))
        for i in range(count):
            marker_id = int(msg.marker_ids[i])
            result = self.pose_to_map_xy(msg, msg.poses[i])
            if result is None:
                continue

            marker_x, marker_y = result
            yaw = math.atan2(marker_y, marker_x)
            stop_x = marker_x - self.stop_offset * math.cos(yaw)
            stop_y = marker_y - self.stop_offset * math.sin(yaw)

            self.landmarks[marker_id] = {
                'name': f'Landmark {marker_id}',
                'marker_id': marker_id,
                'x': round(stop_x, 3),
                'y': round(stop_y, 3),
                'yaw': round(yaw, 3),
                'description': f'Detected ArUco marker {marker_id}',
            }

        if self.landmarks:
            ids = ', '.join(str(k) for k in sorted(self.landmarks))
            self.get_logger().info(f'Detected markers: {ids}')

    def write_yaml(self):
        if not self.landmarks:
            return

        self.output.parent.mkdir(parents=True, exist_ok=True)
        data = {
            'landmarks': [self.landmarks[k] for k in sorted(self.landmarks)],
            'notes': 'Generated from /aruco_markers.',
        }
        with self.output.open('w', encoding='utf-8') as f:
            yaml.safe_dump(data, f, sort_keys=False)
        self.get_logger().info(f'Wrote {len(self.landmarks)} landmarks')


def main(args=None):
    parser = argparse.ArgumentParser()
    parser.add_argument('--topic', default='/aruco_markers')
    parser.add_argument('--output', default='~/ros2_ws/FinalRobotProject/landmarks/discovered_locations.yaml')
    parser.add_argument('--map-frame', default='map')
    parser.add_argument('--stop-offset', type=float, default=0.65)
    parser.add_argument('--write-period', type=float, default=2.0)
    parser.add_argument('--no-tf', action='store_true')
    parsed = parser.parse_args(args)

    rclpy.init(args=args)
    node = LandmarkMapper(parsed)
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.write_yaml()
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
