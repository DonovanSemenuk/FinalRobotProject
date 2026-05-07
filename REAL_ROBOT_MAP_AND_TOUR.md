# Real Robot Mapping and Tour Quickstart

This is the fast path for getting a TurtleBot 4 named `terrapin` mapped in the real classroom, then using that map for a waypoint tour.

## Goal for the next working session

1. Clone this repository on the lab desktop.
2. Connect the desktop to `terrapin`.
3. Start the LiDAR.
4. Run SLAM and RViz.
5. Teleoperate the robot slowly around the room to build a map.
6. Save the map into this repository.
7. Pick tour waypoint coordinates from RViz.
8. Run the tour node using those waypoints.

Do not start with custom A* unless Nav2 waypoint navigation is already working. For a 20-hour recovery timeline, a reliable Nav2-based waypoint tour is the highest-probability demo.

---

## 1. Clone the repository on the new computer

Open a desktop terminal:

```bash
mkdir -p ~/ros2_ws
cd ~/ros2_ws
git clone https://github.com/DonovanSemenuk/FinalRobotProject.git
cd FinalRobotProject
```

If the repository already exists:

```bash
cd ~/ros2_ws/FinalRobotProject
git pull origin main
```

---

## 2. Build the workspace

```bash
cd ~/ros2_ws/FinalRobotProject
source /opt/ros/jazzy/setup.bash
rosdep install --from-paths src -y --ignore-src
colcon build --symlink-install
source install/setup.bash
```

Every new terminal needs:

```bash
cd ~/ros2_ws/FinalRobotProject
source /opt/ros/jazzy/setup.bash
source install/setup.bash
```

---

## 3. Connect to `terrapin`

### Robot terminal

```bash
ssh student@terrapin.cs.nor.ou.edu
```

Then check robot topics:

```bash
ros2 topic list
```

Confirm these exist:

```text
/scan
/tf
/odom
```

If they are missing:

```bash
turtlebot4-daemon-restart
ros2 daemon stop
ros2 daemon start
ros2 topic list
```

Start the LiDAR motor from the robot terminal:

```bash
ros2 service call /start_motor std_srvs/srv/Empty "{}"
```

### Desktop terminal

Run this on the lab desktop, not inside SSH:

```bash
robot-setup.sh
```

Enter:

```text
terrapin
```

Follow the environment commands printed by the setup script. Then verify connection:

```bash
ros2 daemon stop
ros2 daemon start
ros2 topic list
```

The desktop must see `/scan`, `/tf`, and `/odom` before continuing.

---

## 4. Start SLAM for classroom mapping

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

In RViz, watch the map build as the robot moves.

---

## 5. Teleoperate slowly while mapping

Desktop Terminal 3:

```bash
cd ~/ros2_ws/FinalRobotProject
source /opt/ros/jazzy/setup.bash
source install/setup.bash
ros2 run teleop_twist_keyboard teleop_twist_keyboard --ros-args -p stamped:=true
```

Drive slowly. Do not whip the robot around. The goal is a clean map, not speed.

Suggested driving pattern:

1. Start near one wall.
2. Drive the room perimeter first.
3. Do slow rotations at corners.
4. Drive through the middle lanes.
5. Revisit any area that looks smeared or incomplete in RViz.

---

## 6. Save the real classroom map

Keep SLAM running. Open Desktop Terminal 4:

```bash
cd ~/ros2_ws/FinalRobotProject
source /opt/ros/jazzy/setup.bash
source install/setup.bash
mkdir -p src/tour_guide/maps
ros2 run nav2_map_server map_saver_cli -f src/tour_guide/maps/terrapin_classroom
```

This should create:

```text
src/tour_guide/maps/terrapin_classroom.yaml
src/tour_guide/maps/terrapin_classroom.pgm
```

Commit the map after verifying the files exist:

```bash
git status
git add src/tour_guide/maps/terrapin_classroom.yaml src/tour_guide/maps/terrapin_classroom.pgm
git commit -m "Add real classroom map"
git push origin main
```

---

## 7. Get waypoint coordinates from RViz

Use RViz's `Publish Point` tool or inspect the map coordinates around the stops you want. Choose 3 to 4 stops that are easy and safe.

Prioritize reliable locations:

1. Start area
2. Front board / presentation area
3. Table / desk area
4. Door / exit area

Update `landmarks/locations.yaml` with the map-frame coordinates.

Example format:

```yaml
waypoints:
  - name: Start Area
    x: 0.0
    y: 0.0
    yaw: 0.0
    description: Starting location for the tour.
  - name: Board Area
    x: 1.5
    y: 0.7
    yaw: 1.57
    description: Main classroom presentation area.
```

Commit the updated waypoints:

```bash
git add landmarks/locations.yaml
git commit -m "Update real classroom tour waypoints"
git push origin main
```

---

## 8. Run Nav2 with the saved map

Stop SLAM before launching localization/navigation.

Desktop Terminal 1:

```bash
cd ~/ros2_ws/FinalRobotProject
source /opt/ros/jazzy/setup.bash
source install/setup.bash
ros2 launch turtlebot4_navigation nav2.launch.py map:=$(pwd)/src/tour_guide/maps/terrapin_classroom.yaml
```

Desktop Terminal 2:

```bash
cd ~/ros2_ws/FinalRobotProject
source /opt/ros/jazzy/setup.bash
source install/setup.bash
ros2 launch turtlebot4_viz view_navigation.launch.py
```

In RViz, set the initial pose of the robot on the map. This is mandatory. If localization is wrong, the tour will fail even if the code is correct.

---

## 9. Run the tour node

Desktop Terminal 3:

```bash
cd ~/ros2_ws/FinalRobotProject
source /opt/ros/jazzy/setup.bash
source install/setup.bash
ros2 run tour_guide nav_node --landmarks $(pwd)/landmarks/locations.yaml
```

Useful route inputs:

```text
all
nearest
0,1,2
q
```

For demo reliability, test each single waypoint first:

```text
0
1
2
3
```

Only run `all` after every individual waypoint works.

---

## 10. Shutdown checklist

Robot terminal:

```bash
ros2 service call /stop_motor std_srvs/srv/Empty "{}"
```

Then return the robot to the charger.
