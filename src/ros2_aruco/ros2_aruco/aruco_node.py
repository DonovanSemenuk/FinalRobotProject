#!/usr/bin/env python3

import math
from typing import Optional

import cv2
import numpy as np
import rclpy
from cv_bridge import CvBridge
from geometry_msgs.msg import Pose
from rclpy.node import Node
from sensor_msgs.msg import CameraInfo, Image

from ros2_aruco_interfaces.msg import ArucoMarkers


class ArucoNode(Node):
    """
    Lightweight ArUco detector for TurtleBot 4 OAK-D RGB preview images.

    This node intentionally avoids tf_transformations. The tour guide only needs
    marker IDs to create landmark viewing poses from /odom. Pose output is best
    effort and is included for documentation/future work.
    """

    DICTIONARIES = {
        "DICT_4X4_50": cv2.aruco.DICT_4X4_50,
        "DICT_4X4_100": cv2.aruco.DICT_4X4_100,
        "DICT_5X5_50": cv2.aruco.DICT_5X5_50,
        "DICT_5X5_100": cv2.aruco.DICT_5X5_100,
        "DICT_6X6_50": cv2.aruco.DICT_6X6_50,
        "DICT_6X6_100": cv2.aruco.DICT_6X6_100,
        "DICT_7X7_50": cv2.aruco.DICT_7X7_50,
        "DICT_ARUCO_ORIGINAL": cv2.aruco.DICT_ARUCO_ORIGINAL,
    }

    def __init__(self):
        super().__init__("aruco_node")

        self.declare_parameter("image_topic", "/oakd/rgb/preview/image_raw")
        self.declare_parameter("camera_info_topic", "/oakd/rgb/preview/camera_info")
        self.declare_parameter("marker_size", 0.10)
        self.declare_parameter("aruco_dictionary_id", "DICT_4X4_50")
        self.declare_parameter("publish_debug_image", False)

        self.image_topic = self.get_parameter("image_topic").value
        self.camera_info_topic = self.get_parameter("camera_info_topic").value
        self.marker_size = float(self.get_parameter("marker_size").value)
        self.dictionary_name = str(self.get_parameter("aruco_dictionary_id").value)
        self.publish_debug_image = bool(self.get_parameter("publish_debug_image").value)

        if not hasattr(cv2, "aruco"):
            raise RuntimeError(
                "OpenCV was built without the aruco module. Install opencv-contrib-python "
                "or use a ROS image with cv2.aruco available."
            )

        dict_id = self.DICTIONARIES.get(self.dictionary_name)
        if dict_id is None:
            valid = ", ".join(sorted(self.DICTIONARIES.keys()))
            raise ValueError(f"Unknown dictionary {self.dictionary_name}. Valid: {valid}")

        self.dictionary = self._get_dictionary(dict_id)
        self.parameters = self._get_detector_parameters()
        self.detector = self._get_detector()

        self.bridge = CvBridge()
        self.camera_matrix: Optional[np.ndarray] = None
        self.distortion: Optional[np.ndarray] = None
        self.latest_camera_info: Optional[CameraInfo] = None

        self.marker_pub = self.create_publisher(ArucoMarkers, "/aruco_markers", 10)
        if self.publish_debug_image:
            self.debug_pub = self.create_publisher(Image, "/aruco_debug_image", 10)
        else:
            self.debug_pub = None

        self.camera_info_sub = self.create_subscription(
            CameraInfo,
            self.camera_info_topic,
            self.camera_info_callback,
            10,
        )
        self.image_sub = self.create_subscription(
            Image,
            self.image_topic,
            self.image_callback,
            10,
        )

        self.get_logger().info(f"ArUco node listening to image: {self.image_topic}")
        self.get_logger().info(f"ArUco node listening to camera info: {self.camera_info_topic}")
        self.get_logger().info(f"Dictionary: {self.dictionary_name}, marker_size: {self.marker_size} m")

    def _get_dictionary(self, dict_id):
        if hasattr(cv2.aruco, "getPredefinedDictionary"):
            return cv2.aruco.getPredefinedDictionary(dict_id)
        return cv2.aruco.Dictionary_get(dict_id)

    def _get_detector_parameters(self):
        if hasattr(cv2.aruco, "DetectorParameters"):
            return cv2.aruco.DetectorParameters()
        return cv2.aruco.DetectorParameters_create()

    def _get_detector(self):
        if hasattr(cv2.aruco, "ArucoDetector"):
            return cv2.aruco.ArucoDetector(self.dictionary, self.parameters)
        return None

    def camera_info_callback(self, msg: CameraInfo):
        self.latest_camera_info = msg
        self.camera_matrix = np.array(msg.k, dtype=np.float64).reshape((3, 3))
        self.distortion = np.array(msg.d, dtype=np.float64)

    def image_callback(self, msg: Image):
        try:
            frame = self.bridge.imgmsg_to_cv2(msg, desired_encoding="bgr8")
        except Exception as exc:
            self.get_logger().error(f"cv_bridge conversion failed: {exc}")
            return

        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

        if self.detector is not None:
            corners, ids, _ = self.detector.detectMarkers(gray)
        else:
            corners, ids, _ = cv2.aruco.detectMarkers(
                gray,
                self.dictionary,
                parameters=self.parameters,
            )

        marker_msg = ArucoMarkers()
        marker_msg.header = msg.header

        if ids is not None and len(ids) > 0:
            flat_ids = ids.flatten().astype(int).tolist()
            marker_msg.marker_ids = flat_ids

            poses = self.estimate_poses(corners, len(flat_ids))
            marker_msg.poses = poses

            self.get_logger().info(f"Detected ArUco marker IDs: {flat_ids}")

            if self.debug_pub is not None:
                cv2.aruco.drawDetectedMarkers(frame, corners, ids)
                debug_msg = self.bridge.cv2_to_imgmsg(frame, encoding="bgr8")
                debug_msg.header = msg.header
                self.debug_pub.publish(debug_msg)

        self.marker_pub.publish(marker_msg)

    def estimate_poses(self, corners, count):
        poses = []

        if self.camera_matrix is None or self.distortion is None:
            return [Pose() for _ in range(count)]

        try:
            rvecs, tvecs, _ = cv2.aruco.estimatePoseSingleMarkers(
                corners,
                self.marker_size,
                self.camera_matrix,
                self.distortion,
            )
        except Exception as exc:
            self.get_logger().warn(f"Pose estimation failed; publishing IDs only. Error: {exc}")
            return [Pose() for _ in range(count)]

        for i in range(count):
            pose = Pose()
            tvec = tvecs[i][0]
            rvec = rvecs[i][0]

            pose.position.x = float(tvec[0])
            pose.position.y = float(tvec[1])
            pose.position.z = float(tvec[2])

            qx, qy, qz, qw = self.rotation_vector_to_quaternion(rvec)
            pose.orientation.x = qx
            pose.orientation.y = qy
            pose.orientation.z = qz
            pose.orientation.w = qw
            poses.append(pose)

        return poses

    def rotation_vector_to_quaternion(self, rvec):
        rotation_matrix, _ = cv2.Rodrigues(np.array(rvec, dtype=np.float64))
        trace = np.trace(rotation_matrix)

        if trace > 0.0:
            s = math.sqrt(trace + 1.0) * 2.0
            qw = 0.25 * s
            qx = (rotation_matrix[2, 1] - rotation_matrix[1, 2]) / s
            qy = (rotation_matrix[0, 2] - rotation_matrix[2, 0]) / s
            qz = (rotation_matrix[1, 0] - rotation_matrix[0, 1]) / s
        else:
            if rotation_matrix[0, 0] > rotation_matrix[1, 1] and rotation_matrix[0, 0] > rotation_matrix[2, 2]:
                s = math.sqrt(1.0 + rotation_matrix[0, 0] - rotation_matrix[1, 1] - rotation_matrix[2, 2]) * 2.0
                qw = (rotation_matrix[2, 1] - rotation_matrix[1, 2]) / s
                qx = 0.25 * s
                qy = (rotation_matrix[0, 1] + rotation_matrix[1, 0]) / s
                qz = (rotation_matrix[0, 2] + rotation_matrix[2, 0]) / s
            elif rotation_matrix[1, 1] > rotation_matrix[2, 2]:
                s = math.sqrt(1.0 + rotation_matrix[1, 1] - rotation_matrix[0, 0] - rotation_matrix[2, 2]) * 2.0
                qw = (rotation_matrix[0, 2] - rotation_matrix[2, 0]) / s
                qx = (rotation_matrix[0, 1] + rotation_matrix[1, 0]) / s
                qy = 0.25 * s
                qz = (rotation_matrix[1, 2] + rotation_matrix[2, 1]) / s
            else:
                s = math.sqrt(1.0 + rotation_matrix[2, 2] - rotation_matrix[0, 0] - rotation_matrix[1, 1]) * 2.0
                qw = (rotation_matrix[1, 0] - rotation_matrix[0, 1]) / s
                qx = (rotation_matrix[0, 2] + rotation_matrix[2, 0]) / s
                qy = (rotation_matrix[1, 2] + rotation_matrix[2, 1]) / s
                qz = 0.25 * s

        return float(qx), float(qy), float(qz), float(qw)


def main(args=None):
    rclpy.init(args=args)
    node = ArucoNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == "__main__":
    main()
