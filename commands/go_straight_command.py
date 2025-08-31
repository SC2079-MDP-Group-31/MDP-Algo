import constants
from commands.command import Command
from misc.direction import Direction
from misc.positioning import Position


class StraightCommand(Command):
    def __init__(self, dist: float) -> None:
        """
        Initialize a straight movement command.

        Args:
            dist: Distance to travel (already scaled, do not divide by scaling factor)
        """
        # Calculate the time needed to travel the required distance
        time = abs(dist / constants.ROBOT_SPEED_PER_SECOND)
        super().__init__(time)
        self.dist = dist

    def __str__(self) -> str:
        return f"StraightCommand(dist={self.dist}, {self.total_ticks} ticks)"

    __repr__ = __str__

    def process_one_tick(self, robot) -> None:
        """
        Process one simulation tick, moving the robot incrementally.

        Used by AlgoSimulator to update the pygame simulator each time tick.
        """
        if self.total_ticks == 0:
            return

        # Calculate consistent distance per tick based on original values
        original_ticks = abs(self.dist / constants.ROBOT_SPEED_PER_SECOND)
        distance_per_tick = self.dist / original_ticks if original_ticks > 0 else 0

        self.tick()  # Decrement remaining ticks
        robot.straight(distance_per_tick)

    def apply_on_pos(self, curr_pos: Position) -> Position:
        """
        Apply this command to a Position object and return the resulting position.

        Args:
            curr_pos: Current position to modify

        Returns:
            The modified position object
        """
        if curr_pos.direction == Direction.RIGHT:
            curr_pos.x += self.dist
        elif curr_pos.direction == Direction.TOP:
            curr_pos.y += self.dist
        elif curr_pos.direction == Direction.BOTTOM:
            curr_pos.y -= self.dist
        else:  # Direction.LEFT
            curr_pos.x -= self.dist

        return curr_pos

    def convert_to_message(self) -> str:
        """
        Convert command to message format for Raspberry Pi communication.

        Message format:
        - Forward: SFXXX (where XXX is distance in cm, zero-padded if < 100)
        - Backward: SBXXX (where XXX is absolute distance in cm, zero-padded if < 100)
        """
        distance_cm = int(abs(self.dist))
        direction_prefix = "SB" if self.dist < 0 else "SF"

        # Zero-pad distances less than 100
        if distance_cm < 100:
            return f"{direction_prefix}0{distance_cm}"
        else:
            return f"{direction_prefix}{distance_cm}"