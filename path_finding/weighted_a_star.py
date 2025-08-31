from queue import PriorityQueue
from typing import List, Tuple, Optional, Dict, Any

from commands.command import Command
from commands.go_straight_command import StraightCommand
from commands.turn_command import TurnCommand
from misc.positioning import RobotPosition
from misc.type_of_turn import TypeOfTurn
from path_finding.modified_a_star import ModifiedAStar


class WeightedAStar(ModifiedAStar):
    """
    Weighted A* pathfinding algorithm that assigns different costs to different types of movements.
    Prioritizes straight movements over turns, with increasing penalties for larger turns.
    """

    # Movement weight constants
    WEIGHT_STRAIGHT = 0
    WEIGHT_SMALL_TURN = 10
    WEIGHT_MEDIUM_TURN = 20
    WEIGHT_LARGE_TURN = 30
    DEFAULT_WEIGHT = 100

    # Distance calculation constant
    DISTANCE_SCALE_FACTOR = 10

    # Large number for initialization
    INFINITY = 100000

    def __init__(self, grid, brain, start: RobotPosition, end: RobotPosition, yolo):
        """
        Initialize the Weighted A* pathfinder.

        Args:
            grid: The navigation grid
            brain: The robot's brain/controller
            start: Starting position of the robot
            end: Target position for the robot
            yolo: YOLO mode flag
        """
        super().__init__(grid, brain, start, end, yolo)

        # Movement weights - can be adjusted for different behaviors
        self.weight_straight = self.WEIGHT_STRAIGHT
        self.weight_small_turn = self.WEIGHT_SMALL_TURN
        self.weight_medium_turn = self.WEIGHT_MEDIUM_TURN
        self.weight_large_turn = self.WEIGHT_LARGE_TURN

    def distance_heuristic(self, curr_pos: RobotPosition) -> int:
        """
        Calculate the diagonal distance heuristic from current position to goal.

        Args:
            curr_pos: Current robot position

        Returns:
            Estimated distance cost to goal
        """
        sx, sy = curr_pos.x, curr_pos.y
        ex, ey = self.end.x, self.end.y

        # Calculate diagonal distance first, then remaining straight distance
        diag = min(abs(sx - ex), abs(sy - ey))

        # Move diagonally toward the goal
        sx += diag if sx < ex else -diag
        sy += diag if sy < ey else -diag

        # Return total distance scaled by distance factor
        return (diag + abs(sx - ex) + abs(sy - ey)) // self.DISTANCE_SCALE_FACTOR

    def get_weight(self, command: Command) -> int:
        """
        Get the movement weight for a specific command type.

        Args:
            command: The movement command to evaluate

        Returns:
            Weight/cost associated with the command
        """
        if isinstance(command, StraightCommand):
            return self.weight_straight
        elif isinstance(command, TurnCommand):
            turn_type = command.get_type_of_turn()
            if turn_type == TypeOfTurn.SMALL:
                return self.weight_small_turn
            elif turn_type == TypeOfTurn.MEDIUM:
                return self.weight_medium_turn
            elif turn_type == TypeOfTurn.LARGE:
                return self.weight_large_turn

        return self.DEFAULT_WEIGHT

    def _is_goal_reached(self, current_node: Tuple, goal_node: Tuple) -> bool:
        """
        Check if the current node matches the goal node (position and direction).

        Args:
            current_node: Current node (x, y, direction)
            goal_node: Goal node (x, y, direction)

        Returns:
            True if goal is reached, False otherwise
        """
        return (current_node[0] == goal_node[0] and
                current_node[1] == goal_node[1] and
                current_node[2] == goal_node[2])

    def start_weighted_astar(self, flag) -> Tuple[Optional[RobotPosition], List[Command]]:
        """
        Execute the weighted A* pathfinding algorithm.

        Args:
            flag: Processing flag for command extraction

        Returns:
            Tuple of (final_position, command_list) or (None, []) if no path found
        """
        frontier = PriorityQueue()
        backtrack: Dict[Tuple, Tuple[Optional[Tuple], Optional[Command]]] = {}
        cost: Dict[Tuple, int] = {}

        # Set up goal and start nodes
        goal_node = self.end.xy()
        goal_node_with_dir = goal_node + (self.end.direction,)

        start_node = self.start.xy()
        start_node_with_dir = start_node + (self.start.direction,)

        # Initialize search
        offset = 0
        frontier.put((0, offset, (start_node_with_dir, self.start)))
        cost[start_node_with_dir] = 0
        backtrack[start_node_with_dir] = (None, None)

        while not frontier.empty():
            priority, _, (current_node, current_position) = frontier.get()

            # Check if we've reached the goal
            if self._is_goal_reached(current_node, goal_node_with_dir):
                commands = self.extract_commands(backtrack, goal_node_with_dir, flag)
                return current_position, commands

            # Explore neighbors
            neighbors = self.get_neighbours(current_position)
            for new_node, new_pos, command_weight, command in neighbors:
                new_cost = cost.get(current_node, 0) + command_weight

                if new_cost < cost.get(new_node, self.INFINITY):
                    offset += 1
                    priority = (new_cost +
                                self.distance_heuristic(new_pos) +
                                self.direction_heuristic(new_pos) +
                                self.get_weight(command))

                    frontier.put((priority, offset, (new_node, new_pos)))
                    backtrack[new_node] = (current_node, command)
                    cost[new_node] = new_cost

        # No path found
        return None, []

    def start_astar(self, flag) -> Tuple[Optional[RobotPosition], List[Command]]:
        """
        Public interface for starting the A* search.

        Args:
            flag: Processing flag for command extraction

        Returns:
            Tuple of (final_position, command_list) or (None, []) if no path found
        """
        return self.start_weighted_astar(flag)