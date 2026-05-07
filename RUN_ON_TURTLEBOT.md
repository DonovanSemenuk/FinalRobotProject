# Running the Loggerhead Classroom Tour on an OU TurtleBot 4

This repo is set up for a practical real-robot demo: load the saved `loggerhead_classroom.yaml` map, activate TurtleBot4 Nav2, record or edit safe classroom waypoints, then run the tour node through those waypoints.

The goal is not to rebuild the map. The goal is to make Nav2 active and send reliable map-frame goals.

## 1. Update and build on the robotics6 desktop

```bash
cd ~/ros2_ws/FinalRobotProject
git pull
source /opt/ros/jazzy/setup.bash
rosdep install --from-paths src -y --ignore-src
colcon build --symlink-install
source install/setup.bash
```

Run these source commands in every new desktop terminal before ROS commands:

```bash
cd ~/ros2_ws/FinalRobotProject
source /opt/ros/jazzy/setup.bash
source install/setup.bash
```

## 2. Connect to TurtleBot `testudo`

### Robot terminal

```bash
ssh student@testudo.cs.nor.ou.edu
ros2 topic list
```

Verify `/scan`, `/tf`, and `/odom` exist. If they do not:

```bash
turtlebot4-daemon-restart
ros2 topic list
```

If they are still missing:

```bash
ros2 launch turtlebot4_bringup robot.launch.py
```

Start the LiDAR motor:

```bash
ros2 service call /start_motor std_srvs/srv/Empty "{}"
```

### Desktop terminal

Do this on robotics6, not inside SSH:

```bash
robot-setup.sh
```

Enter:

```text
testudo
```

Run the environment commands printed by `robot-setup.sh`, then:

```bash
ros2 daemon stop
ros2 daemon start
ros2 topic list
```

You must see `/scan`, `/tf`, and `/odom` from the desktop before launching Nav2.

## 3. Launch Nav2 with the loggerhead map

In a sourced robotics6 desktop terminal:

```bash
cd ~/ros2_ws/FinalRobotProject
source /opt/ros/jazzy/setup.bash
source install/setup.bash
ros2 launch tour_guide real_nav.launch.py map:=$PWD/src/tour_guide/maps/loggerhead_classroom.yaml
```

Keep this terminal running.

This launch file uses TurtleBot4 `nav_bringup.launch.py` with SLAM off, localization on, and `use_sim_time:=false`.

## 4. Open RViz and set localization

In a second sourced robotics6 desktop terminal:

```bash
ros2 launch turtlebot4_viz view_robot.launch.py
```

In RViz:

1. Set the fixed frame to `map`.
2. Use `2D Pose Estimate` to place the robot on the loggerhead classroom map.
3. Confirm the laser scan lines up with walls/obstacles.
4. Do not send goals until the scan matches the map. Bad localization means bad navigation.

Check Nav2 state:

```bash
ros2 lifecycle get /controller_server
ros2 lifecycle get /planner_server
ros2 lifecycle get /bt_navigator
ros2 action list | grep navigate
```

Expected lifecycle state is `active`. Expected actions include `/navigate_to_pose`.

## 5. Make waypoint YAML from RViz clicks

Use this when your existing `landmarks/locations.yaml` does not match the real loggerhead map well enough.

In a third sourced robotics6 desktop terminal:

```bash
cd ~/ros2_ws/FinalRobotProject
source /opt/ros/jazzy/setup.bash
source install/setup.bash
rm -f landmarks/discovered_locations.yaml
ros2 run tour_guide known_stop_recorder --output $PWD/landmarks/discovered_locations.yaml
```

In RViz, use `Publish Point` and click safe open-floor spots. Do not click walls, cardboard, chairs, or narrow gaps.

Verify the file:

```bash
cat landmarks/discovered_locations.yaml
```

## 6. Test one waypoint before running the tour

First test Nav2 directly from RViz with `Nav2 Goal`. If that works, test the tour node with a single waypoint:

```bash
cd ~/ros2_ws/FinalRobotProject
source /opt/ros/jazzy/setup.bash
source install/setup.bash
ros2 run tour_guide nav_node --landmarks $PWD/landmarks/discovered_locations.yaml --route 0 --once
```

If this fails, do not run `all`. Fix localization or move the waypoint farther into open floor.

## 7. Run the full classroom waypoint tour

```bash
cd ~/ros2_ws/FinalRobotProject
source /opt/ros/jazzy/setup.bash
source install/setup.bash
ros2 run tour_guide nav_node --landmarks $PWD/landmarks/discovered_locations.yaml --route all --once
```

Alternate routes:

```bash
ros2 run tour_guide nav_node --landmarks $PWD/landmarks/discovered_locations.yaml --route nearest --once
ros2 run tour_guide nav_node --landmarks $PWD/landmarks/discovered_locations.yaml --route 0,2,1 --once
```

## 8. Hard failures and what they mean

### Nav2 does not become active

Check that the desktop can see robot topics:

```bash
ros2 topic list | egrep '/scan|/tf|/odom'
```

Then check lifecycle nodes:

```bash
ros2 lifecycle get /map_server
ros2 lifecycle get /amcl
ros2 lifecycle get /controller_server
ros2 lifecycle get /planner_server
ros2 lifecycle get /bt_navigator
```

If `/map_server` or `/amcl` is missing, the Nav2 launch did not start correctly. Restart the `real_nav.launch.py` terminal.

### RViz shows the map but the robot does not move

This usually means one of three things:

1. Nav2 is not active.
2. The initial pose is wrong.
3. The waypoint is inside an obstacle or outside the usable map.

Do not keep changing code blindly. First prove RViz `Nav2 Goal` works.

### The robot spins, hesitates, or immediately aborts

Move the waypoint farther from walls/obstacles and reset the initial pose. The loggerhead map has a large origin offset, but RViz clicks are already in map coordinates, so use clicked points instead of guessing numbers.

## 9. Shutdown

Stop the tour node and Nav2 with `Ctrl+C`. On the robot terminal:

```bash
ros2 service call /stop_motor std_srvs/srv/Empty "{}"
```

Return the robot to its dock.
