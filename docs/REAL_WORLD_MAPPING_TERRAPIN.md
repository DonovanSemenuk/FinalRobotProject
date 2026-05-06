# Real-World Classroom Mapping on TurtleBot 4 `terrapin`

This is the first hardware step for the tour-guide project. Do this before editing landmark coordinates, ArUco tour stops, A* route ordering, or autonomous tour behavior.

## Goal

Create a usable occupancy-grid map of the classroom while manually driving `terrapin`. The output should be two files:

- `src/tour_guide/maps/classroom.yaml`
- `src/tour_guide/maps/classroom.pgm`

After those exist, Nav2 can localize against the real room and the tour-guide nodes can send map-frame goals.

## Safety rules

- Keep the robot on the floor.
- Carry it by the base, not the tower, camera, or sensors.
- Drive slowly: linear speed around `0.10`, angular speed around `0.20`.
- Keep one hand near the keyboard stop keys.
- Turn off the LiDAR motor and dock the robot when finished.

## Terminal 1: SSH into the robot

Run this from the lab desktop:

```bash
ssh student@terrapin.cs.nor.ou.edu
```

Verify the robot is publishing hardware topics:

```bash
ros2 topic list | grep -E "^/(scan|tf|odom)$"
```

Expected topics:

```text
/scan
/tf
/odom
```

If they are missing, restart the robot ROS daemon:

```bash
turtlebot4-daemon-restart
sleep 10
ros2 topic list | grep -E "^/(scan|tf|odom)$"
```

If they are still missing:

```bash
ros2 launch turtlebot4_bringup robot.launch.py
```

Start the LiDAR motor:

```bash
ros2 service call /start_motor std_srvs/srv/Empty "{}"
```

Leave this terminal open.

## Terminal 2: connect the desktop to `terrapin`

Open a new terminal on the desktop, not inside SSH:

```bash
robot-setup.sh
```

When prompted, enter:

```text
terrapin
```

Run the environment commands printed by `robot-setup.sh`. Then verify the desktop sees the robot:

```bash
ros2 daemon stop
ros2 daemon start
ros2 topic list | grep -E "^/(scan|tf|odom)$"
```

Do not continue until `/scan`, `/tf`, and `/odom` are visible from the desktop.

## Terminal 3: start SLAM/map building

Open another desktop terminal and run the same environment commands printed by `robot-setup.sh`.

Then start online async SLAM:

```bash
ros2 launch slam_toolbox online_async_launch.py use_sim_time:=false
```

If that launch file is not found, try:

```bash
ros2 launch turtlebot4_navigation slam.launch.py
```

Leave this terminal open.

## Terminal 4: RViz map view

Open another desktop terminal and run the same environment commands printed by `robot-setup.sh`.

Then run:

```bash
rviz2
```

In RViz:

1. Set Fixed Frame to `map`.
2. Add `Map` and select `/map`.
3. Add `LaserScan` and select `/scan`.
4. Add `TF`.
5. Watch whether walls appear as you drive.

## Terminal 5: manual driving

Open another desktop terminal and run the same environment commands printed by `robot-setup.sh`.

Start keyboard teleop slowly:

```bash
ros2 run teleop_twist_keyboard teleop_twist_keyboard --ros-args \
  -p stamped:=true \
  -p speed:=0.10 \
  -p turn:=0.20
```

Drive a slow loop around the room. Good mapping behavior:

- Start by rotating in place slowly so the robot sees the room outline.
- Drive along walls and around large obstacles.
- Avoid sharp fast turns.
- Revisit the starting area before saving the map.
- Stop if the map smears, doubles, or rotates incorrectly.

## Save the map

When the map looks usable in RViz, open one more desktop terminal with the same robot environment and go to the repo:

```bash
cd ~/ros2_ws/FinalRobotProject
mkdir -p src/tour_guide/maps
ros2 run nav2_map_server map_saver_cli -f src/tour_guide/maps/classroom
```

You should now have:

```bash
ls -lh src/tour_guide/maps/classroom.*
```

Expected output includes:

```text
src/tour_guide/maps/classroom.pgm
src/tour_guide/maps/classroom.yaml
```

Commit the map:

```bash
git status
git add src/tour_guide/maps/classroom.pgm src/tour_guide/maps/classroom.yaml docs/REAL_WORLD_MAPPING_TERRAPIN.md
git commit -m "Add real-world classroom mapping workflow"
git push
```

## Shutdown

In the SSH robot terminal:

```bash
ros2 service call /stop_motor std_srvs/srv/Empty "{}"
```

Then return the robot to the dock.

## Do not do these yet

- Do not implement A* yet.
- Do not tune tour landmarks yet.
- Do not run autonomous navigation before checking localization on the saved map.

A* only becomes useful after the map, localization, and basic Nav2 goal sending are reliable. For the demo, a clean map plus reliable sequential goal execution is more valuable than a fragile planner that fails under pressure.
