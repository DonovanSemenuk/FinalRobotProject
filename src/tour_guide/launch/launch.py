from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration
from ament_index_python.packages import get_package_share_directory
import os

def generate_launch_description():
    pkg_share = get_package_share_directory('tour_guide')
    nav2_share = get_package_share_directory('nav2_bringup')

    default_world = os.path.join(pkg_share, 'worlds', 'tour_world.sdf')
    default_map   = os.path.join(pkg_share, 'maps', 'sim.yaml')
    tb4_sim_launch = os.path.join(nav2_share, 'launch', 'tb4_simulation_launch.py')

    return LaunchDescription([
        DeclareLaunchArgument('world',   default_value=default_world),
        DeclareLaunchArgument('map',     default_value=default_map),
        DeclareLaunchArgument('slam',    default_value='False'),
        DeclareLaunchArgument('headless',default_value='False'),
        IncludeLaunchDescription(
            PythonLaunchDescriptionSource(tb4_sim_launch),
            launch_arguments={
                'world':   LaunchConfiguration('world'),
                'map':     LaunchConfiguration('map'),
                'slam':    LaunchConfiguration('slam'),
                'headless':LaunchConfiguration('headless'),
                'x_pose':  '1.0',
                'y_pose':  '3.0',
                'z_pose':  '0.0',
                'yaw':     '0.0',
            }.items()
        ),
    ])
