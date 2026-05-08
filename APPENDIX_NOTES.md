# Appendix Documentation Notes

Include these files in the report appendices:

## Source code

- `src/tour_guide/tour_guide/navnode.py`
- `src/tour_guide/setup.py`
- `src/tour_guide/package.xml`
- `src/ros2_aruco/ros2_aruco/aruco_node.py`
- `src/ros2_aruco/ros2_aruco/aruco_generate_marker.py`
- `src/ros2_aruco_interfaces/msg/ArucoMarkers.msg`

## Launch files

- `src/tour_guide/launch/tour_guide.launch.py`
- `src/tour_guide/launch/aruco_tour.launch.py`
- `src/ros2_aruco/launch/aruco_oakd.launch.py`

## World and map files

- `src/tour_guide/worlds/tour_world.sdf`
- `src/tour_guide/maps/map_area.yaml`
- `src/tour_guide/maps/map_area.pgm`

## Launch file documentation

`tourt_guide.launch.py` starts only the tour-guide node. It is useful when ArUco detection is not needed or is being launched separately.

`aruco_tour.launch.py` starts both ArUco detection and the tour-guide node. It assumes the OAK-D camera topics are `/oakd/rgb/preview/image_raw` and `/oakd/rgb/preview/camera_info`.

`aruco_oakd.launch.py` starts the lightweight ArUco detector only. It publishes `/aruco_markers`, which the tour-guide node uses to register visible markers as landmarks.

## World file documentation

`tour_world.sdf` is a minimal Gazebo Harmonic world placeholder. It provides a ground plane and light source and can be extended with walls, tables, and ArUco marker models. The real-robot demo does not require this world file, but the assignment requires launch/world file documentation in the appendices.

## Map file documentation

`map_area.yaml` references `map_area.pgm`. This placeholder map should be replaced with a real map if Nav2 map-frame navigation is used. The current real-robot node uses `/navigate_to_position` in the odom frame because that was the action interface visible on the OU TurtleBot 4 during testing.
