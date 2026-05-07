from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription, TimerAction
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration
from ament_index_python.packages import get_package_share_directory
import os


def generate_launch_description():
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

    default_map = os.path.expanduser(
        '~/ros2_ws/FinalRobotProject/src/tour_guide/maps/loggerhead_classroom.yaml'
    )

    return LaunchDescription([
        DeclareLaunchArgument(
            'map',
            default_value=default_map,
            description='Full path to loggerhead_classroom.yaml.',
        ),
        DeclareLaunchArgument(
            'namespace',
            default_value='',
            description='Optional TurtleBot namespace. Leave empty for the single-robot classroom setup.',
        ),
        DeclareLaunchArgument(
            'use_sim_time',
            default_value='false',
            description='Use false for the physical TurtleBot4.',
        ),
        DeclareLaunchArgument(
            'nav2_delay',
            default_value='5.0',
            description='Seconds to wait after localization starts before launching Nav2.',
        ),
        IncludeLaunchDescription(
            PythonLaunchDescriptionSource(localization_launch),
            launch_arguments={
                'map': LaunchConfiguration('map'),
                'namespace': LaunchConfiguration('namespace'),
                'use_sim_time': LaunchConfiguration('use_sim_time'),
            }.items(),
        ),
        TimerAction(
            period=LaunchConfiguration('nav2_delay'),
            actions=[
                IncludeLaunchDescription(
                    PythonLaunchDescriptionSource(nav2_launch),
                    launch_arguments={
                        'namespace': LaunchConfiguration('namespace'),
                        'use_sim_time': LaunchConfiguration('use_sim_time'),
                    }.items(),
                ),
            ],
        ),
    ])
