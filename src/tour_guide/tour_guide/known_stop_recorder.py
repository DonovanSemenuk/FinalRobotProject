from __future__ import annotations

import argparse
import math
from pathlib import Path
from typing import Any

import rclpy
import yaml
from geometry_msgs.msg import PointStamped
from rclpy.node import Node


class KnownStopRecorder(Node):
    def __init__(self, args: argparse.Namespace) -> None:
        super().__init__('known_stop_recorder')
        self.output = Path(args.output).expanduser().resolve()
        self.topic = args.topic
        self.stop_prefix = args.prefix
        self.default_yaw = float(args.yaw)
        self.description = args.description
        self.required_frame = args.frame
        self.stops = self.load_existing_stops()

        self.create_subscription(PointStamped, self.topic, self.point_callback, 10)
        self.get_logger().info(f'Listening for RViz clicked points on {self.topic}')
        self.get_logger().info(f'Writing tour stops to {self.output}')
        self.get_logger().info('In RViz, use Publish Point and click open floor locations, not walls or furniture.')

    def load_existing_stops(self) -> list[dict[str, Any]]:
        if not self.output.exists():
            return []
        with self.output.open('r', encoding='utf-8') as handle:
            data = yaml.safe_load(handle) or {}
        raw = data.get('landmarks', [])
        if not isinstance(raw, list):
            raise ValueError(f'Invalid landmark YAML format in {self.output}')
        return raw

    def point_callback(self, msg: PointStamped) -> None:
        frame = msg.header.frame_id or self.required_frame
        if frame != self.required_frame:
            self.get_logger().warn(
                f'Ignoring clicked point in frame {frame!r}; expected {self.required_frame!r}. '
                'Set RViz Fixed Frame to map.'
            )
            return

        index = len(self.stops) + 1
        stop = {
            'name': f'{self.stop_prefix} {index}',
            'x': round(float(msg.point.x), 3),
            'y': round(float(msg.point.y), 3),
            'yaw': round(self.default_yaw, 3),
            'description': self.description or f'Manually selected classroom tour stop {index}.',
        }
        self.stops.append(stop)
        self.write_file()
        self.get_logger().info(
            f"Saved {stop['name']} at x={stop['x']:.3f}, y={stop['y']:.3f}, yaw={stop['yaw']:.3f}"
        )

    def write_file(self) -> None:
        self.output.parent.mkdir(parents=True, exist_ok=True)
        data = {'landmarks': self.stops}
        with self.output.open('w', encoding='utf-8') as handle:
            yaml.safe_dump(data, handle, sort_keys=False)


def parse_args(argv=None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description='Save RViz clicked points as tour landmark YAML.')
    parser.add_argument('--topic', default='/clicked_point')
    parser.add_argument('--output', default='~/ros2_ws/FinalRobotProject/landmarks/discovered_locations.yaml')
    parser.add_argument('--frame', default='map')
    parser.add_argument('--prefix', default='Classroom Stop')
    parser.add_argument('--yaw', type=float, default=0.0)
    parser.add_argument('--description', default='')
    return parser.parse_args(argv)


def main(args=None) -> None:
    parsed = parse_args(args)
    rclpy.init(args=None)
    node = KnownStopRecorder(parsed)
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
