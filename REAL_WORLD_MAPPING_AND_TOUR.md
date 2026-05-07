# Real-World Classroom Mapping and Tour Workflow

This is the hardware-first workflow for using an OU TurtleBot 4 as a classroom tour guide. The first objective is not autonomous touring. The first objective is a clean classroom map made while manually driving `terrapin`. Autonomous touring comes after the map exists and Nav2 can localize on it.

## System goal

The project mission is a TurtleBot 4 tour guide:

1. Build or load a map of the room.
2. Localize the robot in that map.
3. Discover or define landmarks.
4. Select a route.
5. Send Nav2 goals to each stop.

The current code supports the later phases with:

- `nav_node`: loads YAML landmark stops and sends them to Nav2.
- `landmark_mapper`: listens for ArUco detections and writes discovered landmark stops to YAML.
- `ros2_aruco`: detects ArUco markers from the OAK-D camera stream.

Do not skip mapping. If localization is bad, the tour will fail even if the route code is correct.

## Phase 1: connect to `terrapin`

### Robot terminal

SSH into the robot:

```bash
ssh student@terrapin.cs.nor.ou.edu
```

Verify core robot topics:

```bash
ros2 topic list | egrep '/scan|/tf|/odom'
```

If `/scan`, `/tf`, or `/odom` are missing:

```bash
turtlebot4-daemon-restart
sleep 10
ros2 topic list | egrep '/scan|/tf|/odom'
```

Start the LiDAR motor:

```bash
ros2 service call /start_motor std_srvs/srv/Empty "{}"
```

### Desktop terminal

Run this from the lab desktop, not inside SSH:

```bash
robot-setup.sh
```

Enter:

```text
terrapin
```

Then run the export commands printed by the script. Verify the desktop can see robot topics:

```bash
ros2 daemon stop
ros2 daemon start
ros2 topic list | egrep '/scan|/tf|/odom'
```

## Phase 2: teleop test before mapping

Use low speed. Do not test mapping until teleop is proven.

```bash
ros2 run teleop_twist_keyboard teleop_twist_keyboard --ros-args -p stamped:=true
```

Inside teleop, reduce speed before driving:

- linear speed around `0.10`
- turn speed around `0.20`

Drive forward, rotate, and stop. If the robot does not obey teleop, do not start SLAM yet.

## Phase 3: start SLAM Toolbox mapping

Open a new desktop terminal. Run the same ROS setup/export commands from `robot-setup.sh`, then:

```bash
source /opt/ros/jazzy/setup.bash
ros2 launch slam_toolbox online_async_launch.py use_sim_time:=false
```

If that launch file is not installed, install/use the lab-provided SLAM Toolbox package. The key requirement is that SLAM publishes the `map` frame and an occupancy grid while the robot is being driven.

## Phase 4: watch the map in RViz

Open another desktop terminal with the same robot environment:

```bash
source /opt/ros/jazzy/setup.bash
ros2 launch turtlebot4_viz view_robot.launch.py
```

In RViz:

1. Set fixed frame to `map`.
2. Add/display `Map` if it is not visible.
3. Confirm LiDAR scan points align with walls/furniture.

## Phase 5: manually scan the classroom

In the teleop terminal, drive slowly:

1. Start near the planned demo start position.
2. Drive the perimeter first.
3. Rotate slowly near corners and doorways.
4. Avoid fast turns; fast motion makes the map noisy.
5. Return near the starting area before saving.

Mapping standard: if the map is smeared, doubled, or has broken walls, throw it away and remap. A bad map will waste more time than remapping.

## Phase 6: save the classroom map

Create the map directory in the repo:

```bash
cd ~/ros2_ws/FinalRobotProject
mkdir -p src/tour_guide/maps
```

Save the map:

```bash
ros2 run nav2_map_server map_saver_cli -f src/tour_guide/maps/terrapin_classroom
```

Expected files:

```bash
ls src/tour_guide/maps/terrapin_classroom.*
```

You should see:

- `terrapin_classroom.yaml`
- `terrapin_classroom.pgm`

Commit the saved map:

```bash
git add src/tour_guide/maps/terrapin_classroom.yaml src/tour_guide/maps/terrapin_classroom.pgm
git commit -m "Add terrapin classroom map"
git push
```

## Phase 7: test Nav2 localization on the saved map

Stop SLAM. Keep the robot still. Then launch Nav2 with the saved map from a sourced desktop terminal:

```bash
cd ~/ros2_ws/FinalRobotProject
source /opt/ros/jazzy/setup.bash
source install/setup.bash
ros2 launch turtlebot4_navigation nav2.launch.py map:=$(pwd)/src/tour_guide/maps/terrapin_classroom.yaml
```

Open RViz if needed. Set the initial pose using RViz's `2D Pose Estimate`. Then test a small Nav2 goal nearby before attempting a tour.

Pass condition: the robot can drive a short goal and stop without spinning, drifting, or hitting furniture.

## Phase 8: add tour stops

There are two valid paths.

### Reliable path: hand-enter landmark stops

Create or edit:

```bash
landmarks/locations.yaml
```

Format:

```yaml
landmarks:
  - name: Stop 1
    x: 0.0
    y: 0.0
    yaw: 0.0
    description: First classroom stop
```

Use RViz `Publish Point`, `2D Goal Pose`, or `/clicked_point` to estimate map-frame coordinates. This is the lowest-risk demo path.

### Higher-risk path: ArUco-assisted landmarks

Start the OAK-D camera on the robot if needed:

```bash
ros2 launch turtlebot4_bringup oakd.launch.py
```

Start the ArUco detector using the package in this repo. Then run:

```bash
cd ~/ros2_ws/FinalRobotProject
source /opt/ros/jazzy/setup.bash
source install/setup.bash
ros2 run tour_guide landmark_mapper --output landmarks/discovered_locations.yaml --min-samples 3
```

If you want the robot to rotate in place while collecting detections:

```bash
ros2 run tour_guide landmark_mapper --output landmarks/discovered_locations.yaml --min-samples 3 --sweep --angular-speed 0.25
```

Only use this in an open area. If the camera/TF chain is unreliable, fall back to hand-entered stops.

## Phase 9: run the tour

With Nav2 active and localized:

```bash
cd ~/ros2_ws/FinalRobotProject
source /opt/ros/jazzy/setup.bash
source install/setup.bash
ros2 run tour_guide nav_node --landmarks landmarks/locations.yaml --route nearest --once
```

Or use discovered landmarks:

```bash
ros2 run tour_guide nav_node --landmarks landmarks/discovered_locations.yaml --route nearest --once
```

Manual menu mode:

```bash
ros2 run tour_guide nav_node --landmarks landmarks/locations.yaml
```

## 20-hour execution order

1. Get `terrapin` connected and teleop working.
2. Build a clean map.
3. Save and commit the map.
4. Launch Nav2 with that map.
5. Prove one short autonomous goal.
6. Add two hand-entered tour stops.
7. Prove `nav_node --route all --once`.
8. Add ArUco detection only after the basic tour works.
9. Add more stops and route ordering.
10. Record test results for report/poster.

## Demo fallback ladder

Use the highest working level during the demo:

1. Full: Nav2 localized on saved map, route visits multiple stops.
2. Medium: Nav2 visits one or two stops reliably.
3. Minimum: robot shows map/localization and accepts a tour stop goal.
4. Emergency: manually teleop while explaining the mapping, localization, route, and Nav2 goal pipeline.

Do not chase A* until the above works. Nav2 already uses global planning. Adding your own A* only helps if you can clearly show it improves route selection or planning behavior. For this deadline, nearest-neighbor tour ordering plus reliable Nav2 execution is the safer original contribution.

## Shutdown

On the robot:

```bash
ros2 service call /stop_motor std_srvs/srv/Empty "{}"
```

Return the robot to the dock.
