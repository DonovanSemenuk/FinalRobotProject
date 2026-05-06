"""Interactive landmark tour node for TurtleBot4/Nav2.

This node loads landmark goals from YAML, lets the operator choose a route,
and sends the robot through the selected landmarks with Nav2.
"""

from __future__ import annotations

import math
import os
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, List

import rclpy
import yaml
from ament_index_python.packages import get_package_share_directory
from geometry_msgs.msg import PoseStamped
from turtlebot4_navigation.turtlebot4_navigator import TurtleBot4Navigator


@dataclass
class Landmark:
    name: str
    x: float
    y: float
    yaw: float = 0.0
    marker_id: int | None = None
    description: str = ""


def yaw_to_quaternion(yaw: float):
    qz = math.sin(yaw / 2.0)
    qw = math.cos(yaw / 2.0)
    return qz, qw


def make_pose(x: float, y: float, yaw: float) -> PoseStamped:
    pose = PoseStamped()
    pose.header.frame_id = "map"
    pose.pose.position.x = float(x)
    pose.pose.position.y = float(y)
    pose.pose.position.z = 0.0
    qz, qw = yaw_to_quaternion(float(yaw))
    pose.pose.orientation.z = qz
    pose.pose.orientation.w = qw
    return pose


def default_landmark_file() -> Path:
    override = os.environ.get("TOUR_GUIDE_LANDMARKS")
    if override:
        return Path(override).expanduser().resolve()

    share = Path(get_package_share_directory("tour_guide"))
    installed = share / "landmarks" / "locations.yaml"
    if installed.exists():
        return installed

    source_tree = Path.cwd() / "landmarks" / "locations.yaml"
    return source_tree


def load_landmarks(path: Path) -> List[Landmark]:
    if not path.exists():
        raise FileNotFoundError(
            f"Landmark file not found: {path}. Set TOUR_GUIDE_LANDMARKS=/path/to/locations.yaml"
        )

    with path.open("r", encoding="utf-8") as handle:
        data = yaml.safe_load(handle) or {}

    raw_items = data.get("landmarks", data.get("waypoints", []))
    landmarks: List[Landmark] = []

    for index, item in enumerate(raw_items):
        if item is None:
            continue
        landmarks.append(
            Landmark(
                name=str(item.get("name", f"Landmark {index + 1}")),
                x=float(item["x"]),
                y=float(item["y"]),
                yaw=float(item.get("yaw", 0.0)),
                marker_id=item.get("marker_id"),
                description=str(item.get("description", "")),
            )
        )

    if not landmarks:
        raise ValueError(f"No landmarks found in {path}")
    return landmarks


def nearest_neighbor_order(landmarks: List[Landmark]) -> List[Landmark]:
    """Simple route ordering fallback. Not A*: it orders stops by greedy distance."""
    remaining = landmarks[:]
    route: List[Landmark] = []
    current_x, current_y = 0.0, 0.0

    while remaining:
        next_stop = min(remaining, key=lambda lm: math.hypot(lm.x - current_x, lm.y - current_y))
        route.append(next_stop)
        remaining.remove(next_stop)
        current_x, current_y = next_stop.x, next_stop.y

    return route


def parse_route(selection: str, landmarks: List[Landmark]) -> List[Landmark]:
    text = selection.strip().lower()
    if text in {"q", "quit", "exit"}:
        return []
    if text in {"all", "tour"}:
        return landmarks[:]
    if text in {"nearest", "auto", "optimized"}:
        return nearest_neighbor_order(landmarks)

    route: List[Landmark] = []
    for token in text.replace(" ", "").split(","):
        if token == "":
            continue
        index = int(token)
        if index < 0 or index >= len(landmarks):
            raise IndexError(f"Landmark index out of range: {index}")
        route.append(landmarks[index])
    return route


def print_menu(landmarks: Iterable[Landmark]) -> None:
    print("\nAvailable landmarks:")
    for index, landmark in enumerate(landmarks):
        marker = f" marker_id={landmark.marker_id}" if landmark.marker_id is not None else ""
        print(f"  {index}: {landmark.name} ({landmark.x:.2f}, {landmark.y:.2f}, yaw={landmark.yaw:.2f}){marker}")
    print("\nEnter one of these:")
    print("  single stop: 0")
    print("  custom tour: 0,2,1")
    print("  full listed tour: all")
    print("  greedy distance order: nearest")
    print("  quit: q")


def wait_for_navigation(navigator: TurtleBot4Navigator, poll_seconds: float = 0.5) -> None:
    """Wait when the TurtleBot4 navigator exposes task-completion APIs."""
    if not hasattr(navigator, "isTaskComplete"):
        return

    while rclpy.ok() and not navigator.isTaskComplete():
        time.sleep(poll_seconds)


def run_route(navigator: TurtleBot4Navigator, route: List[Landmark], stop_delay: float) -> None:
    for stop_number, landmark in enumerate(route, start=1):
        pose = make_pose(landmark.x, landmark.y, landmark.yaw)
        navigator.info(f"Stop {stop_number}/{len(route)}: navigating to {landmark.name}")
        navigator.startToPose(pose)
        wait_for_navigation(navigator)
        navigator.info(f"Arrived at {landmark.name}. Holding for {stop_delay:.1f} seconds.")
        if landmark.description:
            navigator.info(landmark.description)
        time.sleep(stop_delay)


def main(args=None):
    rclpy.init(args=args)
    navigator = TurtleBot4Navigator()

    landmark_path = default_landmark_file()
    landmarks = load_landmarks(landmark_path)
    stop_delay = float(os.environ.get("TOUR_GUIDE_STOP_DELAY", "5.0"))

    if os.environ.get("TOUR_GUIDE_SET_INITIAL_POSE", "1") != "0":
        initial_pose = make_pose(
            float(os.environ.get("TOUR_GUIDE_INITIAL_X", "0.0")),
            float(os.environ.get("TOUR_GUIDE_INITIAL_Y", "0.0")),
            float(os.environ.get("TOUR_GUIDE_INITIAL_YAW", "0.0")),
        )
        navigator.setInitialPose(initial_pose)

    navigator.info("Waiting for Nav2 to become active...")
    navigator.waitUntilNav2Active()
    navigator.info(f"Loaded {len(landmarks)} landmarks from {landmark_path}")

    try:
        while rclpy.ok():
            print_menu(landmarks)
            raw_input = input("Route selection: ")
            try:
                route = parse_route(raw_input, landmarks)
            except (ValueError, IndexError) as exc:
                navigator.error(str(exc))
                continue

            if not route:
                break

            names = " -> ".join(landmark.name for landmark in route)
            navigator.info(f"Starting route: {names}")
            run_route(navigator, route, stop_delay)
            navigator.info("Route complete.")
    except KeyboardInterrupt:
        navigator.info("Tour interrupted by operator.")
    finally:
        rclpy.shutdown()


if __name__ == "__main__":
    main()
