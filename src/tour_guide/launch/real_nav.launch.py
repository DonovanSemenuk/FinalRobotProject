from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration
from ament_index_python.packages import get_package_share_directory
import os


def generate_launch_description():
    """Launch localization and Nav2 for a physical TurtleBot 4 using a saved map."""

    turtlebot4_navigation = get_package_share_directory('turtlebot4_navigation')

    localization_launch = os.path.join(
        turtlebot4_navigation,
        'launch',
        'localization.launch.py',
    )
    nav2_launch = os.path.join(
        turtlebot4_navigation,
        'launch',
        'nav2.launch.py',
    )

    return LaunchDescription([
        DeclareLaunchArgument(
            'map',
            default_value=os.path.expanduser(
                '~/ros2_ws/FinalRobotProject/src/tour_guide/maps/classroom_map.yaml'
            ),
            description='Full path to the saved occupancy-grid YAML map.',
        ),
        DeclareLaunchArgument(
            'namespace',
            default_value='',
            description='Optional TurtleBot namespace. Leave empty for the OU single-robot setup.',
        ),
        IncludeLaunchDescription(
            PythonLaunchDescriptionSource(localization_launch),
            launch_arguments={
                'map': LaunchConfiguration('map'),
                'namespace': LaunchConfiguration('namespace'),
            }.items(),
        ),
        IncludeLaunchDescription(
            PythonLaunchDescriptionSource(nav2_launch),
            launch_arguments={
                'namespace': LaunchConfiguration('namespace'),
            }.items(),
        ),
    ])
