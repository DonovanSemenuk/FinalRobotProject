# Running the Tour Guide on an OU TurtleBot 4

This package contains a ROS 2 TurtleBot 4 tour-guide node. In simulation, use the package launch file to bring up Gazebo Harmonic, Nav2, the included map, and the included world. On the real OU TurtleBot 4, connect the lab desktop to the robot first, verify that the robot is publishing ROS topics, then run only the tour-guide node from the desktop terminal.

## 1. Build the workspace on the lab desktop

From the repository root on the Ubuntu 24.04 desktop:

```bash
cd /workspace/FinalRobotProject
source /opt/ros/jazzy/setup.bash
rosdep install --from-paths src -y --ignore-src
colcon build --symlink-install
source install/setup.bash
```

Open every new terminal from this repository and source both ROS and the workspace before running ROS commands:

```bash
cd /workspace/FinalRobotProject
source /opt/ros/jazzy/setup.bash
source install/setup.bash
```

## 2. Optional: test the project in simulation first

Use this when you want to verify that the package starts correctly before using hardware:

```bash
ros2 launch tour_guide launch.py
```

In a second sourced desktop terminal, start the interactive tour menu:

```bash
ros2 run tour_guide nav_node
```

The node prints a landmark menu. Enter the number for a waypoint, wait for the robot to drive there, and enter `4` to exit.

## 3. Connect to the real OU TurtleBot 4

Replace `<robot_name>` with the name printed on the TurtleBot, such as `matamata`.

### Robot terminal: SSH into the TurtleBot

```bash
ssh student@<robot_name>.cs.nor.ou.edu
```

After logging into the Raspberry Pi, verify that the robot topics exist:

```bash
ros2 topic list
```

Confirm that `/scan`, `/tf`, and `/odom` are visible. If they are missing, restart ROS discovery on the robot:

```bash
turtlebot4-daemon-restart
```

If the topics are still missing after the robot finishes booting, manually start bringup:

```bash
ros2 launch turtlebot4_bringup robot.launch.py
```

Start the LiDAR motor before navigating:

```bash
ros2 service call /start_motor std_srvs/srv/Empty "{}"
```

### Desktop terminal: join the robot ROS network

On the lab desktop, do not SSH for this step:

```bash
robot-setup.sh
```

Enter the TurtleBot name when prompted. Then follow the environment-variable commands printed by the script. After that, restart the ROS daemon and verify that the desktop can see the robot:

```bash
ros2 daemon stop
ros2 daemon start
ros2 topic list
```

You should see robot topics such as `/scan`, `/tf`, and `/odom` from the desktop terminal.

## 4. Start navigation support for the real robot

The tour-guide node sends goals through Nav2, so the real robot must have localization and Nav2 active before starting the tour menu.

If your robot already has a saved map and Nav2 launch command supplied by the lab, start that command in a sourced desktop terminal. If you are using this repository's included map as a placeholder, you can pass it to the TurtleBot 4 navigation launch setup used in your lab environment. For example, if your TurtleBot 4 image provides the standard navigation launch file:

```bash
ros2 launch turtlebot4_navigation nav2.launch.py map:=$(pwd)/src/tour_guide/maps/map_area.yaml
```

Keep this Nav2 terminal running. In RViz, set the robot's initial pose if needed so the map frame matches the physical robot's location.

> Important: the hard-coded tour waypoints in `tour_guide/navnode.py` are map-frame coordinates. For the real classroom demo, update those coordinates to match the map you are using before running the tour.

## 5. Run the tour-guide node on the desktop

In a new sourced desktop terminal that has also run the `robot-setup.sh` instructions:

```bash
cd /workspace/FinalRobotProject
source /opt/ros/jazzy/setup.bash
source install/setup.bash
ros2 run tour_guide nav_node
```

Use the menu:

- `0` sends the robot to Waypoint 1.
- `1` sends the robot to Waypoint 2.
- `2` sends the robot to Waypoint 3.
- `3` sends the robot to Waypoint 4.
- `4` exits the program.

Watch the robot while it moves. Be ready to stop the program with `Ctrl+C` or use teleoperation/emergency stop if the map, localization, or waypoint coordinates are wrong.

## 6. Shutdown checklist

When finished:

1. Stop the tour node with menu option `4` or `Ctrl+C`.
2. Stop Nav2/RViz/other launch files with `Ctrl+C`.
3. On the robot terminal, stop the LiDAR motor:

   ```bash
   ros2 service call /stop_motor std_srvs/srv/Empty "{}"
   ```

4. Return the TurtleBot to its charging dock.
