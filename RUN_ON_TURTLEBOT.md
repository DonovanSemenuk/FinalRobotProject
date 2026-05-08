# Running on an OU TurtleBot 4

## 1. Build

```bash
cd ~/ros2_ws/FinalRobotProject
source /opt/ros/jazzy/setup.bash
colcon build --symlink-install
source install/setup.bash
```

## 2. Connect desktop to robot

```bash
robot-setup.sh
```

Apply the printed commands. For `terrapin`, this was:

```bash
unset ROS_LOCALHOST_ONLY
export ROS_DOMAIN_ID=5
export ROS_DISCOVERY_SERVER=";;;;;10.194.16.38:11811;"
export ROS_SUPER_CLIENT=True
ros2 daemon stop; ros2 daemon start
```

## 3. Verify robot

```bash
ros2 topic list | grep -E "/odom|/scan|/tf"
ros2 topic list | grep -E "image|camera|color|oak|rgb|depth"
ros2 action list -t | grep navigate
```

## 4. ArUco detector

```bash
ros2 launch ros2_aruco aruco_oakd.launch.py
```

or:

```bash
ros2 run ros2_aruco aruco_node --ros-args \
  -p image_topic:=/oakd/rgb/preview/image_raw \
  -p camera_info_topic:=/oakd/rgb/preview/camera_info \
  -p marker_size:=0.10 \
  -p aruco_dictionary_id:=DICT_4X4_50
```

## 5. Tour guide

```bash
ros2 run tour_guide nav_node
```

Menu use:

- `1`: scan for ArUco landmarks
- `2`: manually register current pose
- `3`: print landmark map
- `4`: visit one landmark
- `5`: run registered tour
- `6`: run fixed fallback demo tour
- `7`: save landmarks
- `8`: load landmarks
- `9`: exit

## Demo safety

Start with the fixed fallback tour or a single registered landmark. Keep goals small and stop with `Ctrl+C` if localization or movement is wrong.
