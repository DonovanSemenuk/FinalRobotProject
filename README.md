# FinalRobotProject

TurtleBot 4 tour guide for OU's robotics course. The robot builds a classroom map, localizes on it, and autonomously drives to named stops using Nav2.

My package handles the higher-level tour logic — storing landmarks, letting the operator pick a route, and sending sequential navigation goals. Nav2 handles the actual path planning and obstacle avoidance.

## Build

```bash
cd ~/ros2_ws/FinalRobotProject
source /opt/ros/jazzy/setup.bash
rosdep install --from-paths src -y --ignore-src
colcon build --symlink-install
source install/setup.bash
```

Source this in every new terminal before running ROS commands:

```bash
source /opt/ros/jazzy/setup.bash && source install/setup.bash
```

## Connecting to the robot

Run `robot-setup.sh` on each desktop terminal that needs robot access, enter the robot name (e.g. `loggerhead`), then verify connectivity:

```bash
ros2 topic list | grep -E '/scan|/odom|/tf|/cmd_vel'
```

You need `/scan`, `/odom`, and `/tf` before doing anything else.

## Mapping the classroom

```bash
# terminal 1 — SLAM
ros2 launch turtlebot4_navigation slam.launch.py

# terminal 2 — RViz
ros2 launch turtlebot4_viz view_navigation.launch.py

# terminal 3 — teleop
ros2 run teleop_twist_keyboard teleop_twist_keyboard --ros-args -p stamped:=true
```

Drive slowly around the room. Once the map looks good, save it:

```bash
mkdir -p src/tour_guide/maps
ros2 run nav2_map_server map_saver_cli -f src/tour_guide/maps/classroom_map
```

## Localize and launch Nav2

Stop SLAM first, then:

```bash
ros2 launch tour_guide real_nav.launch.py map:=$HOME/ros2_ws/FinalRobotProject/src/tour_guide/maps/classroom_map.yaml
ros2 launch turtlebot4_viz view_navigation.launch.py
```

In RViz, use **2D Pose Estimate** to place the robot on the map, then send one **Nav2 Goal** to a nearby open-floor spot to confirm Nav2 is working before running the tour.

## Defining tour stops

### Option A: click stops in RViz

With Nav2 running, start the recorder:

```bash
ros2 run tour_guide known_stop_recorder --output ~/ros2_ws/FinalRobotProject/landmarks/discovered_locations.yaml
```

Set the RViz Fixed Frame to `map`, use **Publish Point**, and click open floor positions. Each click saves a stop.

### Option B: edit YAML directly

```yaml
landmarks:
  - name: Front of room
    x: 1.55
    y: 1.90
    yaw: 0.0
  - name: Back corner
    x: -0.31
    y: -0.07
    yaw: 0.0
```

Keep goals on open floor, away from walls and furniture.

## Running the tour

```bash
ros2 run tour_guide nav_node
```

Route options at the prompt:
- `all` — visit every stop in order
- `nearest` — greedy nearest-neighbor ordering
- `0,2,1` — custom order by index
- `q` — quit

One-shot for a clean demo:

```bash
ros2 run tour_guide nav_node --once --route nearest
```

To point at a specific landmark file:

```bash
ros2 run tour_guide nav_node --landmarks ~/ros2_ws/FinalRobotProject/landmarks/discovered_locations.yaml
```

## ArUco landmark detection

If ArUco markers are set up in the room, run the mapper while driving around:

```bash
ros2 run tour_guide landmark_mapper --topic /aruco_markers
```

Add `--sweep` to have the robot rotate in place and scan automatically. The mapper writes detected markers to `landmarks/discovered_locations.yaml`.

## Simulation

```bash
ros2 launch tour_guide launch.py
```

Wait for Nav2 to come up before running the tour node.
