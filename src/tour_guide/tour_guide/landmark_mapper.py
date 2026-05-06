"""Build a YAML landmark map from ArUco marker detections.

Expected input is a PoseArray-style topic from ros2_aruco. Each detected marker is
stored as a map-frame tour stop, then written to a YAML file that navnode.py can
load. This gives the project a real sweep/detect/map phase without rewriting
Nav2 or building a custom global planner.
"""

from __future__ import annotations

import argparse
import math
from pathlib import Path
from typing import Dict, Optional, Tuple

import rclpy
import yaml
from geometry_msgs.msg import PoseArray, PoseStamped, TransformStamped
from rclpy.duration import Duration
from rclpy.node import Node
from tf2_ros import Buffer, TransformException, TransformListener


def quaternion_to_yaw(z: float, w: float) -> float:
    return math.atan2(2.0 * w * z, 1.0 - 2.0 * z * z)


def yaw_to_quaternion(yaw: float) -> Tuple[float, float]:
    return math.sin(yaw / 2.0), math.cos(yaw / 2.0)


def apply_transform(pose: PoseStamped, transform: TransformStamped) -> PoseStamped:
    """2-D transform sufficient for TurtleBot tour goals on a flat map."""
    tx = transform.transform.translation.x
    ty = transform.transform.translation.y
    theta = quaternion_to_yaw(transform.transform.rotation.z, transform.transform.rotation.w)

    x = pose.pose.position.x
    y = pose.pose.position.y

    out = PoseStamped()
    out.header.frame_id = transform.header.frame_id
    out.header.stamp = pose.header.stamp
    out.pose.position.x = tx + math.cos(theta) * x - math.sin(theta) * y
    out.pose.position.y = ty + math.sin(theta) * x + math.cos(theta) * y
    out.pose.position.z = 0.0

    marker_yaw = quaternion_to_yaw(pose.pose.orientation.z, pose.pose.orientation.w)
    qz, qw = yaw_to_quaternion(theta + marker_yaw)
    out.pose.orientation.z = qz
    out.pose.orientation.w = qw
    return out


class LandmarkMapper(Node):
    def __init__(self, args):
        super().__init__("landmark_mapper")
        self.output = Path(args.output).expanduser().resolve()
        self.topic = args.topic
        self.map_frame = args.map_frame
        self.stop_offset = float(args.stop_offset)
        self.marker_prefix = args.marker_prefix
        self.marker_ids = [int(x) for x in args.marker_ids.split(",") if x.strip()] if args.marker_ids else []
        self.landmarks: Dict[int, Dict[str, float | int | str]] = {}

        self.tf_buffer = Buffer(cache_time=Duration(seconds=10.0))
        self.tf_listener = TransformListener(self.tf_buffer, self)
        self.sub = self.create_subscription(PoseArray, self.topic, self.pose_array_callback, 10)
        self.timer = self.create_timer(float(args.write_period), self.write_yaml)

        self.get_logger().info(f"Listening for ArUco detections on {self.topic}")
        self.get_logger().info(f"Writing discovered landmarks to {self.output}")

    def marker_id_for_index(self, index: int) -> int:
        if index < len(self.marker_ids):
            return self.marker_ids[index]
        return index

    def transform_to_map(self, pose: PoseStamped) -> Optional[PoseStamped]:
        if not pose.header.frame_id:
            self.get_logger().warn("Detection pose has no frame_id; cannot transform to map.", throttle_duration_sec=5.0)
            return None
        try:
            transform = self.tf_buffer.lookup_transform(
                self.map_frame,
                pose.header.frame_id,
                rclpy.time.Time(),
                timeout=Duration(seconds=0.25),
            )
            return apply_transform(pose, transform)
        except TransformException as exc:
            self.get_logger().warn(f"No transform {self.map_frame} <- {pose.header.frame_id}: {exc}", throttle_duration_sec=5.0)
            return None

    def pose_array_callback(self, msg: PoseArray) -> None:
        if not msg.poses:
            return

        updated = False
        for index, detected_pose in enumerate(msg.poses):
            marker_id = self.marker_id_for_index(index)
            stamped = PoseStamped()
            stamped.header = msg.header
            stamped.pose = detected_pose

            map_pose = self.transform_to_map(stamped)
            if map_pose is None:
                continue

            marker_x = float(map_pose.pose.position.x)
            marker_y = float(map_pose.pose.position.y)

            # Put the robot stop point slightly in front of the marker instead of
            # trying to drive into the wall/cardboard landmark.
            yaw_to_marker = math.atan2(marker_y, marker_x)
            stop_x = marker_x - self.stop_offset * math.cos(yaw_to_marker)
            stop_y = marker_y - self.stop_offset * math.sin(yaw_to_marker)
            face_yaw = math.atan2(marker_y - stop_y, marker_x - stop_x)

            self.landmarks[marker_id] = {
                "name": f"{self.marker_prefix} {marker_id}",
                "marker_id": marker_id,
                "x": round(stop_x, 3),
                "y": round(stop_y, 3),
                "yaw": round(face_yaw, 3),
                "description": f"Detected ArUco marker {marker_id}",
            }
            updated = True

        if updated:
            ids = ", ".join(str(k) for k in sorted(self.landmarks))
            self.get_logger().info(f"Discovered/updated markers: {ids}")

    def write_yaml(self) -> None:
        if not self.landmarks:
            return
        self.output.parent.mkdir(parents=True, exist_ok=True)
        ordered = [self.landmarks[key] for key in sorted(self.landmarks)]
        data = {
            "landmarks": ordered,
            "notes": "Generated by tour_guide landmark_mapper from ArUco detections.",
        }
        with self.output.open("w", encoding="utf-8") as handle:
            yaml.safe_dump(data, handle, sort_keys=False)
        self.get_logger().info(f"Wrote {len(ordered)} landmarks to {self.output}")


def parse_args(argv=None):
    parser = argparse.ArgumentParser(description="Create a tour landmark YAML from ArUco detections.")
    parser.add_argument("--topic", default="/aruco_poses", help="PoseArray topic from the ArUco detector.")
    parser.add_argument("--output", default="~/ros2_ws/FinalRobotProject/landmarks/discovered_locations.yaml")
    parser.add_argument("--map-frame", default="map")
    parser.add_argument("--stop-offset", type=float, default=0.65, help="Meters to stop in front of each marker.")
    parser.add_argument("--write-period", type=float, default=2.0)
    parser.add_argument("--marker-prefix", default="Landmark")
    parser.add_argument("--marker-ids", default="", help="Optional comma list matching PoseArray order, e.g. 0,1,2,3")
    return parser.parse_args(argv)


def main(args=None):
    cli = parse_args(args)
    rclpy.init(args=args)
    node = LandmarkMapper(cli)
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.write_yaml()
        node.destroy_node()
        rclpy.shutdown()


if __name__ == "__main__":
    main()
