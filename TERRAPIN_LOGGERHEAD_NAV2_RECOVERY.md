# Terrapin + Loggerhead Map Nav2 Recovery Runbook

Use this exact path when the map opens but Nav2 goals or waypoints do not activate. The goal is to run the TurtleBot named `terrapin` against the saved `loggerhead_classroom.yaml` map and prove one RViz Nav2 goal before running the tour node.

## Core rule

Do not remap unless the map is visibly wrong. If `loggerhead_classroom.pgm` and `loggerhead_classroom.yaml` load in RViz, the next problem is localization/lifecycle, not mapping.

## Terminal 0: clean old ROS processes on the desktop

Run this once before starting fresh:

```bash
pkill -f rviz2 || true
pkill -f nav2 || true
pkill -f amcl || true
pkill -f map_server || true
pkill -f lifecycle_manager || true
pkill -f ros2 || true
ros2 daemon stop
ros2 daemon start
```

Open fresh terminals after this.

## Every desktop terminal: connect to terrapin

Run the setup script in every new desktop terminal that will talk to the robot:

```bash
robot-setup.sh
```

Enter:

```text
terrapin
```

Then run the exact environment commands printed by the script. For the current terrapin session this has looked like:

```bash
unset ROS_LOCALHOST_ONLY
export ROS_DOMAIN_ID=5
export ROS_DISCOVERY_SERVER=";;;;;10.194.16.38:11811;"
export ROS_SUPER_CLIENT=True
ros2 daemon stop
ros2 daemon start
```

Then source the project:

```bash
cd ~/ros2_ws/FinalRobotProject
source /opt/ros/jazzy/setup.bash
source install/setup.bash
```

Verify robot topics from the desktop:

```bash
ros2 topic list | grep -E '/scan|/odom|/tf|/tf_static|/cmd_vel'
```

Required: `/scan`, `/odom`, `/tf`, `/tf_static`, and `/cmd_vel` should appear. If they do not, stop and fix discovery before touching Nav2.

## Terminal 1: launch localization + Nav2 on the loggerhead map

```bash
cd ~/ros2_ws/FinalRobotProject
source /opt/ros/jazzy/setup.bash
source install/setup.bash
ros2 launch tour_guide real_nav.launch.py map:=$(pwd)/src/tour_guide/maps/loggerhead_classroom.yaml
```

Leave this terminal running. Do not Ctrl-C it while checking lifecycle states.

## Terminal 2: open RViz navigation view

```bash
cd ~/ros2_ws/FinalRobotProject
source /opt/ros/jazzy/setup.bash
source install/setup.bash
ros2 launch turtlebot4_viz view_navigation.launch.py
```

In RViz:

1. Set Fixed Frame to `map` if it is not already set.
2. Confirm the loggerhead classroom map is visible.
3. Use `2D Pose Estimate` and place the robot on the map where the physical robot actually is.
4. Drag the arrow in the robot's real heading direction.
5. Wait 5 seconds.

This step is not optional. AMCL warnings saying `Please set the initial pose` mean the robot is not localized yet.

## Terminal 3: verify lifecycle after setting initial pose

Run this after the RViz 2D Pose Estimate:

```bash
for n in /map_server /amcl /controller_server /planner_server /bt_navigator /waypoint_follower; do
  echo "--- $n"
  ros2 lifecycle get $n || true
done
```

Expected target:

```text
/map_server: active
/amcl: active
/controller_server: active
/planner_server: active
/bt_navigator: active
/waypoint_follower: active
```

If some nodes are inactive or unconfigured, try activating the lifecycle managers rather than editing the map:

```bash
ros2 service call /lifecycle_manager_localization/manage_nodes nav2_msgs/srv/ManageLifecycleNodes "{command: 1}"
ros2 service call /lifecycle_manager_navigation/manage_nodes nav2_msgs/srv/ManageLifecycleNodes "{command: 1}"
```

Then check again:

```bash
for n in /map_server /amcl /controller_server /planner_server /bt_navigator /waypoint_follower; do
  echo "--- $n"
  ros2 lifecycle get $n || true
done
```

## Terminal 2/RViz: prove base Nav2 first

Before running the tour node, send one small nearby `Nav2 Goal` in RViz.

Pass condition:

- A path appears.
- The robot moves.
- The robot reaches a nearby open-floor goal.

If this fails, the tour node is not the problem. Fix initial pose, costmaps, or Nav2 lifecycle first.

Useful recovery commands:

```bash
ros2 service call /global_costmap/clear_entirely_global_costmap nav2_msgs/srv/ClearEntireCostmap "{}" || true
ros2 service call /local_costmap/clear_entirely_local_costmap nav2_msgs/srv/ClearEntireCostmap "{}" || true
```

Then reset the initial pose in RViz and send a closer goal.

## Terminal 4: run one waypoint first

Only after the RViz Nav2 Goal works:

```bash
cd ~/ros2_ws/FinalRobotProject
source /opt/ros/jazzy/setup.bash
source install/setup.bash
TOUR_GUIDE_STOP_DELAY=3.0 ros2 run tour_guide nav_node --landmarks $(pwd)/landmarks/locations.yaml --once --route 0
```

If stop 0 works, try nearest:

```bash
TOUR_GUIDE_STOP_DELAY=3.0 ros2 run tour_guide nav_node --landmarks $(pwd)/landmarks/locations.yaml --once --route nearest
```

## If AMCL still says initial pose is missing

Use the tour node to publish an initial pose only if you know a reasonable map-frame pose:

```bash
TOUR_GUIDE_STOP_DELAY=3.0 ros2 run tour_guide nav_node \
  --landmarks $(pwd)/landmarks/locations.yaml \
  --set-initial-pose --initial-x 0.0 --initial-y 0.0 --initial-yaw 0.0 \
  --once --route 0
```

Do not blindly use `0,0,0` unless the physical robot is actually near that pose on the map. A wrong initial pose is worse than no initial pose.

## Fast diagnosis

- `/scan`, `/odom`, `/tf` missing: robot discovery problem.
- Map visible but AMCL warns about initial pose: use RViz `2D Pose Estimate`.
- Lifecycle nodes unconfigured/inactive: call the lifecycle manager startup services above.
- RViz Nav2 Goal fails: do not run `nav_node`; the base stack is not ready.
- RViz goal works but tour fails: landmark YAML coordinates are bad or too close to obstacles.
- Single stop works but `nearest` fails: one later waypoint is bad; test stops individually.

## Demo wording

The safe claim is: Nav2 performs obstacle-aware planning and control; this package adds the mission layer by loading named classroom stops, selecting a route, and sending sequential Nav2 goals for a tour-guide behavior.
