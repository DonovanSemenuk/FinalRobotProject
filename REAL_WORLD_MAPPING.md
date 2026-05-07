# Real-World Classroom Mapping on OU TurtleBot 4

This checklist is for mapping the classroom with a physical OU TurtleBot 4 named `terrapin`, saving the generated map into this repository, and preparing the repo for tour execution.

## Goal for this phase

Create a real map of the demonstration space while manually driving the robot. Do not start with autonomous tours until this map exists and localization is stable.

Expected outputs:

- `src/tour_guide/maps/classroom.yaml`
- `src/tour_guide/maps/classroom.pgm`
- optional later output: `landmarks/discovered_locations.yaml`

## Safety rules

- Keep the robot on the floor.
- Do not lift it by the tower, OAK-D camera, or sensors.
- Drive slowly: use about `0.10 m/s` linear speed and `0.20 rad/s` turn speed.
- Keep one hand ready for emergency stop or `Ctrl+C`.
- Stop the LiDAR motor before docking the robot.

## Terminal 0: clean local ROS state on the desktop

Run this on the lab desktop before connecting to the robot:

```bash
pkill -f rviz2 || true
pkill -f gazebo || true
pkill -f gz || true
pkill -f nav2 || true
pkill -f slam || true
pkill -f teleop_twist_keyboard || true
pkill -f robot_state_publisher || true
ros2 daemon stop
ros2 daemon start
```

## Terminal 1: SSH into the robot

```bash
ssh student@terrapin.cs.nor.ou.edu
```

Then verify the robot is publishing core topics:

```bash
ros2 topic list | egrep '/scan|/tf|/odom'
```

If `/scan`, `/tf`, or `/odom` are missing:

```bash
turtlebot4-daemon-restart
sleep 10
ros2 topic list | egrep '/scan|/tf|/odom'
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

Run on the desktop, not inside SSH:

```bash
robot-setup.sh
```

Enter:

```text
terrapin
```

Run the environment commands printed by the script. Then verify the desktop can see robot topics:

```bash
ros2 daemon stop
ros2 daemon start
ros2 topic list | egrep '/scan|/tf|/odom'
```

If these topics do not appear on the desktop, stop. The desktop is not connected to the robot ROS graph yet.

## Terminal 3: start SLAM

Run on the desktop after `robot-setup.sh` has been applied in this terminal:

```bash
cd ~/ros2_ws/FinalRobotProject
source /opt/ros/jazzy/setup.bash
colcon build --symlink-install
source install/setup.bash
ros2 launch turtlebot4_navigation slam.launch.py
```

Keep this terminal running.

## Terminal 4: open mapping visualization

Run on the desktop after `robot-setup.sh` has been applied in this terminal:

```bash
source /opt/ros/jazzy/setup.bash
ros2 launch turtlebot4_viz view_navigation.launch.py
```

In RViz, verify:

- Laser scan points are visible.
- The map grows as the robot moves.
- The robot model does not jump wildly.

## Terminal 5: teleoperate slowly

Run on the desktop after `robot-setup.sh` has been applied in this terminal:

```bash
source /opt/ros/jazzy/setup.bash
ros2 run teleop_twist_keyboard teleop_twist_keyboard --ros-args -p stamped:=true
```

In the teleop window, reduce speed before driving:

- Press `z` until linear speed is near `0.10`.
- Press `x` until turn speed is near `0.20`.

Mapping pattern:

1. Start near the intended demo starting point.
2. Slowly drive the outer boundary of the classroom/demo area.
3. Slowly pass each hallway, wall, table, cardboard wall, and landmark area.
4. Rotate in place at corners so the LiDAR sees all walls.
5. Avoid fast turns. Fast turns create smeared maps.
6. Finish near the same starting point if possible.

## Save the map

When the map looks usable in RViz, keep SLAM running and open a new desktop terminal with `robot-setup.sh` applied:

```bash
cd ~/ros2_ws/FinalRobotProject
mkdir -p src/tour_guide/maps
ros2 run nav2_map_server map_saver_cli -f src/tour_guide/maps/classroom
ls -lh src/tour_guide/maps/classroom.*
```

You should see:

```text
src/tour_guide/maps/classroom.yaml
src/tour_guide/maps/classroom.pgm
```

## Quick map quality check

Open the YAML:

```bash
cat src/tour_guide/maps/classroom.yaml
```

Check that the `image:` field points to `classroom.pgm`. If it points to an absolute path, edit it to:

```yaml
image: classroom.pgm
```

## Commit the map

```bash
cd ~/ros2_ws/FinalRobotProject
git status
git add src/tour_guide/maps/classroom.yaml src/tour_guide/maps/classroom.pgm REAL_WORLD_MAPPING.md
git commit -m "Add real-world classroom mapping procedure"
git push origin main
```

## After mapping: run localization/Nav2 against the saved map

Stop SLAM with `Ctrl+C`, then launch navigation with the saved map:

```bash
cd ~/ros2_ws/FinalRobotProject
source /opt/ros/jazzy/setup.bash
source install/setup.bash
ros2 launch turtlebot4_navigation nav2.launch.py map:=$(pwd)/src/tour_guide/maps/classroom.yaml
```

Open RViz if needed:

```bash
ros2 launch turtlebot4_viz view_navigation.launch.py
```

Set the robot initial pose in RViz. If localization is unstable, do not start the tour node yet. Fix localization first.

## Shutdown

On the robot SSH terminal:

```bash
ros2 service call /stop_motor std_srvs/srv/Empty "{}"
```

Return the robot to the dock.
