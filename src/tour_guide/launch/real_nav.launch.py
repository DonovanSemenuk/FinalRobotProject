from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration
from ament_index_python.packages import get_package_share_directory
import os


def generate_launch_description():
    """Launch TurtleBot4 localization and Nav2 on the saved loggerhead classroom map.

    The official TurtleBot4 navigation entry point is nav_bringup.launch.py with
    localization enabled and SLAM disabled. Using that launch file avoids the
    common lifecycle/race problems caused by manually composing localization and
    Nav2 in a custom launch file.
    """

    turtlebot4_navigation = get_package_share_directory('turtlebot4_navigation')
    nav_bringup_launch = os.path.join(
        turtlebot4_navigation,
        'launch',
        'nav_bringup.launch.py',
    )

    default_map = os.path.expanduser(
        '~/ros2_ws/FinalRobotProject/src/tour_guide/maps/loggerhead_classroom.yaml'
    )

    return LaunchDescription([
        DeclareLaunchArgument(
            'map',
            default_value=default_map,
            description='Full path to loggerhead_classroom.yaml or another saved occupancy-grid map.',
        ),
        DeclareLaunchArgument(
            'namespace',
            default_value='',
            description='Optional TurtleBot namespace. Leave empty for the OU single-robot setup.',
        ),
        DeclareLaunchArgument(
            'use_sim_time',
            default_value='false',
            description='Use false for the physical TurtleBot4.',
        ),
        IncludeLaunchDescription(
            PythonLaunchDescriptionSource(nav_bringup_launch),
            launch_arguments={
                'slam': 'off',
                'localization': 'true',
                'map': LaunchConfiguration('map'),
                'namespace': LaunchConfiguration('namespace'),
                'use_sim_time': LaunchConfiguration('use_sim_time'),
            }.items(),
        ),
    ])
