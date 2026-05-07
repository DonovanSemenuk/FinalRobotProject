# FinalRobotProject

TurtleBot4 autonomous tour guide for a relocatable-landmark environment.

## Mission target

The project mission is a robot tour guide for an OU TurtleBot 4. The grading sheet rewards software that is useful for the mission, works on the real TurtleBot/Gazebo stack, and adds original robot-performance behavior beyond simply launching existing packages. The assignment also requires ROS 2 and Gazebo Harmonic compatibility, and it specifically expects a deliberative or hybrid architecture.

This repo should therefore be built in this order:

1. Make a clean real-world classroom map.
2. Localize the real robot on that map.
3. Send the robot to known tour stops.
4. Add landmark discovery or route optimization only after the basic tour works.

Do not lead with custom A*. Nav2 already provides collision-aware path planning. A custom A* route-ordering layer can be added later, but it is not the fastest path to a working demo.

## Core behavior

The robot should:

1. Run in the TurtleBot4/Nav2 environment.
2. Build or load a classroom occupancy-grid map.
3. Detect or define tour landmarks.
4. Save landmarks as map-frame tour stops.
5. Let the operator select a landmark order.
6. Navigate to each selected landmark and pause at each stop.

## Build

From the workspace root:

```bash
cd ~/ros2_ws/FinalRobotProject
source /opt/ros/jazzy/setup.bash
rosdep install --from-paths src -y --ignore-src
colcon build --symlink-install
source install/setup.bash
```

Every new terminal should be sourced before running ROS commands:

```bash
cd ~/ros2_ws/FinalRobotProject
source /opt/ros/jazzy/setup.bash
source install/setup.bash
```

## Real robot milestone 1: connect to loggerhead

On each desktop terminal that talks to the robot:

```bash
robot-setup.sh
```

Enter:

```text
loggerhead
```

Then run the environment commands printed by the script. Verify the desktop can see the robot:

```bash
ros2 topic list | grep -E '/scan|/odom|/tf|/cmd_vel'
```

Do not continue unless `/scan`, `/odom`, and `/tf` are visible from the desktop.

## Real robot milestone 2: map the classroom with manual control

See `LOGGERHEAD_MAP_AND_TOUR.md` for the full runbook. Minimal command sequence:

```bash
# robot SSH terminal
ssh student@loggerhead.cs.nor.ou.edu
ros2 service call /start_motor std_srvs/srv/Empty "{}"
```

```bash
# desktop SLAM terminal
source /opt/ros/jazzy/setup.bash
ros2 launch turtlebot4_navigation slam.launch.py
```

```bash
# desktop RViz terminal
source /opt/ros/jazzy/setup.bash
ros2 launch turtlebot4_viz view_robot.launch.py
```

```bash
# desktop teleop terminal
source /opt/ros/jazzy/setup.bash
ros2 run teleop_twist_keyboard teleop_twist_keyboard --ros-args -p stamped:=true
```

Drive slowly. Save the map from the repository root:

```bash
cd ~/ros2_ws/FinalRobotProject
mkdir -p src/tour_guide/maps
ros2 run nav2_map_server map_saver_cli -f src/tour_guide/maps/classroom_map
```

Expected output:

```text
src/tour_guide/maps/classroom_map.yaml
src/tour_guide/maps/classroom_map.pgm
```

## Real robot milestone 3: localize and launch Nav2 on the saved map

After saving a good map, stop SLAM. Then launch localization/Nav2:

```bash
cd ~/ros2_ws/FinalRobotProject
source /opt/ros/jazzy/setup.bash
source install/setup.bash
ros2 launch tour_guide real_nav.launch.py map:=$HOME/ros2_ws/FinalRobotProject/src/tour_guide/maps/classroom_map.yaml
```

Open RViz:

```bash
ros2 launch turtlebot4_viz view_navigation.launch.py
```

Use `2D Pose Estimate` in RViz to align the robot with the saved map. Then use `Nav2 Goal` to verify the robot can drive to one nearby point before trying a full tour.

## Real robot milestone 4: define initial tour stops

The fastest reliable path is to start with manual landmarks. After the map works, create:

```text
landmarks/discovered_locations.yaml
```

Recommended recorder method:

```bash
cd ~/ros2_ws/FinalRobotProject
source /opt/ros/jazzy/setup.bash
source install/setup.bash
ros2 run tour_guide known_stop_recorder --output ~/ros2_ws/FinalRobotProject/landmarks/discovered_locations.yaml
```

In RViz, set Fixed Frame to `map`, choose `Publish Point`, and click open floor locations where the robot should stop. The recorder will append stops to the YAML file.

Manual YAML format:

```yaml
landmarks:
  - name: Start Area
    x: 0.0
    y: 0.0
    yaw: 0.0
    description: Starting point for the tour.
  - name: Landmark 1
    x: 1.0
    y: 0.5
    yaw: 0.0
    description: First classroom stop.
```

Keep stops conservative: place them in open floor, not directly against walls, chairs, tables, or marker boards.

## Real robot milestone 5: run the tour

Interactive mode:

```bash
ros2 run tour_guide nav_node
```

Useful selections:

```text
all       # visit all listed landmarks
nearest   # greedy nearest-neighbor stop order
0,2,1     # custom route by menu index
q         # quit
```

One-shot mode for a cleaner demo:

```bash
ros2 run tour_guide nav_node --once --route nearest
```

To force a specific landmark file:

```bash
ros2 run tour_guide nav_node --landmarks ~/ros2_ws/FinalRobotProject/landmarks/discovered_locations.yaml
```

## Simulation/Nav2 fallback

```bash
ros2 launch tour_guide launch.py
```

Wait until Nav2 is active before running the mapper or tour node.

## ArUco landmark mapping phase

The dynamic landmark mapper expects `ros2_aruco_interfaces/msg/ArucoMarkers`, normally on `/aruco_markers`.

Check output:

```bash
ros2 topic list | grep -i aruco
ros2 topic info /aruco_markers
```

Run mapper while manually driving or rotating the robot:

```bash
ros2 run tour_guide landmark_mapper --topic /aruco_markers
```

Automatic sweep option:

```bash
ros2 run tour_guide landmark_mapper --topic /aruco_markers --sweep
```

The mapper writes:

```text
~/ros2_ws/FinalRobotProject/landmarks/discovered_locations.yaml
```

Useful mapper options:

```bash
--stop-offset 0.65
--min-samples 3
--angular-speed 0.25
--sweep-revolutions 1.0
--output PATH
```

## Demo script

1. Show the saved classroom map in RViz.
2. Show the robot localized on the map.
3. Send one RViz Nav2 goal to prove base navigation.
4. Show the landmark YAML file.
5. Run `nav_node`.
6. Select `nearest` or a custom route.
7. Explain that Nav2 handles obstacle-aware path planning while this package handles the higher-level tour-guide behavior: landmark records, route selection, and sequential mission execution.

## Fallback if ArUco detection fails on demo day

Use the static landmark file:

```bash
TOUR_GUIDE_LANDMARKS=~/ros2_ws/FinalRobotProject/landmarks/locations.yaml ros2 run tour_guide nav_node --once --route nearest
```

That still demonstrates operator route selection and Nav2 tour execution. Be direct that the dynamic detection phase is separate or partially integrated.

## What to say if asked about A*

Do not claim this project implements a custom A* planner unless you actually add one. The stronger answer is:

> This project uses Nav2 for path planning and obstacle-aware navigation. The project contribution is the higher-level behavior: creating tour stops from landmarks, letting the operator choose or auto-order a tour, and sending sequential goals to Nav2.

A custom A* grid planner is only worth adding after the real robot can map, localize, and reach manually selected stops.
