# Safe Report Results Wording

The final repository contains a robust tour-guide implementation with three execution paths: ArUco landmark registration, manual landmark registration, and a fixed fallback tour. The ArUco detector is implemented locally and avoids the previous `tf_transformations` dependency failure. The real-robot movement layer uses `/navigate_to_position`, which was the action server exposed by the OU TurtleBot 4 during testing. This design allows the project to demonstrate tour-guide behavior even if the camera pipeline is unavailable during the demo.
