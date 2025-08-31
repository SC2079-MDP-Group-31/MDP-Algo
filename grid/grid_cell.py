import constants
from misc.positioning import Position
from typing import Optional


class GridCell:
    """Represents a cell in a grid with position and occupancy status."""

    def __init__(self, position: Position, occupied: bool) -> None:
        self.position = position
        self.occupied = occupied

    def __str__(self) -> str:
        return f"Cell({self.position})"

    def __repr__(self) -> str:
        return f"GridCell(position={self.position!r}, occupied={self.occupied})"

    def __eq__(self, other) -> bool:
        if not isinstance(other, GridCell):
            return False
        return (
                self.position == other.position
                and self.occupied == other.occupied
        )

    def __hash__(self) -> int:
        return hash((self.position.xy_dir(), self.occupied))

    def copy(self) -> 'GridCell':
        """Return a deep copy of this grid cell."""
        return GridCell(
            position=self.position.copy() if hasattr(self.position, 'copy')
            else Position(self.position.x, self.position.y, self.position.direction),
            occupied=self.occupied
        )