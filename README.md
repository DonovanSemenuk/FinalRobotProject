# FinalRobotProject

TurtleBot4 autonomous tour guide for a relocatable-landmark environment.

## Goal

The robot should:

1. Run in the TurtleBot4/Nav2 environment.
2. Detect ArUco landmarks using the OAK-D camera pipeline.
3. Save detected landmarks as map-frame tour stops.
4. Let the operator select a landmark order.
5. Navigate to each selected landmark and pause at each stop.

This implementation keeps Nav2 as the path planner. Do not spend demo time writing A*. Nav2 is responsible for collision-aware path planning; this package is responsible for landmark discovery, landmark-map generation, route selection, and tour execution.

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

## Launch simulation/Nav2

```bash
ros2 launch tour_guide launch.py
```

Wait until Nav2 is active before running the mapper or tour node.

## Phase 1: verify ArUco output

In a second terminal:

```bash
ros2 topic list | grep -i aruco
ros2 topic info /aruco_markers
```

The mapper expects `ros2_aruco_interfaces/msg/ArucoMarkers`, normally on `/aruco_markers`. If your ArUco node publishes a different topic, pass it with `--topic`.

## Phase 2: create or refresh landmarks from ArUco detections

For the cleanest demo, let the mapper slowly rotate the robot while collecting marker detections:

```bash
cd ~/ros2_ws/FinalRobotProject
source /opt/ros/jazzy/setup.bash
source install/setup.bash
ros2 run tour_guide landmark_mapper --topic /aruco_markers --sweep
```

The mapper averages repeated detections, computes a safe stop pose offset from each marker, and writes:

```text
~/ros2_ws/FinalRobotProject/landmarks/discovered_locations.yaml
```

Useful mapper options:

```bash
--stop-offset 0.65        # meters to stop in front of each marker
--min-samples 3           # ignore markers seen fewer than this many times
--angular-speed 0.35      # sweep turn speed in rad/s
--sweep-revolutions 1.0   # number of rotations during discovery
--output PATH             # write the discovered YAML somewhere else
```

If the robot cannot safely rotate in place, omit `--sweep` and drive/turn it manually while the mapper runs:

```bash
ros2 run tour_guide landmark_mapper --topic /aruco_markers
```

## Phase 3: run the tour

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

## Demo script

1. Launch simulation/Nav2.
2. Show the ArUco markers in the world or on the physical course.
3. Run `landmark_mapper --sweep`.
4. Show `landmarks/discovered_locations.yaml` being created with marker IDs, sample counts, and map-frame stop poses.
5. Run `nav_node`.
6. Select `nearest` or a custom route.
7. Explain that Nav2 handles collision-aware path planning while this project handles relocatable landmark discovery and tour sequencing.

## Fallback if ArUco detection fails on demo day

Use the static landmark file:

```bash
TOUR_GUIDE_LANDMARKS=~/ros2_ws/FinalRobotProject/landmarks/locations.yaml ros2 run tour_guide nav_node --once --route nearest
```

That still demonstrates operator route selection and Nav2 tour execution. Be honest that the dynamic detection phase was tested separately or is partially integrated.

## What to say if asked about A*

Do not claim that this project implements a custom A* planner unless you actually add one. The stronger answer is:

> This project uses Nav2 for path planning and obstacle-aware navigation. The project contribution is the higher-level behavior: discovering relocatable ArUco landmarks, converting detections into map-frame tour stops, letting the operator choose a tour order, and sending sequential goals to Nav2.
