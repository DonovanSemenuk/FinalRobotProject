#!/usr/bin/env python3

import json
import math
import os
import time
from typing import Dict, Optional

import rclpy
from rclpy.action import ActionClient
from rclpy.node import Node

from nav_msgs.msg import Odometry
from irobot_create_msgs.action import NavigateToPosition
from ros2_aruco_interfaces.msg import ArucoMarkers


class TourGuideNode(Node):
    """
    TurtleBot 4 Tour Guide Node.

    Modes:
    - ArUco landmark registration from /aruco_markers.
    - Manual landmark registration from current /odom pose.
    - Fixed fallback tour with conservative odom-frame goals.
    """

    def __init__(self):
        super().__init__('tour_guide_node')

        self.navigator_client = ActionClient(self, NavigateToPosition, '/navigate_to_position')

        self.odom_sub = self.create_subscription(Odometry, '/odom', self.odom_callback, 10)
        self.aruco_sub = self.create_subscription(ArucoMarkers, '/aruco_markers', self.aruco_callback, 10)

        self.current_pose: Optional[Dict[str, float]] = None
        self.landmarks: Dict[int, Dict] = {}
        self.landmark_file = os.path.expanduser('~/ros2_ws/FinalRobotProject/landmarks/landmarks.json')

        self.default_descriptions = {
            0: 'Entrance Area: This is the beginning of the TurtleBot tour route.',
            1: 'Classroom Work Area: This stop represents the main classroom workspace.',
            2: 'Demonstration Area: This is where the robot demonstrates the tour-guide system.',
            3: 'Final Stop: This is the conclusion of the TurtleBot tour.',
        }

        self.fixed_demo_stops = {
            1: {'name': 'Entrance Area', 'description': 'This is the beginning of the TurtleBot tour route.', 'x': 0.20, 'y': 0.0, 'yaw': 0.0},
            2: {'name': 'Classroom Work Area', 'description': 'This stop represents the main classroom workspace and project area.', 'x': 0.35, 'y': 0.0, 'yaw': 0.0},
            3: {'name': 'Demonstration Area', 'description': 'This is where the robot demonstrates the tour-guide software.', 'x': 0.50, 'y': 0.0, 'yaw': 0.0},
            4: {'name': 'Final Stop', 'description': 'This final stop concludes the TurtleBot 4 tour-guide demonstration.', 'x': 0.65, 'y': 0.0, 'yaw': 0.0},
        }

        self.get_logger().info('Tour guide node started.')
        self.get_logger().info('Listening to /odom and /aruco_markers.')
        self.get_logger().info('Using /navigate_to_position for movement.')

    def announce(self, message: str):
        print('\n' + '=' * 78)
        print(message)
        print('=' * 78 + '\n')

    def quaternion_to_yaw(self, q) -> float:
        siny_cosp = 2.0 * (q.w * q.z + q.x * q.y)
        cosy_cosp = 1.0 - 2.0 * (q.y * q.y + q.z * q.z)
        return math.atan2(siny_cosp, cosy_cosp)

    def yaw_to_quaternion(self, yaw: float):
        qz = math.sin(yaw / 2.0)
        qw = math.cos(yaw / 2.0)
        return qz, qw

    def odom_callback(self, msg: Odometry):
        pose = msg.pose.pose
        self.current_pose = {
            'x': float(pose.position.x),
            'y': float(pose.position.y),
            'yaw': float(self.quaternion_to_yaw(pose.orientation)),
        }

    def aruco_callback(self, msg: ArucoMarkers):
        if self.current_pose is None:
            return

        for marker_id_raw in msg.marker_ids:
            marker_id = int(marker_id_raw)

            if marker_id not in self.landmarks:
                description = self.default_descriptions.get(
                    marker_id,
                    f'Marker {marker_id}: This is a relocatable ArUco tour landmark.'
                )
                self.landmarks[marker_id] = {
                    'id': marker_id,
                    'name': f'ArUco Landmark {marker_id}',
                    'description': description,
                    'x': self.current_pose['x'],
                    'y': self.current_pose['y'],
                    'yaw': self.current_pose['yaw'],
                    'source': 'aruco',
                    'times_seen': 1,
                }
                self.get_logger().info(
                    f'Registered ArUco marker {marker_id} at viewing pose '
                    f'x={self.current_pose["x"]:.2f}, y={self.current_pose["y"]:.2f}, '
                    f'yaw={self.current_pose["yaw"]:.2f}'
                )
            else:
                self.landmarks[marker_id]['times_seen'] += 1

    def wait_for_pose(self, timeout_sec: float = 5.0) -> bool:
        start_time = time.time()
        while rclpy.ok() and self.current_pose is None:
            rclpy.spin_once(self, timeout_sec=0.1)
            if time.time() - start_time > timeout_sec:
                return False
        return self.current_pose is not None

    def next_manual_landmark_id(self) -> int:
        if not self.landmarks:
            return 100
        return max(self.landmarks.keys()) + 1

    def manual_register_landmark(self):
        if not self.wait_for_pose():
            self.announce('No /odom pose received. Cannot register landmark.')
            return

        name = input('Landmark name: ').strip() or f'Manual Landmark {len(self.landmarks) + 1}'
        description = input('Tour description: ').strip() or f'This is {name}, one of the registered tour stops.'
        new_id = self.next_manual_landmark_id()

        self.landmarks[new_id] = {
            'id': new_id,
            'name': name,
            'description': description,
            'x': self.current_pose['x'],
            'y': self.current_pose['y'],
            'yaw': self.current_pose['yaw'],
            'source': 'manual',
            'times_seen': 1,
        }

        self.announce(
            f'Registered landmark {new_id}: {name}\n'
            f'x={self.current_pose["x"]:.2f}, y={self.current_pose["y"]:.2f}, '
            f'yaw={self.current_pose["yaw"]:.2f}'
        )

    def scan_for_aruco_landmarks(self, seconds: int = 15):
        self.announce(
            f'Scanning for ArUco landmarks for {seconds} seconds.\n'
            'Point the OAK-D camera toward printed DICT_4X4_50 markers.'
        )
        start_time = time.time()
        before_count = len(self.landmarks)
        while rclpy.ok() and time.time() - start_time < seconds:
            rclpy.spin_once(self, timeout_sec=0.1)
        after_count = len(self.landmarks)
        self.announce(
            f'Scan complete. New landmarks detected: {after_count - before_count}. '
            f'Total landmarks: {after_count}.'
        )

    def print_landmarks(self):
        if not self.landmarks:
            self.announce('No landmarks registered yet.')
            return
        self.announce('Registered Landmark Map')
        for landmark_id in sorted(self.landmarks.keys()):
            lm = self.landmarks[landmark_id]
            print(
                f'{landmark_id}: {lm["name"]} [{lm.get("source", "unknown")}] '
                f'x={lm["x"]:.2f}, y={lm["y"]:.2f}, yaw={lm["yaw"]:.2f}, '
                f'seen={lm.get("times_seen", 1)}'
            )
            print(f'   {lm["description"]}\n')

    def save_landmarks(self):
        os.makedirs(os.path.dirname(self.landmark_file), exist_ok=True)
        with open(self.landmark_file, 'w', encoding='utf-8') as f:
            json.dump({'landmarks': list(self.landmarks.values())}, f, indent=2)
        self.announce(f'Saved landmarks to {self.landmark_file}')

    def load_landmarks(self):
        if not os.path.exists(self.landmark_file):
            self.announce(f'No saved landmark file found at {self.landmark_file}')
            return
        with open(self.landmark_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        self.landmarks = {int(lm['id']): lm for lm in data.get('landmarks', [])}
        self.announce(f'Loaded {len(self.landmarks)} landmarks from {self.landmark_file}')

    def send_goal(self, x: float, y: float, yaw: float) -> bool:
        self.get_logger().info('Waiting for /navigate_to_position action server...')
        if not self.navigator_client.wait_for_server(timeout_sec=5.0):
            self.get_logger().error('Action server /navigate_to_position not available.')
            return False

        goal_msg = NavigateToPosition.Goal()
        goal_msg.achieve_goal_heading = False
        goal_msg.max_translation_speed = 0.15
        goal_msg.max_rotation_speed = 0.5

        goal_msg.goal_pose.header.frame_id = 'odom'
        goal_msg.goal_pose.pose.position.x = float(x)
        goal_msg.goal_pose.pose.position.y = float(y)
        goal_msg.goal_pose.pose.position.z = 0.0

        qz, qw = self.yaw_to_quaternion(yaw)
        goal_msg.goal_pose.pose.orientation.x = 0.0
        goal_msg.goal_pose.pose.orientation.y = 0.0
        goal_msg.goal_pose.pose.orientation.z = qz
        goal_msg.goal_pose.pose.orientation.w = qw

        self.get_logger().info(f'Sending goal: x={x:.2f}, y={y:.2f}, yaw={yaw:.2f}')

        send_goal_future = self.navigator_client.send_goal_async(goal_msg)
        rclpy.spin_until_future_complete(self, send_goal_future)
        goal_handle = send_goal_future.result()

        if goal_handle is None or not goal_handle.accepted:
            self.get_logger().error('Goal request failed or was rejected.')
            return False

        self.get_logger().info('Goal accepted. Waiting for result...')
        result_future = goal_handle.get_result_async()
        rclpy.spin_until_future_complete(self, result_future)
        result = result_future.result()

        if result is None:
            self.get_logger().error('No result received.')
            return False

        self.get_logger().info(f'Goal finished with status: {result.status}')
        return result.status == 4

    def visit_landmark(self, landmark_id: int) -> bool:
        if landmark_id not in self.landmarks:
            self.announce(f'Landmark {landmark_id} is not registered.')
            return False

        lm = self.landmarks[landmark_id]
        self.announce(f'Navigating to {lm["name"]}...')
        success = self.send_goal(lm['x'], lm['y'], lm['yaw'])

        if success:
            self.announce(f'Arrived at {lm["name"]}.\n\n{lm["description"]}')
            time.sleep(1.5)
            return True

        self.announce(f'Failed to reach {lm["name"]}. Stopping this tour step for safety.')
        return False

    def run_registered_tour(self):
        if not self.landmarks:
            self.announce('No registered landmarks. Scan or manually register landmarks first.')
            return
        self.announce('Welcome to the TurtleBot 4 landmark tour. The robot will visit each registered landmark in numerical order.')
        for landmark_id in sorted(self.landmarks.keys()):
            if not self.visit_landmark(landmark_id):
                break
        self.announce('Registered landmark tour complete.')

    def run_fixed_demo_tour(self):
        self.announce(
            'Welcome to the TurtleBot 4 fixed demonstration tour.\n'
            'This fallback mode uses safe odometry-frame goals so the robot can still demonstrate tour-guide behavior.'
        )
        for stop_id in sorted(self.fixed_demo_stops.keys()):
            stop = self.fixed_demo_stops[stop_id]
            self.announce(f'Navigating to {stop["name"]}...')
            success = self.send_goal(stop['x'], stop['y'], stop['yaw'])
            if success:
                self.announce(f'Arrived at {stop["name"]}.\n\n{stop["description"]}')
                time.sleep(1.5)
            else:
                self.announce(f'Failed to reach {stop["name"]}. Stopping fixed demo tour for safety.')
                break
        self.announce('Fixed demonstration tour complete.')

    def menu_loop(self):
        while rclpy.ok():
            rclpy.spin_once(self, timeout_sec=0.1)
            print('\nTurtleBot 4 Tour Guide Menu')
            print('1: Scan for ArUco landmarks')
            print('2: Manually register current robot pose as landmark')
            print('3: Print registered landmark map')
            print('4: Visit one registered landmark')
            print('5: Run full registered-landmark tour')
            print('6: Run fixed fallback demo tour')
            print('7: Save landmarks')
            print('8: Load landmarks')
            print('9: Exit')
            choice = input('Enter choice: ').strip()

            if choice == '1':
                seconds_text = input('Scan time in seconds [default 15]: ').strip()
                try:
                    seconds = int(seconds_text) if seconds_text else 15
                except ValueError:
                    seconds = 15
                self.scan_for_aruco_landmarks(seconds)
            elif choice == '2':
                self.manual_register_landmark()
            elif choice == '3':
                self.print_landmarks()
            elif choice == '4':
                landmark_text = input('Enter landmark ID: ').strip()
                try:
                    self.visit_landmark(int(landmark_text))
                except ValueError:
                    print('Invalid landmark ID.')
            elif choice == '5':
                self.run_registered_tour()
            elif choice == '6':
                self.run_fixed_demo_tour()
            elif choice == '7':
                self.save_landmarks()
            elif choice == '8':
                self.load_landmarks()
            elif choice == '9':
                print('Exiting.')
                break
            else:
                print('Invalid choice.')


def main(args=None):
    rclpy.init(args=args)
    node = TourGuideNode()
    try:
        node.menu_loop()
    except KeyboardInterrupt:
        print('\nInterrupted.')
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
