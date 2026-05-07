# Known-Coordinate Classroom Tour Procedure

This is the fastest reliable path to a working real-robot tour demo.

Use Nav2 for collision-aware path planning and recovery behavior. This package provides the deliberative tour behavior: storing named classroom stops, choosing a route, and sending sequential goals to Nav2.

## Goal

Make the robot drive to known classroom coordinates in the saved map frame.

Required result:

1. A saved classroom map exists at `src/tour_guide/maps/classroom_map.yaml`.
2. Nav2/localization can load that map.
3. The robot can accept one manual RViz `Nav2 Goal`.
4. A YAML landmark file contains safe open-floor tour stops.
5. `ros2 run tour_guide nav_node --once --route nearest` drives the robot through those stops.

## Do not start with A*

Nav2 already has global and local planning. A separate A* route layer can be added later for route ordering, but it is not the next bottleneck. For the demo, the stronger claim is:

> Nav2 handles obstacle-aware path planning. This project adds the higher-level tour-guide mission layer: landmark storage, route selection, and sequential autonomous navigation to selected classroom stops.

Do not say the project implements A* unless there is actual code for it.

## Step 1: connect to the real robot

On every desktop terminal that needs ROS access to the robot, run:

```bash
robot-setup.sh
```

When prompted, enter the robot name:

```text
terrapin
```

Then run the environment commands printed by the script.

Verify that the desktop sees the robot:

```bash
ros2 topic list | grep -E '/scan|/odom|/tf|/cmd_vel'
```

You need `/scan`, `/odom`, and `/tf`. If these are missing, stop and fix connectivity. The tour node cannot work without the robot graph.

## Step 2: start the LiDAR motor

Robot terminal:

```bash
ros2 service call /start_motor std_srvs/srv/Empty "{}"
```

Confirm the LiDAR is physically spinning.

## Step 3: build the classroom map with manual driving

Desktop SLAM terminal:

```bash
cd ~/ros2_ws/FinalRobotProject
source /opt/ros/jazzy/setup.bash
source install/setup.bash 2>/dev/null || true
ros2 launch turtlebot4_navigation slam.launch.py
```

Desktop RViz terminal:

```bash
source /opt/ros/jazzy/setup.bash
ros2 launch turtlebot4_viz view_navigation.launch.py
```

Desktop teleop terminal:

```bash
source /opt/ros/jazzy/setup.bash
ros2 run teleop_twist_keyboard teleop_twist_keyboard --ros-args -p stamped:=true
```

Drive slowly. Rotate near the starting pose, drive the perimeter, pause near corners, drive through the center aisle, then return near the start. If the map doubles, tears, or rotates, delete it and remap slower.

## Step 4: save the map

Keep SLAM running while saving.

```bash
cd ~/ros2_ws/FinalRobotProject
mkdir -p src/tour_guide/maps
ros2 run nav2_map_server map_saver_cli -f src/tour_guide/maps/classroom_map
```

Expected files:

```text
src/tour_guide/maps/classroom_map.yaml
src/tour_guide/maps/classroom_map.pgm
```

Commit the map after it saves:

```bash
git add src/tour_guide/maps/classroom_map.yaml src/tour_guide/maps/classroom_map.pgm
git commit -m "Add real classroom map"
git push
```

## Step 5: launch Nav2/localization on the saved map

Stop SLAM first.

Desktop Nav2 terminal:

```bash
cd ~/ros2_ws/FinalRobotProject
source /opt/ros/jazzy/setup.bash
source install/setup.bash
ros2 launch tour_guide real_nav.launch.py map:=$HOME/ros2_ws/FinalRobotProject/src/tour_guide/maps/classroom_map.yaml
```

Desktop RViz terminal:

```bash
source /opt/ros/jazzy/setup.bash
ros2 launch turtlebot4_viz view_navigation.launch.py
```

In RViz, use `2D Pose Estimate` to place the robot where it actually is on the map. Then send one nearby `Nav2 Goal` in open floor. Do not run the full tour until a single RViz goal works.

## Step 6: record safe classroom coordinates

Create or edit:

```bash
mkdir -p ~/ros2_ws/FinalRobotProject/landmarks
nano ~/ros2_ws/FinalRobotProject/landmarks/discovered_locations.yaml
```

Use this format:

```yaml
landmarks:
  - name: Start Area
    x: 0.0
    y: 0.0
    yaw: 0.0
    description: Starting point for the classroom tour.
  - name: Front Landmark
    x: 1.0
    y: 0.5
    yaw: 0.0
    description: First classroom tour stop.
  - name: Center Landmark
    x: 0.0
    y: 1.5
    yaw: 1.57
    description: Second classroom tour stop.
```

Replace the numbers with real RViz map-frame coordinates.

## Step 7: run the known-coordinate tour

Interactive mode:

```bash
cd ~/ros2_ws/FinalRobotProject
source /opt/ros/jazzy/setup.bash
source install/setup.bash
ros2 run tour_guide nav_node --landmarks ~/ros2_ws/FinalRobotProject/landmarks/discovered_locations.yaml
```

Cleaner demo mode:

```bash
ros2 run tour_guide nav_node --landmarks ~/ros2_ws/FinalRobotProject/landmarks/discovered_locations.yaml --once --route nearest
```

## Demo wording

> The robot uses a saved classroom occupancy-grid map and Nav2 for collision-aware navigation. My added tour layer stores classroom landmarks as map-frame goals, allows the operator to choose a route, optionally orders the route by nearest-neighbor distance, and sends each stop to Nav2 as a sequential autonomous mission.

## Pass/fail checklist

You are ready for a demo only if all are true:

- `/scan`, `/odom`, and `/tf` are visible from the desktop.
- RViz shows a clean saved map.
- `real_nav.launch.py` loads the map.
- `2D Pose Estimate` correctly localizes the robot.
- One manual RViz `Nav2 Goal` works.
- `discovered_locations.yaml` uses real classroom coordinates.
- `nav_node --once --route nearest` reaches at least two stops.

If one manual Nav2 goal fails, the tour node is not the problem. Fix map/localization/Nav2 first.
