# Real TurtleBot Mapping Procedure

This is the first real-world milestone: create a usable classroom map while manually driving the TurtleBot. Do not start with custom A* or full autonomy. A bad map will make every later tour demo fail.

Target robot name used below: `terrapin`.

## What this proves

This step proves that the desktop can see the robot's ROS graph, the LiDAR is publishing, SLAM can build a map, and the robot can be manually driven through the classroom without bypassing the required ROS 2 stack.

## Terminal layout

Use four desktop terminals and one optional robot SSH terminal.

Every desktop terminal must run `robot-setup.sh` first. When prompted, enter:

```bash
terrapin
```

After the script prints the environment variables, run the commands it gives you. Then verify:

```bash
ros2 topic list | grep -E '/scan|/odom|/tf|/cmd_vel'
```

You must see at least `/scan`, `/odom`, and `/tf`. If not, stop. Fix connectivity before touching the project code.

## Optional robot-side check

From a desktop terminal:

```bash
ssh student@terrapin.cs.nor.ou.edu
ros2 topic list | grep -E '/scan|/odom|/tf'
```

If the robot does not show the core topics, restart the robot daemon:

```bash
turtlebot4-daemon-restart
```

Wait a few seconds and check topics again.

## Terminal 1: start or confirm LiDAR

Run this on the robot over SSH:

```bash
ros2 service call /start_motor std_srvs/srv/Empty "{}"
```

Confirm that the LiDAR is physically spinning. If `/scan` exists but RViz shows no laser points, the LiDAR motor is a prime suspect.

## Terminal 2: launch SLAM on the desktop

Run this on the desktop, not over SSH:

```bash
cd ~/ros2_ws/FinalRobotProject
source /opt/ros/jazzy/setup.bash
source install/setup.bash 2>/dev/null || true
ros2 launch turtlebot4_navigation slam.launch.py
```

Use synchronous, careful mapping first. A slow clean map is more valuable than a fast distorted one.

## Terminal 3: RViz map view

Run this on the desktop:

```bash
ros2 launch turtlebot4_viz view_navigation.launch.py
```

If `view_navigation.launch.py` is not available, use:

```bash
ros2 launch turtlebot4_viz view_robot.launch.py
```

In RViz, watch the map fill in. If the map tears, overlaps, or rotates badly, you are driving too fast or losing scan matching.

## Terminal 4: safe teleop

Run this on the desktop:

```bash
ros2 run teleop_twist_keyboard teleop_twist_keyboard --ros-args -p stamped:=true
```

Drive slowly:

- keep linear speed near `0.10 m/s`
- keep angular speed near `0.20 rad/s`
- make slow 360-degree turns near corners and doorways
- avoid people walking through the scan
- do not ram chair legs; they create noisy geometry and recovery behavior later

## Mapping route

Use this pattern:

1. Start near the expected tour start pose.
2. Rotate slowly once so SLAM gets a strong initial scan match.
3. Drive the room perimeter slowly.
4. Pause near corners and rotate slightly.
5. Drive through the center aisle.
6. Return near the start area.
7. Stop when RViz shows clean walls and major obstacles.

Do not over-map. A compact, clean classroom map beats a huge distorted map.

## Save the map

Create the map output folder:

```bash
mkdir -p ~/ros2_ws/FinalRobotProject/src/tour_guide/maps
cd ~/ros2_ws/FinalRobotProject
```

Save from the desktop while SLAM is still running:

```bash
ros2 run nav2_map_server map_saver_cli -f src/tour_guide/maps/classroom_map
```

You should get:

```text
src/tour_guide/maps/classroom_map.yaml
src/tour_guide/maps/classroom_map.pgm
```

If that fails because the map topic is not transient-local, try:

```bash
ros2 run nav2_map_server map_saver_cli -f src/tour_guide/maps/classroom_map --ros-args -p map_subscribe_transient_local:=true
```

## Commit the map

From the repo root:

```bash
cd ~/ros2_ws/FinalRobotProject
git status
git add src/tour_guide/maps/classroom_map.yaml src/tour_guide/maps/classroom_map.pgm
git commit -m "Add real classroom map"
git push
```

## First localization check after saving

Stop SLAM and RViz. Then launch localization/Nav2 with the saved map:

```bash
cd ~/ros2_ws/FinalRobotProject
source /opt/ros/jazzy/setup.bash
source install/setup.bash
ros2 launch tour_guide real_nav.launch.py map:=$HOME/ros2_ws/FinalRobotProject/src/tour_guide/maps/classroom_map.yaml
```

Open RViz again:

```bash
ros2 launch turtlebot4_viz view_navigation.launch.py
```

Use RViz `2D Pose Estimate` to align the robot with the map. If the robot pose jumps or drifts badly, the map is not demo-grade yet.

## Pass/fail criteria for this milestone

Pass:

- `/scan`, `/odom`, and `/tf` are visible from the desktop
- RViz displays live laser points
- SLAM produces a recognizable classroom map
- `classroom_map.yaml` and `classroom_map.pgm` save successfully
- Nav2/localization can load the saved map

Fail:

- you cannot see robot topics from the desktop
- the LiDAR is not spinning
- the map is warped or doubled
- localization cannot hold the robot pose on the saved map

Do not move to tour execution until this passes.