import math
from typing import List
import pygame

import constants
from grid.grid_cell import GridCell
from grid.obstacle import Obstacle
from misc.positioning import Position


class GridTwo:
    """A grid-based pathfinding system with obstacles and safety boundaries."""

    def __init__(self, obstacles: List[Obstacle]):
        self.obstacles = obstacles
        self.gridcells = self._generate_grid()

    def _generate_grid(self) -> List[List[GridCell]]:
        """
        Generate the grid cells that make up this grid.

        Creates a 2D grid where each cell represents a GRID_CELL_LENGTH x GRID_CELL_LENGTH area.
        Cells within safety distance of obstacles are marked as occupied.

        Returns:
            2D list of GridCell objects, indexed as grid[row][col]
        """
        rows_count = constants.TASK2_LENGTH // constants.GRID_CELL_LENGTH
        cols_count = constants.TASK2_WIDTH // constants.GRID_CELL_LENGTH

        grid = []
        for row_idx in range(rows_count):
            row = []
            for col_idx in range(cols_count):
                x = constants.GRID_CELL_LENGTH * col_idx
                y = constants.GRID_CELL_LENGTH * row_idx
                position = Position(x, y)
                is_occupied = not self._is_valid_position(position)

                cell = GridCell(position, is_occupied)
                row.append(cell)

            # Insert at beginning to maintain coordinate system (bottom-up)
            grid.insert(0, row)

        return grid

    def get_grid_cell_at_coordinate(self, x: float, y: float) -> GridCell:
        """
        Get the GridCell that contains the specified coordinates.

        Args:
            x: X coordinate in grid space
            y: Y coordinate in grid space

        Returns:
            GridCell at the specified coordinates, or None if out of bounds
        """
        col = math.floor(x / constants.GRID_CELL_LENGTH)
        row = (constants.TASK2_WIDTH // constants.GRID_CELL_LENGTH -
               math.floor(y / constants.GRID_CELL_LENGTH) - 1)

        if (0 <= row < len(self.gridcells) and
                0 <= col < len(self.gridcells[0])):
            return self.gridcells[row][col]

        return None

    def copy(self) -> 'GridTwo':
        """Create a deep copy of the grid."""
        new_grid = GridTwo(self.obstacles)
        new_grid.gridcells = [
            [cell.copy() for cell in row]
            for row in self.gridcells
        ]
        return new_grid

    def _is_valid_position(self, position: Position) -> bool:
        """
        Check if a position is valid (not in obstacle and within bounds).

        Args:
            position: Position to check

        Returns:
            True if position is valid, False otherwise
        """
        # Check if position is inside any obstacle
        if any(obstacle.check_within_boundary(position) for obstacle in self.obstacles):
            return False

        # Check if position is too close to borders
        # Allow some buffer from the edge equal to GRID_CELL_LENGTH
        if (position.y < constants.GRID_CELL_LENGTH or
                position.y >= constants.GRID_LENGTH - constants.GRID_CELL_LENGTH or
                position.x < constants.GRID_CELL_LENGTH or
                position.x >= constants.GRID_LENGTH - constants.GRID_CELL_LENGTH):
            return False

        return True

    @staticmethod
    def draw_arena_borders(screen):
        """Draw the arena borders and grid lines."""
        # Draw grid lines (thicker every 5th line)
        cells_per_side = constants.TASK2_LENGTH // constants.GRID_CELL_LENGTH

        for i in range(1, cells_per_side):
            line_thickness = 2 if i % 5 == 0 else 1
            color = constants.DARK_GRAY if i % 5 == 0 else constants.LIGHT_GRAY

            y_pos = i * constants.GRID_CELL_LENGTH
            x_pos = i * constants.GRID_CELL_LENGTH

            # Horizontal lines
            pygame.draw.line(screen, color, (0, y_pos), (constants.GRID_LENGTH, y_pos), line_thickness)
            # Vertical lines
            pygame.draw.line(screen, color, (x_pos, 0), (x_pos, constants.GRID_LENGTH), line_thickness)

        # Draw border lines
        border_points = [
            ((0, 0), (constants.GRID_LENGTH, 0)),  # Top
            ((0, constants.GRID_LENGTH), (constants.GRID_LENGTH, constants.GRID_LENGTH)),  # Bottom
            ((0, 0), (0, constants.GRID_LENGTH)),  # Left
            ((constants.GRID_LENGTH, 0), (constants.GRID_LENGTH, constants.GRID_LENGTH))  # Right
        ]

        for start_pos, end_pos in border_points:
            pygame.draw.line(screen, constants.RED, start_pos, end_pos, 2)

        # Draw grid coordinate labels
        font = pygame.freetype.SysFont(None, 18)
        font.origin = True

        # X-axis labels
        for i in range(constants.NO_OF_GRID_CELLS_PER_SIDE):
            x_pos = i * constants.GRID_CELL_LENGTH + 8
            y_pos = constants.GRID_LENGTH + 25
            font.render_to(screen, (x_pos, y_pos), f"{i}", pygame.Color("DarkBlue"))

        # Y-axis labels
        for j in range(constants.NO_OF_GRID_CELLS_PER_SIDE):
            x_pos = constants.GRID_LENGTH + 10
            y_pos = constants.GRID_LENGTH - j * constants.GRID_CELL_LENGTH - 8
            font.render_to(screen, (x_pos, y_pos), f"{j}", pygame.Color("DarkBlue"))

    def draw_obstacles(self, screen):
        """Draw all obstacles on the screen."""
        for obstacle in self.obstacles:
            obstacle.draw(screen)

    def draw_grid_cells(self, screen):
        """Draw all grid cells on the screen."""
        for row in self.gridcells:
            for cell in row:
                cell.draw(screen)

    def draw(self, screen):
        """Draw the complete grid including cells, borders, and obstacles."""
        self.draw_grid_cells(screen)
        self.draw_arena_borders(screen)
        self.draw_obstacles(screen)