# Loggerhead Map and Tour Runbook

Use this file for the current real-robot demo path. The goal is not to build a custom planner first. The goal is to make the TurtleBot named `loggerhead` build a fresh classroom map, localize on it, and drive to known classroom coordinates using Nav2.

## Mission for the next 11 hours

1. Connect the lab desktop to `loggerhead`.
2. Confirm the desktop can see `/scan`, `/odom`, `/tf`, and `/cmd_vel`.
3. Build a fresh map using SLAM.
4. Save the map into `src/tour_guide/maps/loggerhead_classroom.yaml` and `.pgm`.
5. Launch Nav2/localization on that saved map.
6. Use RViz `2D Pose Estimate` to localize the robot.
7. Test one RViz `Nav2 Goal` before running the tour node.
8. Run `nav_node` against `landmarks/locations.yaml` or update that file with better map-frame coordinates.

Do not skip steps 2, 6, or the single RViz test goal. If those fail, the tour node is not the problem.

---

## 0. Clean old ROS state on the desktop

Run this before starting if terminals are messy:

```bash
pkill -f ros2 || true
pkill -f rviz2 || true
pkill -f gz || true
ros2 daemon stop
ros2 daemon start
```

Then open fresh terminals.

---

## 1. Pull and build the repo

```bash
cd ~/ros2_ws/FinalRobotProject
git pull origin main
source /opt/ros/jazzy/setup.bash
rosdep install --from-paths src -y --ignore-src
colcon build --symlink-install
source install/setup.bash
```

Every new desktop terminal needs:

```bash
cd ~/ros2_ws/FinalRobotProject
source /opt/ros/jazzy/setup.bash
source install/setup.bash
```

---

## 2. Connect to loggerhead

On the lab desktop, run:

```bash
robot-setup.sh
```

Enter:

```text
loggerhead
```

Run the environment commands printed by `robot-setup.sh` in that terminal.

Verify the desktop can see the robot:

```bash
ros2 topic list | grep -E '/scan|/odom|/tf|/cmd_vel'
```

Required result: you should see `/scan`, `/odom`, `/tf`, and `/cmd_vel`. If not, stop. Fix robot network discovery first.

Optional robot SSH terminal:

```bash
ssh student@loggerhead.cs.nor.ou.edu
ros2 service call /start_motor std_srvs/srv/Empty "{}"
```

If `/start_motor` is not available, check whether the LiDAR is already publishing with:

```bash
ros2 topic echo /scan --once
```

---

## 3. Start SLAM mapping

Desktop Terminal 1:

```bash
cd ~/ros2_ws/FinalRobotProject
source /opt/ros/jazzy/setup.bash
source install/setup.bash
ros2 launch turtlebot4_navigation slam.launch.py
```

Desktop Terminal 2:

```bash
cd ~/ros2_ws/FinalRobotProject
source /opt/ros/jazzy/setup.bash
source install/setup.bash
ros2 launch turtlebot4_viz view_navigation.launch.py
```

Desktop Terminal 3 for teleop:

```bash
cd ~/ros2_ws/FinalRobotProject
source /opt/ros/jazzy/setup.bash
source install/setup.bash
ros2 run teleop_twist_keyboard teleop_twist_keyboard --ros-args -p stamped:=true
```

Mapping rules:

- Drive slowly.
- Map the perimeter first.
- Rotate slowly at corners.
- Do not let the map smear. If it smears badly, restart SLAM and remap.
- Keep the robot away from chair legs and tight clutter during mapping.

---

## 4. Save the new map

Keep SLAM running. In Desktop Terminal 4:

```bash
cd ~/ros2_ws/FinalRobotProject
source /opt/ros/jazzy/setup.bash
source install/setup.bash
mkdir -p src/tour_guide/maps
ros2 run nav2_map_server map_saver_cli -f src/tour_guide/maps/loggerhead_classroom
ls -lh src/tour_guide/maps/loggerhead_classroom.*
```

Expected files:

```text
src/tour_guide/maps/loggerhead_classroom.yaml
src/tour_guide/maps/loggerhead_classroom.pgm
```

Commit the map only after RViz shows it is usable:

```bash
git add src/tour_guide/maps/loggerhead_classroom.yaml src/tour_guide/maps/loggerhead_classroom.pgm
git commit -m "Add loggerhead classroom map"
git push origin main
```

---

## 5. Launch Nav2/localization on the saved map

Stop SLAM first. Then run:

Desktop Terminal 1:

```bash
cd ~/ros2_ws/FinalRobotProject
source /opt/ros/jazzy/setup.bash
source install/setup.bash
ros2 launch tour_guide real_nav.launch.py map:=$(pwd)/src/tour_guide/maps/loggerhead_classroom.yaml
```

Desktop Terminal 2:

```bash
cd ~/ros2_ws/FinalRobotProject
source /opt/ros/jazzy/setup.bash
source install/setup.bash
ros2 launch turtlebot4_viz view_navigation.launch.py
```

In RViz:

1. Set the fixed frame to `map` if needed.
2. Use `2D Pose Estimate` to place the robot on the map.
3. Match the robot's direction as accurately as possible.
4. Wait a few seconds for localization to settle.

This step is mandatory. Bad initial pose makes good code look broken.

---

## 6. Prove Nav2 works before running the tour node

In RViz, use `Nav2 Goal` and send the robot to one nearby open-floor point.

Pass condition:

- Robot plans a path.
- Robot starts moving.
- Robot reaches the nearby point without spinning forever.

Fail condition:

- No path appears.
- Robot does not move.
- Robot drives the wrong direction because localization is wrong.

If this fails, do not run `nav_node` yet. Fix map/localization/Nav2 first.

---

## 7. Update or verify tour coordinates

The tour node reads this file by default:

```text
landmarks/locations.yaml
```

Current format:

```yaml
landmarks:
  - name: Classroom Stop 1
    x: 1.55
    y: 1.90
    yaw: 0.0
    description: First manually defined classroom tour stop.
```

Use RViz to choose conservative open-floor coordinates. Do not place goals against walls, under desks, inside chair clusters, or directly on top of obstacles.

After editing:

```bash
git add landmarks/locations.yaml
git commit -m "Update loggerhead classroom tour stops"
git push origin main
```

---

## 8. Run the tour node

Interactive mode:

```bash
cd ~/ros2_ws/FinalRobotProject
source /opt/ros/jazzy/setup.bash
source install/setup.bash
ros2 run tour_guide nav_node --landmarks $(pwd)/landmarks/locations.yaml
```

Safer one-shot mode:

```bash
TOUR_GUIDE_STOP_DELAY=3.0 ros2 run tour_guide nav_node --landmarks $(pwd)/landmarks/locations.yaml --once --route nearest
```

Testing order:

1. Run a single stop: enter `0`.
2. Run another single stop: enter `1`.
3. Only then run `nearest` or `all`.

Useful inputs:

```text
0
1
2
3
all
nearest
0,2,1
q
```

---

## 9. What to say during the demo

Say this plainly:

> The robot uses SLAM to create a classroom occupancy-grid map, then localizes against the saved map. Nav2 handles obstacle-aware path planning. My package handles the higher-level tour-guide behavior: loading named classroom stops, letting the operator choose a route, and sending sequential navigation goals to the robot.

Do not claim custom A* unless it exists and has been tested. A broken custom planner is worse than a working Nav2 tour.

---

## 10. Fast failure diagnosis

### Desktop cannot see `/scan`, `/odom`, or `/tf`

Problem: robot connection/discovery, not tour code.

Fix:

```bash
robot-setup.sh
ros2 daemon stop
ros2 daemon start
ros2 topic list | grep -E '/scan|/odom|/tf|/cmd_vel'
```

### RViz map is smeared

Problem: bad SLAM map.

Fix: remap slowly. Do not salvage a bad map.

### Nav2 goal in RViz fails

Problem: Nav2/localization/map/costmap.

Fix: reset initial pose, choose a closer open-floor goal, clear costmaps if available, or relaunch Nav2.

### RViz goal works but `nav_node` fails

Problem: landmark coordinates or YAML path.

Fix: test one coordinate at a time and move goals farther from obstacles.

---

## 11. Shutdown

Robot SSH terminal if `/stop_motor` is available:

```bash
ros2 service call /stop_motor std_srvs/srv/Empty "{}"
```

Return the robot to the charger.
