# Testudo + loggerhead map Nav2 runbook

This is the fastest path for the real robot demo. Do not make a new map. Use the saved loggerhead classroom map:

```text
src/tour_guide/maps/loggerhead_classroom.yaml
src/tour_guide/maps/loggerhead_classroom.pgm
```

The current objective is not ArUco discovery. The current objective is:

1. connect the desktop to the real robot named `testudo`,
2. start LiDAR on the robot,
3. launch localization and Nav2 on `loggerhead_classroom.yaml`,
4. set AMCL initial pose in RViz,
5. prove one Nav2 goal works,
6. record or edit map-frame classroom stops,
7. run `nav_node` through those stops.

## Terminal 0: clean old desktop ROS state

Run this on the desktop before launching Nav2 if node discovery looks stale or inconsistent:

```bash
unset ROS_LOCALHOST_ONLY
unset ROS_AUTOMATIC_DISCOVERY_RANGE
unset ROS_STATIC_PEERS
unset ROS_DISCOVERY_SERVER
unset ROS_SUPER_CLIENT

ros2 daemon stop || true
ros2 daemon start
```

## Terminal 1: connect desktop to testudo

Run this in every desktop terminal that will use ROS 2 with the robot:

```bash
robot-setup.sh
```

When prompted, enter:

```text
testudo
```

Then run the exact environment commands printed by `robot-setup.sh`. Do not copy loggerhead or another robot's discovery-server IP unless the script prints it for `testudo`.

Verify robot topics from the desktop:

```bash
ros2 topic list | grep -E '^/(scan|odom|tf|cmd_vel)'
```

Do not continue until `/scan`, `/odom`, and `/tf` are visible.

## Terminal 2: robot SSH, start LiDAR

```bash
ssh student@testudo.cs.nor.ou.edu
ros2 service call /start_motor std_srvs/srv/Empty "{}"
ros2 topic list | grep -E '^/(scan|odom|tf)'
```

Leave this terminal available. If `/scan` is missing, restart the robot daemon:

```bash
turtlebot4-daemon-restart
ros2 daemon stop
ros2 daemon start
ros2 topic list | grep -E '^/(scan|odom|tf)'
```

## Terminal 3: build and launch loggerhead map localization/Nav2

Desktop terminal, after the `testudo` environment has been set:

```bash
cd ~/ros2_ws/FinalRobotProject
source /opt/ros/jazzy/setup.bash
source install/setup.bash
colcon build --symlink-install
source install/setup.bash

ros2 launch tour_guide real_nav.launch.py \
  map:=$HOME/ros2_ws/FinalRobotProject/src/tour_guide/maps/loggerhead_classroom.yaml \
  use_sim_time:=false \
  nav2_delay:=8.0
```

Keep this launch running. Do not run lifecycle checks from this same terminal.

## Terminal 4: RViz navigation view

Desktop terminal, after the `testudo` environment has been set:

```bash
source /opt/ros/jazzy/setup.bash
source ~/ros2_ws/FinalRobotProject/install/setup.bash
ros2 launch turtlebot4_viz view_navigation.launch.py
```

In RViz:

1. Set Fixed Frame to `map` if it is not already `map`.
2. Use `2D Pose Estimate` to put the robot where it actually is on the loggerhead map.
3. Rotate the green pose arrow to match the robot's real heading.
4. Wait a few seconds for AMCL particles to settle.
5. Send one short nearby `Nav2 Goal` in open floor.

AMCL warning `Please set the initial pose` is expected before step 2. It is not a map failure.

## Terminal 5: lifecycle check

Desktop terminal, after the `testudo` environment has been set:

```bash
source /opt/ros/jazzy/setup.bash
source ~/ros2_ws/FinalRobotProject/install/setup.bash

ros2 node list | sort | grep -E 'map_server|amcl|controller|planner|bt_navigator|waypoint|lifecycle'

for n in /map_server /amcl /controller_server /planner_server /bt_navigator /waypoint_follower; do
  echo "--- $n"
  ros2 lifecycle get $n || true
done
```

Healthy target:

```text
/map_server: active [3]
/amcl: active [3]
/controller_server: active [3]
/planner_server: active [3]
/bt_navigator: active [3]
/waypoint_follower: active [3]
```

If controller/planner are inactive or bt_navigator/waypoint_follower are unconfigured after 30 seconds, force lifecycle startup:

```bash
ros2 service call /lifecycle_manager_navigation/manage_nodes nav2_msgs/srv/ManageLifecycleNodes "{command: 1}"
```

Check again:

```bash
for n in /map_server /amcl /controller_server /planner_server /bt_navigator /waypoint_follower; do
  echo "--- $n"
  ros2 lifecycle get $n || true
done
```

If the nodes disappear entirely, the Nav2 launch is not running anymore. Go back to Terminal 3 and relaunch it; do not keep debugging lifecycle states for nodes that no longer exist.

## Create known classroom stops

Use the existing fallback file first:

```bash
cat ~/ros2_ws/FinalRobotProject/landmarks/locations.yaml
```

For real map-frame coordinates, use the recorder:

```bash
cd ~/ros2_ws/FinalRobotProject
source /opt/ros/jazzy/setup.bash
source install/setup.bash
mkdir -p landmarks
ros2 run tour_guide known_stop_recorder --output ~/ros2_ws/FinalRobotProject/landmarks/discovered_locations.yaml
```

In RViz, use `Publish Point` and click safe open-floor stops. Then inspect:

```bash
cat ~/ros2_ws/FinalRobotProject/landmarks/discovered_locations.yaml
```

Keep every stop in open floor. Bad stop placement near walls/desks will look like a Nav2 failure even when the software is fine.

## Run the tour node

After one manual RViz Nav2 goal succeeds:

```bash
cd ~/ros2_ws/FinalRobotProject
source /opt/ros/jazzy/setup.bash
source install/setup.bash

ros2 run tour_guide nav_node \
  --landmarks ~/ros2_ws/FinalRobotProject/landmarks/discovered_locations.yaml \
  --once \
  --route nearest
```

Fallback using committed static stops:

```bash
TOUR_GUIDE_LANDMARKS=~/ros2_ws/FinalRobotProject/landmarks/locations.yaml \
ros2 run tour_guide nav_node --once --route nearest
```

## Triage table

| Symptom | Meaning | Fix |
|---|---|---|
| `Node not found` for all Nav2 lifecycle nodes | Nav2 launch is not running or this terminal is not in the robot ROS environment | Re-run `robot-setup.sh` commands in that terminal, source the workspace, relaunch Terminal 3 |
| `/map_server` and `/amcl` active but controller/planner inactive | Navigation lifecycle did not finish | Wait 30 seconds, then call `/lifecycle_manager_navigation/manage_nodes` startup |
| AMCL says `Please set the initial pose` | Expected until localization is initialized | Use RViz `2D Pose Estimate` |
| RViz shows map but Nav2 goals do nothing | Usually lifecycle inactive or initial pose missing | Check lifecycle, set initial pose, try short nearby goal |
| Tour node hangs at `Waiting for Nav2 to become active` | Nav2 is not fully active | Do not debug tour node first; fix lifecycle first |
| Robot sees no `/scan` | LiDAR motor or robot bringup issue | Start motor from robot SSH; restart TurtleBot daemon if needed |

## Demo order

1. Show loggerhead map in RViz.
2. Set initial pose.
3. Send one nearby Nav2 goal.
4. Show `landmarks/discovered_locations.yaml` or `landmarks/locations.yaml`.
5. Run `nav_node --once --route nearest`.
6. Explain: Nav2 handles obstacle-aware path planning; this package handles tour-stop records, route selection, and sequential mission execution.
