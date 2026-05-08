from launch import LaunchDescription
from launch_ros.actions import Node


def generate_launch_description():
    return LaunchDescription([
        Node(
            package='tour_guide',
            executable='nav_node',
            name='tour_guide_node',
            output='screen',
        )
    ])
