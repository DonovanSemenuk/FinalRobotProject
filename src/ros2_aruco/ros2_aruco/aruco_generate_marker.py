#!/usr/bin/env python3

import cv2
import rclpy
from rclpy.node import Node


class MarkerGenerator(Node):
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
        super().__init__("aruco_generate_marker")
        self.declare_parameter("marker_id", 0)
        self.declare_parameter("side_pixels", 800)
        self.declare_parameter("aruco_dictionary_id", "DICT_4X4_50")
        self.declare_parameter("output_path", "marker.png")

        marker_id = int(self.get_parameter("marker_id").value)
        side_pixels = int(self.get_parameter("side_pixels").value)
        dictionary_name = str(self.get_parameter("aruco_dictionary_id").value)
        output_path = str(self.get_parameter("output_path").value)

        if not hasattr(cv2, "aruco"):
            raise RuntimeError("cv2.aruco is unavailable. Install OpenCV contrib.")

        dict_id = self.DICTIONARIES.get(dictionary_name)
        if dict_id is None:
            raise ValueError(f"Unknown dictionary {dictionary_name}")

        if hasattr(cv2.aruco, "getPredefinedDictionary"):
            dictionary = cv2.aruco.getPredefinedDictionary(dict_id)
        else:
            dictionary = cv2.aruco.Dictionary_get(dict_id)

        if hasattr(cv2.aruco, "generateImageMarker"):
            marker_image = cv2.aruco.generateImageMarker(dictionary, marker_id, side_pixels)
        else:
            marker_image = cv2.aruco.drawMarker(dictionary, marker_id, side_pixels)

        cv2.imwrite(output_path, marker_image)
        self.get_logger().info(f"Saved marker {marker_id} to {output_path}")


def main(args=None):
    rclpy.init(args=args)
    node = MarkerGenerator()
    node.destroy_node()
    rclpy.shutdown()


if __name__ == "__main__":
    main()
