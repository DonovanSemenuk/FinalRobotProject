# Real Robot Tour Demo Guide

This is the reliable path to a working TurtleBot4 tour demo on `terrapin` from the `robotics6` desktop.

## Mission cut line

Do not start by adding a custom planner. The demo must first prove this chain:

1. Desktop can see the real robot topics.
2. LiDAR is spinning.
3. A fresh classroom map exists.
4. Nav2 can localize the robot on that map.
5. A single RViz Nav2 goal works.
6. `nav_node` sends a sequence of known map-frame tour goals.

Only after all six work should ArUco marker discovery or route optimization be attempted.

## Terminal 1: connect desktop to terrapin

Run on the `robotics6` desktop, not inside SSH:

```bash
robot-setup.sh
```

Enter:

```text
terrapin
```

Then run the environment commands printed by the script. Verify:

```bash
ros2 topic list | grep -E '/scan|/odom|/tf|/cmd_vel'
```

Hard stop: if `/scan`, `/odom`, and `/tf` are not visible, do not continue.

## Terminal 2: robot SSH and LiDAR motor

```bash
ssh student@terrapin.cs.nor.ou.edu
ros2 topic list | grep -E '/scan|/odom|/tf'
ros2 service call /start_motor std_srvs/srv/Empty "{}"
```

If topics are missing on the robot:

```bash
turtlebot4-daemon-restart
ros2 topic list | grep -E '/scan|/odom|/tf'
```

## Terminal 3: build the repo

Run on the desktop:

```bash
cd ~/ros2_ws/FinalRobotProject
source /opt/ros/jazzy/setup.bash
rosdep install --from-paths src -y --ignore-src
colcon build --symlink-install
source install/setup.bash
```

## Terminal 4: make a new map

Run on the desktop:

```bash
source /opt/ros/jazzy/setup.bash
ros2 launch turtlebot4_navigation slam.launch.py
```

## Terminal 5: RViz for mapping

Run on the desktop:

```bash
source /opt/ros/jazzy/setup.bash
ros2 launch turtlebot4_viz view_robot.launch.py
```

Drive slowly. The map should grow cleanly. Do not rotate aggressively.

## Terminal 6: teleop

Run on the desktop:

```bash
source /opt/ros/jazzy/setup.bash
ros2 run teleop_twist_keyboard teleop_twist_keyboard --ros-args -p stamped:=true
```

Use low speed. Map the room edges and all interior walls or obstacles that matter for the tour.

## Save the map

After the map looks usable, run from the repo root:

```bash
cd ~/ros2_ws/FinalRobotProject
mkdir -p src/tour_guide/maps
ros2 run nav2_map_server map_saver_cli -f src/tour_guide/maps/classroom_map
ls -lh src/tour_guide/maps/classroom_map.*
```

Expected files:

```text
src/tour_guide/maps/classroom_map.yaml
src/tour_guide/maps/classroom_map.pgm
```

Commit the map only after confirming it is usable:

```bash
git status
git add src/tour_guide/maps/classroom_map.yaml src/tour_guide/maps/classroom_map.pgm
git commit -m "Add classroom map for real robot tour"
```

## Stop SLAM before localization

Close the SLAM launch. Do not run SLAM and localization at the same time for the demo.

## Launch localization and Nav2 on the saved map

```bash
cd ~/ros2_ws/FinalRobotProject
source /opt/ros/jazzy/setup.bash
source install/setup.bash
ros2 launch tour_guide real_nav.launch.py map:=$HOME/ros2_ws/FinalRobotProject/src/tour_guide/maps/classroom_map.yaml
```

## RViz navigation view

```bash
source /opt/ros/jazzy/setup.bash
ros2 launch turtlebot4_viz view_navigation.launch.py
```

In RViz:

1. Set the initial pose with `2D Pose Estimate`.
2. Use one nearby `Nav2 Goal` first.
3. Only continue if the robot reaches that single goal cleanly.

## Record known classroom tour stops from RViz

Run this while Nav2/RViz are open:

```bash
cd ~/ros2_ws/FinalRobotProject
source /opt/ros/jazzy/setup.bash
source install/setup.bash
rm -f landmarks/discovered_locations.yaml
ros2 run tour_guide known_stop_recorder --output ~/ros2_ws/FinalRobotProject/landmarks/discovered_locations.yaml --prefix "Classroom Stop"
```

In RViz, use `Publish Point` and click safe open-floor positions. Do not click walls, furniture, or exact marker positions. The robot goal should be reachable floor space near the classroom feature.

Check the file:

```bash
cat ~/ros2_ws/FinalRobotProject/landmarks/discovered_locations.yaml
```

Commit it:

```bash
cd ~/ros2_ws/FinalRobotProject
git add landmarks/discovered_locations.yaml
git commit -m "Add known classroom tour stops"
```

## Run the tour

Interactive:

```bash
cd ~/ros2_ws/FinalRobotProject
source /opt/ros/jazzy/setup.bash
source install/setup.bash
ros2 run tour_guide nav_node --landmarks ~/ros2_ws/FinalRobotProject/landmarks/discovered_locations.yaml
```

Cleaner one-shot demo:

```bash
cd ~/ros2_ws/FinalRobotProject
source /opt/ros/jazzy/setup.bash
source install/setup.bash
TOUR_GUIDE_STOP_DELAY=3 ros2 run tour_guide nav_node --landmarks ~/ros2_ws/FinalRobotProject/landmarks/discovered_locations.yaml --once --route nearest
```

## Demo talk track

Say this accurately:

> The robot first uses a saved occupancy-grid map and Nav2 localization. My added tour layer stores classroom tour stops in the map frame, allows an operator-selected or nearest-neighbor route order, and sends sequential Nav2 goals so the robot performs a classroom tour. Nav2 handles collision-aware navigation; the project software handles the mission-level tour behavior.

Do not claim a custom A* planner exists unless it is actually implemented and tested.

## Failure triage

### `ros2 topic list` cannot see robot topics

Re-run `robot-setup.sh` in that terminal and restart the daemon:

```bash
ros2 daemon stop
ros2 daemon start
ros2 topic list | grep -E '/scan|/odom|/tf'
```

### RViz shows no laser scan

Start the LiDAR motor on the robot SSH terminal:

```bash
ros2 service call /start_motor std_srvs/srv/Empty "{}"
```

### Nav2 does not move

Check lifecycle and action topics:

```bash
ros2 node list | grep -E 'controller|planner|bt_navigator|amcl|map_server'
ros2 action list | grep navigate
```

Then set `2D Pose Estimate` again in RViz. Bad localization is the most common cause.

### Tour node says no landmark file

Run:

```bash
ls -lh ~/ros2_ws/FinalRobotProject/landmarks/discovered_locations.yaml
cat ~/ros2_ws/FinalRobotProject/landmarks/discovered_locations.yaml
```

Then pass the path explicitly:

```bash
ros2 run tour_guide nav_node --landmarks ~/ros2_ws/FinalRobotProject/landmarks/discovered_locations.yaml --once --route nearest
```

## End-of-session robot safety

Before leaving:

```bash
ssh student@terrapin.cs.nor.ou.edu
ros2 service call /stop_motor std_srvs/srv/Empty "{}"
```

Return the robot to the dock.
