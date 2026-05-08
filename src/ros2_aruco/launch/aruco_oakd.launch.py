from launch import LaunchDescription
from launch_ros.actions import Node


def generate_launch_description():
    return LaunchDescription([
        Node(
            package='ros2_aruco',
            executable='aruco_node',
            name='aruco_node',
            output='screen',
            parameters=[{
                'image_topic': '/oakd/rgb/preview/image_raw',
                'camera_info_topic': '/oakd/rgb/preview/camera_info',
                'marker_size': 0.10,
                'aruco_dictionary_id': 'DICT_4X4_50',
                'publish_debug_image': False,
            }],
        )
    ])
