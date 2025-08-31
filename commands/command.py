import math
from abc import ABC, abstractmethod
from typing import Any

import constants


class Command(ABC):
    """Abstract base class for robot commands with time-based execution."""

    def __init__(self, time: float) -> None:
        """
        Initialize a command with execution time.

        Args:
            time: Duration in seconds for command execution
        """
        self.time = time

        # Calculate number of frame ticks needed for this command
        self.ticks = math.ceil(time * constants.FRAMES)
        self.total_ticks = self.ticks

    def tick(self) -> None:
        """Decrement the tick counter by one."""
        self.ticks -= 1

    @abstractmethod
    def process_one_tick(self, robot: Any) -> None:
        """
        Process one frame tick of this command.

        Args:
            robot: The robot object to apply the command to

        Note:
            Implementing methods must call tick() to decrement the counter.
        """
        pass

    @abstractmethod
    def apply_on_pos(self, curr_pos: Any) -> 'Command':
        """
        Apply this command's effects to a position object.

        Args:
            curr_pos: Current position object to modify

        Returns:
            Self for method chaining
        """
        pass

    @abstractmethod
    def convert_to_message(self) -> Any:
        """
        Convert this command to a message format for transmission.

        Returns:
            Message object suitable for sending over RPi communication
        """
        pass