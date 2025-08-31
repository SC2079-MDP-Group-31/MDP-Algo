import datetime
from typing import List, Tuple

import pygame

import constants as constants
import misc.timer as timer
from commands.go_straight_command import StraightCommand
from commands.turn_command import TurnCommand
from misc.direction import Direction
from misc.positioning import RobotPosition
from path_finding.hamiltonian import Hamiltonian


class Robot:
    """
    Robot class that handles movement, pathfinding, and rendering for a grid-based robot.

    The robot starts facing upward and uses internal angle tracking for precise movement.
    It can execute a series of commands to follow a Hamiltonian path through a grid.
    """

    COORDINATE_SCALE = 10  # Scale factor for grid coordinate conversion

    def __init__(self, grid) -> None:
        """
        Initialize robot at starting position.

        Args:
            grid: The grid environment for pathfinding
        """
        # Robot starts facing upward with internal angle tracking
        self.pos = RobotPosition(
            constants.ROBOT_SAFETY_DISTANCE,
            constants.ROBOT_SAFETY_DISTANCE,
            Direction.TOP,
            90,
        )

        self._start_position = self.pos.copy()
        self.hamiltonian = Hamiltonian(self, grid)

        # Path history for visualization
        self.path_history: List[Tuple[int, int]] = []

        # Command execution state
        self._current_command_index = 0
        self._total_time_printed = False

    def get_current_pos(self) -> RobotPosition:
        """Get the current robot position."""
        return self.pos

    def __str__(self) -> str:
        """String representation of robot position."""
        return f"Robot at {self.pos}"

    def set_position(self, x: int, y: int, direction: Direction) -> None:
        """
        Set robot position using grid coordinates.

        Args:
            x: Grid x-coordinate
            y: Grid y-coordinate
            direction: Facing direction
        """
        self.pos.x = constants.GRID_LENGTH - constants.GRID_CELL_LENGTH - (x * self.COORDINATE_SCALE)
        self.pos.y = y * self.COORDINATE_SCALE
        self.pos.direction = direction

    def set_position_task2(self, x: int, y: int, direction: Direction) -> None:
        """
        Set robot position for Task 2 using different grid dimensions.

        Args:
            x: Grid x-coordinate
            y: Grid y-coordinate
            direction: Facing direction
        """
        self.pos.x = constants.TASK2_LENGTH - constants.GRID_CELL_LENGTH - (x * self.COORDINATE_SCALE)
        self.pos.y = y * self.COORDINATE_SCALE
        self.pos.direction = direction

    def initialize_algorithm(self, grid) -> None:
        """
        Initialize the pathfinding algorithm from current position.

        Args:
            grid: The grid environment for pathfinding
        """
        self.pos = self.get_current_position()
        self._start_position = self.pos.copy()
        self.hamiltonian = Hamiltonian(self, grid)
        self.path_history.clear()
        self._current_command_index = 0
        self._total_time_printed = False

    def convert_commands_to_messages(self) -> List[str]:
        """
        Convert command objects to string messages.

        Returns:
            List of command strings
        """
        print("Converting commands to string...", end="")
        string_commands = [
            command.convert_to_message() for command in self.hamiltonian.commands
        ]
        print("Done!")
        return string_commands

    def turn(self, command_type: str, left: float, right: float, reverse: bool) -> None:
        """
        Execute a turn command.

        Args:
            command_type: Type of turn command
            left: Left turn parameter
            right: Right turn parameter
            reverse: Whether to reverse
        """
        turn_command = TurnCommand(command_type, left, right, reverse)
        turn_command.apply_on_pos(self.pos)

    def move_straight(self, distance: float) -> None:
        """
        Move robot straight by specified distance.

        Args:
            distance: Distance to move (negative for reverse)
        """
        straight_command = StraightCommand(distance)
        straight_command.apply_on_pos(self.pos)

    def _draw_hamiltonian_path(self, screen) -> None:
        """Draw the simple Hamiltonian path on screen."""
        if not self.hamiltonian.simple_hamiltonian:
            return

        prev_pos = self._start_position.xy_pygame()
        for obstacle in self.hamiltonian.simple_hamiltonian:
            target_pos = obstacle.get_robot_target_pos().xy_pygame()
            pygame.draw.line(screen, constants.DARK_GREEN, prev_pos, target_pos)
            prev_pos = target_pos

    def _draw_path_history(self, screen) -> None:
        """Draw the historical path taken by the robot."""
        for position in self.path_history:
            pygame.draw.circle(screen, constants.BLACK, position, 2)

    def draw(self, screen) -> None:
        """
        Draw the robot and its paths on screen.

        Args:
            screen: Pygame screen surface to draw on
        """
        self._draw_hamiltonian_path(screen)
        self._draw_path_history(screen)

    def _update_path_history(self) -> None:
        """Update the path history with current position if it's new."""
        current_pygame_pos = self.pos.xy_pygame()
        if (len(self.path_history) == 0 or
                current_pygame_pos != self.path_history[-1]):
            self.path_history.append(current_pygame_pos)

    def _execute_current_command(self) -> None:
        """Execute one tick of the current command."""
        if self._current_command_index >= len(self.hamiltonian.commands):
            return

        current_command = self.hamiltonian.commands[self._current_command_index]

        # Skip commands with zero ticks
        if current_command.total_ticks == 0:
            self._current_command_index += 1
            return

        # Process one tick of the command
        current_command.process_one_tick(self)

        # Check if command is completed
        if current_command.ticks <= 0:
            print(f"Finished processing {current_command}, {self.pos}")
            self._current_command_index += 1
            self._check_all_commands_completed()

    def _check_all_commands_completed(self) -> None:
        """Check if all commands are completed and print total time."""
        if (self._current_command_index >= len(self.hamiltonian.commands) and
                not self._total_time_printed):
            total_time = sum(command.time for command in self.hamiltonian.commands)
            total_time = round(total_time)

            print(f"All commands took {datetime.timedelta(seconds=total_time)}")
            self._total_time_printed = True
            timer.Timer.end_timer()

    def update(self) -> None:
        """
        Update robot state for one frame.

        Updates path history and executes current command if available.
        """
        self._update_path_history()
        self._execute_current_command()