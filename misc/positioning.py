import constants

from .direction import Direction
from typing import Optional, Tuple


class Position:
    def __init__(self, x: float, y: float, direction: Optional[Direction] = None):
        """
        x and y coordinates are in terms of the coordinates
        Note that they should already be scaled properly.

        Most of the time, we do not need to set direction. Should only be used for the robot.
        """
        self.x = x
        self.y = y
        self.direction = direction

    def __str__(self) -> str:
        return f"({self.x}, {self.y}, {self.direction})"

    __repr__ = __str__

    def xy(self) -> Tuple[float, float]:
        """
        Return the x, y coordinates of the current Position.
        """
        return self.x, self.y

    def xy_dir(self) -> Tuple[float, float, Optional[Direction]]:
        """
        Return the x, y coordinates and direction of the current Position.
        """
        return self.x, self.y, self.direction

    def get_dir(self) -> Optional[Direction]:
        return self.direction

    def xy_pygame(self) -> Tuple[float, float]:
        """
        Return the x, y coordinates in terms of Pygame coordinates. Useful for drawing on screen.
        """
        return self.x, constants.GRID_LENGTH - self.y

    def copy(self) -> 'Position':
        """
        Create a new copy of this Position.
        """
        return Position(self.x, self.y, self.direction)


class RobotPosition(Position):
    def __init__(self, x: float, y: float, direction: Optional[Direction] = None, angle: Optional[float] = None):
        super().__init__(x, y, direction)

        # Set angle based on provided angle or direction
        if angle is not None:
            self.angle = angle
        elif direction is not None:
            self.angle = direction.value
        else:
            self.angle = None

    def __str__(self) -> str:
        return f"RobotPosition({super().__str__()}, angle={self.angle})"

    __repr__ = __str__

    def copy(self) -> 'RobotPosition':
        return RobotPosition(self.x, self.y, self.direction, self.angle)