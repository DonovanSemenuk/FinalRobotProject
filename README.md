# FinalRobotProject

TurtleBot4 autonomous tour guide for a relocatable-landmark environment.

## Goal

The robot should:

1. Run in the TurtleBot4/Nav2 environment.
2. Detect ArUco landmarks using the OAK-D camera pipeline.
3. Save detected landmarks as map-frame tour stops.
4. Let the operator select a landmark order.
5. Navigate to each selected landmark and pause at each stop.

This implementation keeps Nav2 as the path planner. Do not spend demo time writing A*. A* is already conceptually inside global planning; the grading-visible work is landmark detection, map creation, user selection, and tour execution.

## Build

From the workspace root:

```bash
cd ~/ros2_ws/FinalRobotProject
colcon build --symlink-install
source install/setup.bash
```

## Launch simulation/Nav2

```bash
ros2 launch tour_guide launch.py
```

Wait until Nav2 is active before running the tour node.

## Phase 1: create or refresh landmarks from ArUco detections

In a second terminal:

```bash
cd ~/ros2_ws/FinalRobotProject
source install/setup.bash
ros2 run tour_guide landmark_mapper --topic /aruco_poses --marker-ids 0,1,2,3
```

Drive or rotate the robot so the camera sees the markers. The mapper writes:

```text
~/ros2_ws/FinalRobotProject/landmarks/discovered_locations.yaml
```

If the ArUco node publishes a different PoseArray topic, find it with:

```bash
ros2 topic list | grep -i aruco
ros2 topic info /THE_TOPIC_NAME
```

Then rerun the mapper with `--topic /THE_TOPIC_NAME`.

## Phase 2: run the tour

Interactive mode:

```bash
source install/setup.bash
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

## Demo script

1. Launch simulation/Nav2.
2. Show the ArUco markers in the world or on the physical course.
3. Run `landmark_mapper` while rotating/driving the robot.
4. Show `landmarks/discovered_locations.yaml` being created.
5. Run `nav_node`.
6. Select `nearest` or a custom route.
7. Explain that Nav2 handles collision-aware path planning while this project handles relocatable landmark discovery and tour sequencing.

## Fallback if ArUco detection fails on demo day

Use the static landmark file:

```bash
TOUR_GUIDE_LANDMARKS=~/ros2_ws/FinalRobotProject/landmarks/locations.yaml ros2 run tour_guide nav_node --once --route nearest
```

That still demonstrates operator route selection and Nav2 tour execution. Be honest that the dynamic detection phase was tested separately or is partially integrated.
