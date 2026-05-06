# Real TurtleBot 4 Classroom Mapping Procedure

This guide is for creating a real classroom map with the OU TurtleBot 4 named `terrapin`. The goal is to produce a usable occupancy-grid map that can later support Nav2 tour-guide navigation and landmark-based route execution.

## Purpose

Before running an autonomous tour, the robot needs a real map of the classroom/demo area. The map should be created by manually driving the robot while SLAM is running. After the map is saved, the resulting `.yaml` and `.pgm` files should be copied into `src/tour_guide/maps/` and used by Nav2.

## Terminal layout

Use at least four terminals:

1. Robot SSH terminal
2. Desktop robot-network terminal
3. Desktop SLAM/RViz terminal
4. Desktop teleoperation terminal

Every desktop terminal that talks to the robot must run the robot setup procedure or inherit the same ROS environment variables.

## 1. Robot terminal: connect to terrapin

```bash
ssh student@terrapin.cs.nor.ou.edu
```

Verify robot topics:

```bash
ros2 topic list
```

Confirm that these exist:

```text
/scan
/tf
/odom
/cmd_vel
```

If they are missing, restart the robot ROS daemon:

```bash
turtlebot4-daemon-restart
```

If topics are still missing after restart:

```bash
ros2 launch turtlebot4_bringup robot.launch.py
```

Start the LiDAR motor:

```bash
ros2 service call /start_motor std_srvs/srv/Empty "{}"
```

Leave this terminal open.

## 2. Desktop terminal: join the robot ROS network

On the lab desktop, not inside SSH:

```bash
robot-setup.sh
```

Enter:

```text
terrapin
```

Then run the environment commands printed by the script. They should look similar to this, but use the exact values printed for terrapin:

```bash
unset ROS_LOCALHOST_ONLY
export ROS_DOMAIN_ID=<printed_domain_id>
export ROS_DISCOVERY_SERVER="<printed_discovery_server>"
export ROS_SUPER_CLIENT=True
ros2 daemon stop
ros2 daemon start
```

Verify the desktop can see the robot:

```bash
ros2 topic list | grep -E '/scan|/odom|/tf|/cmd_vel'
```

Do not continue until `/scan`, `/odom`, and `/tf` appear from the desktop.

## 3. Start SLAM mapping

In a sourced desktop terminal:

```bash
source /opt/ros/jazzy/setup.bash
ros2 launch turtlebot4_navigation slam.launch.py
```

If that launch file is unavailable on the lab image, try:

```bash
source /opt/ros/jazzy/setup.bash
ros2 launch slam_toolbox online_async_launch.py use_sim_time:=false
```

Leave SLAM running.

## 4. Open RViz

In another sourced desktop terminal:

```bash
source /opt/ros/jazzy/setup.bash
ros2 launch turtlebot4_viz view_robot.launch.py
```

In RViz, confirm:

- Laser scan points appear.
- The map grows as the robot moves.
- The robot pose does not jump wildly.
- The map walls look straight enough to support navigation.

## 5. Teleoperate slowly while mapping

In another desktop terminal with the robot network environment active:

```bash
source /opt/ros/jazzy/setup.bash
ros2 run teleop_twist_keyboard teleop_twist_keyboard --ros-args -p stamped:=true
```

Use conservative speeds:

```text
speed: 0.10 m/s
turn:  0.20 rad/s
```

Mapping pattern:

1. Start near the intended demo starting location.
2. Drive around the perimeter first.
3. Point the LiDAR at walls, corners, doorways, and cardboard boundaries.
4. Make slow turns. Do not spin rapidly.
5. Revisit the starting area before saving the map to help loop closure.
6. Avoid bumping furniture or people.

Bad mapping behavior:

- Fast spinning
- Repeated collisions
- Driving through tight obstacles before the perimeter is mapped
- Saving before the map has clean walls
- Mapping a room layout different from the final demo layout

## 6. Save the map

Create a map output directory from the repository root:

```bash
cd ~/ros2_ws/FinalRobotProject
mkdir -p src/tour_guide/maps
```

Save the map:

```bash
ros2 run nav2_map_server map_saver_cli -f src/tour_guide/maps/classroom_map
```

Expected files:

```text
src/tour_guide/maps/classroom_map.yaml
src/tour_guide/maps/classroom_map.pgm
```

Check that they exist:

```bash
ls -lh src/tour_guide/maps/classroom_map.*
```

## 7. Commit the map

```bash
cd ~/ros2_ws/FinalRobotProject
git status
git add src/tour_guide/maps/classroom_map.yaml src/tour_guide/maps/classroom_map.pgm docs/REAL_ROBOT_MAPPING.md
git commit -m "Add real robot classroom mapping procedure and map files"
git push origin main
```

If the map files are large, check size before pushing:

```bash
du -h src/tour_guide/maps/classroom_map.*
```

## 8. Shutdown

Stop teleop, RViz, and SLAM with `Ctrl+C`.

On the robot SSH terminal:

```bash
ros2 service call /stop_motor std_srvs/srv/Empty "{}"
```

Return the robot to the charger.

## Success criteria

The mapping step is done only when:

- `classroom_map.yaml` and `classroom_map.pgm` exist.
- RViz shows clean, recognizable room geometry.
- The saved map matches the physical demo layout.
- The robot can later be localized on that map without the pose drifting immediately.

Do not start building route logic until this is true. A route planner cannot compensate for a bad map.