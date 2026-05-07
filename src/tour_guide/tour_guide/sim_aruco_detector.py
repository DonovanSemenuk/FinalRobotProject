from __future__ import annotations

import math
from typing import Optional

import cv2
import numpy as np
import rclpy
from geometry_msgs.msg import Pose
from rclpy.node import Node
from ros2_aruco_interfaces.msg import ArucoMarkers
from sensor_msgs.msg import CameraInfo, Image


class SimArucoDetector(Node):
    def __init__(self):
        super().__init__('sim_aruco_detector')
        self.declare_parameter('image_topic', '/rgbd_camera/image')
        self.declare_parameter('camera_info_topic', '/rgbd_camera/camera_info')
        self.declare_parameter('marker_size', 0.10)
        self.declare_parameter('aruco_dictionary_id', 'DICT_4X4_50')
        self.declare_parameter('output_topic', '/aruco_markers')

        self.image_topic = str(self.get_parameter('image_topic').value)
        self.camera_info_topic = str(self.get_parameter('camera_info_topic').value)
        self.marker_size = float(self.get_parameter('marker_size').value)
        self.output_topic = str(self.get_parameter('output_topic').value)
        dictionary_name = str(self.get_parameter('aruco_dictionary_id').value)

        dictionary_id = getattr(cv2.aruco, dictionary_name, cv2.aruco.DICT_4X4_50)
        self.dictionary = cv2.aruco.getPredefinedDictionary(dictionary_id)
        self.parameters = cv2.aruco.DetectorParameters()
        self.detector = cv2.aruco.ArucoDetector(self.dictionary, self.parameters)

        self.latest_camera_info: Optional[CameraInfo] = None
        self.publisher = self.create_publisher(ArucoMarkers, self.output_topic, 10)
        self.create_subscription(CameraInfo, self.camera_info_topic, self.camera_info_callback, 10)
        self.create_subscription(Image, self.image_topic, self.image_callback, 10)

        self.get_logger().info(f'Sim ArUco detector listening to image: {self.image_topic}')
        self.get_logger().info(f'Sim ArUco detector listening to camera info: {self.camera_info_topic}')
        self.get_logger().info(f'Publishing detections to: {self.output_topic}')
        self.get_logger().info(f'Dictionary: {dictionary_name}, marker_size: {self.marker_size} m')

    def camera_info_callback(self, msg: CameraInfo) -> None:
        self.latest_camera_info = msg

    @staticmethod
    def image_to_array(msg: Image) -> Optional[np.ndarray]:
        if msg.encoding not in {'rgb8', 'bgr8', 'rgba8', 'bgra8', 'mono8'}:
            return None

        channels = {
            'mono8': 1,
            'rgb8': 3,
            'bgr8': 3,
            'rgba8': 4,
            'bgra8': 4,
        }[msg.encoding]

        array = np.frombuffer(msg.data, dtype=np.uint8)
        expected = msg.height * msg.step
        if array.size < expected:
            return None

        array = array[:expected].reshape((msg.height, msg.step))
        image = array[:, : msg.width * channels].reshape((msg.height, msg.width, channels))
        if msg.encoding == 'mono8':
            return image.reshape((msg.height, msg.width))
        if msg.encoding == 'rgb8':
            return cv2.cvtColor(image, cv2.COLOR_RGB2GRAY)
        if msg.encoding == 'bgr8':
            return cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        if msg.encoding == 'rgba8':
            return cv2.cvtColor(image, cv2.COLOR_RGBA2GRAY)
        if msg.encoding == 'bgra8':
            return cv2.cvtColor(image, cv2.COLOR_BGRA2GRAY)
        return None

    @staticmethod
    def rvec_to_quaternion(rvec: np.ndarray):
        rotation_matrix, _ = cv2.Rodrigues(rvec)
        trace = float(np.trace(rotation_matrix))
        if trace > 0.0:
            s = math.sqrt(trace + 1.0) * 2.0
            qw = 0.25 * s
            qx = (rotation_matrix[2, 1] - rotation_matrix[1, 2]) / s
            qy = (rotation_matrix[0, 2] - rotation_matrix[2, 0]) / s
            qz = (rotation_matrix[1, 0] - rotation_matrix[0, 1]) / s
        else:
            qw, qx, qy, qz = 1.0, 0.0, 0.0, 0.0
        return qx, qy, qz, qw

    def image_callback(self, msg: Image) -> None:
        if self.latest_camera_info is None:
            self.get_logger().warn('Waiting for camera info', throttle_duration_sec=2.0)
            return

        gray = self.image_to_array(msg)
        if gray is None:
            self.get_logger().warn(f'Unsupported image encoding: {msg.encoding}', throttle_duration_sec=2.0)
            return

        corners, ids, _ = self.detector.detectMarkers(gray)
        if ids is None or len(ids) == 0:
            return

        camera_matrix = np.array(self.latest_camera_info.k, dtype=np.float64).reshape((3, 3))
        dist_coeffs = np.array(self.latest_camera_info.d, dtype=np.float64)
        rvecs, tvecs, _ = cv2.aruco.estimatePoseSingleMarkers(
            corners,
            self.marker_size,
            camera_matrix,
            dist_coeffs,
        )

        output = ArucoMarkers()
        output.header = msg.header
        output.marker_ids = [int(marker_id[0]) for marker_id in ids]

        poses = []
        for rvec, tvec in zip(rvecs, tvecs):
            pose = Pose()
            pose.position.x = float(tvec[0][0])
            pose.position.y = float(tvec[0][1])
            pose.position.z = float(tvec[0][2])
            qx, qy, qz, qw = self.rvec_to_quaternion(rvec[0])
            pose.orientation.x = float(qx)
            pose.orientation.y = float(qy)
            pose.orientation.z = float(qz)
            pose.orientation.w = float(qw)
            poses.append(pose)

        output.poses = poses
        self.publisher.publish(output)
        self.get_logger().info(f'Detected marker IDs: {output.marker_ids}', throttle_duration_sec=1.0)


def main(args=None):
    rclpy.init(args=args)
    node = SimArucoDetector()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()


if __name__ == '__main__':
    main()
