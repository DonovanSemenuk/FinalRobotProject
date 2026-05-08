# FinalRobotProject — TurtleBot 4 ArUco Tour Guide

This repository contains a ROS 2 TurtleBot 4 tour-guide project designed for the OU robotics lab environment. It includes:

- `tour_guide`: the main tour-guide node.
- `ros2_aruco`: a lightweight ArUco detector node written for this project.
- `ros2_aruco_interfaces`: custom message definitions for detected ArUco markers.

The system supports three demo paths:

1. **ArUco landmark tour**: detect ArUco markers, record the robot viewing pose, and tour detected landmarks.
2. **Manual landmark tour**: manually register the robot's current odometry pose as a landmark when ArUco detection is unavailable.
3. **Fixed fallback tour**: run a conservative four-stop tour using safe odometry-frame goals.

The real OU TurtleBot 4 tested by the team exposed `/navigate_to_position` using `irobot_create_msgs/action/NavigateToPosition`, so the tour node uses that action server instead of assuming Nav2 `/navigate_to_pose` is available.

## Build

```bash
cd ~/ros2_ws/FinalRobotProject
source /opt/ros/jazzy/setup.bash
colcon build --symlink-install
source install/setup.bash
```

## Robot network setup

Run the lab setup script:

```bash
robot-setup.sh
```

For the robot tested, the printed commands were similar to:

```bash
unset ROS_LOCALHOST_ONLY
export ROS_DOMAIN_ID=5
export ROS_DISCOVERY_SERVER=";;;;;10.194.16.38:11811;"
export ROS_SUPER_CLIENT=True
ros2 daemon stop; ros2 daemon start
```

Verify topics:

```bash
ros2 topic list | grep -E "/odom|/scan|/tf|oak|camera|image"
ros2 action list -t | grep navigate
```

Expected important topics/actions:

```text
/odom
/scan
/tf
/tf_static
/oakd/rgb/preview/image_raw
/oakd/rgb/preview/camera_info
/navigate_to_position [irobot_create_msgs/action/NavigateToPosition]
```

## Run ArUco detection

```bash
ros2 run ros2_aruco aruco_node --ros-args \
  -p image_topic:=/oakd/rgb/preview/image_raw \
  -p camera_info_topic:=/oakd/rgb/preview/camera_info \
  -p marker_size:=0.10 \
  -p aruco_dictionary_id:=DICT_4X4_50
```

In another terminal:

```bash
ros2 topic list | grep -i aruco
ros2 topic echo /aruco_markers
```

## Run tour guide

```bash
ros2 run tour_guide nav_node
```

Recommended demo order:

- If ArUco works: `1` scan, `3` print map, `5` run registered tour.
- If ArUco does not work: `2` manually register landmarks, `3` print map, `5` run registered tour.
- If time is short: `6` run fixed fallback demo tour.

## Generate markers

```bash
ros2 run ros2_aruco aruco_generate_marker --ros-args -p marker_id:=0 -p output_path:=marker_0.png
```

Repeat for marker IDs 1, 2, and 3.
