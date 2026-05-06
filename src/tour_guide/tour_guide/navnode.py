import rclpy
import time
from turtlebot4_navigation.turtlebot4_navigator import TurtleBot4Navigator, TurtleBot4Directions


def main(args=None):
    rclpy.init(args=args)

    navigator = TurtleBot4Navigator()

    # Set initial pose at origin where robot spawns
    initial_pose = navigator.getPoseStamped([0.0, 0.0], TurtleBot4Directions.NORTH)
    navigator.setInitialPose(initial_pose)

    # Wait for Nav2
    navigator.waitUntilNav2Active()

    # Your waypoints
    goal_options = [
        {'name': 'Waypoint 1',
         'pose': navigator.getPoseStamped([1.1,  2.08], TurtleBot4Directions.NORTH)},
        {'name': 'Waypoint 2',
         'pose': navigator.getPoseStamped([0.46, -2.21], TurtleBot4Directions.SOUTH)},
        {'name': 'Waypoint 3',
         'pose': navigator.getPoseStamped([0.50,  -2.21], TurtleBot4Directions.WEST)},
        {'name': 'Waypoint 4',
         'pose': navigator.getPoseStamped([1.0, 3.0], TurtleBot4Directions.NORTH)},
        {'name': 'Exit', 'pose': None}
    ]

    navigator.info('Welcome to the tour guide.')

    while True:
        options_str = 'Select a landmark:\n'
        for i in range(len(goal_options)):
            options_str += f'    {i}. {goal_options[i]["name"]}\n'

        raw_input = input(f'{options_str}Selection: ')

        try:
            selected_index = int(raw_input)
        except ValueError:
            navigator.error(f'Invalid input: {raw_input}')
            continue

        if selected_index < 0 or selected_index >= len(goal_options):
            navigator.error('Out of range')
        elif goal_options[selected_index]['name'] == 'Exit':
            break
        else:
            navigator.info(f'Going to {goal_options[selected_index]["name"]}')
            navigator.startToPose(goal_options[selected_index]['pose'])
            navigator.info('Arrived. Waiting 5 seconds...')
            time.sleep(5.0)

    rclpy.shutdown()


if __name__ == '__main__':
    main()
