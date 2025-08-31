import math
from collections import deque
from typing import List, Optional

import pygame

import constants
from grid.grid_cell import GridCell
from grid.obstacle import Obstacle
from misc.positioning import Position


class Grid:
    """
    Represents a grid system for pathfinding and obstacle avoidance.

    The grid is composed of cells that can be either occupied (blocked by obstacles)
    or free. Each cell has a fixed size defined by GRID_CELL_LENGTH.
    """

    def __init__(self, obstacles: List[Obstacle]):
        """
        Initialize the grid with obstacles.

        Args:
            obstacles: List of Obstacle objects to place in the grid
        """
        self.obstacles = obstacles
        self.gridcells = self._generate_grid(
            constants.NO_OF_GRID_CELLS_PER_SIDE,
            constants.NO_OF_GRID_CELLS_PER_SIDE
        )
        self.gridcells2 = self._generate_grid(
            constants.TASK2_LENGTH // constants.GRID_CELL_LENGTH,
            constants.TASK2_WIDTH // constants.GRID_CELL_LENGTH
        )

    def _generate_grid(self, rows: int, cols: int) -> deque:
        """
        Generate grid cells for the specified dimensions.

        Cells that fall within the safety distance of obstacles are marked as occupied.
        The grid uses a coordinate system where grid[0] refers to the top row.

        Args:
            rows: Number of rows in the grid
            cols: Number of columns in the grid

        Returns:
            deque: 2D grid structure containing GridCell objects
        """
        grid = deque()

        for i in range(rows):
            row = deque()
            for j in range(cols):
                x = constants.GRID_CELL_LENGTH * j
                y = constants.GRID_CELL_LENGTH * i
                position = Position(x, y)
                is_occupied = not self._is_valid_position(position)

                cell = GridCell(position, is_occupied)
                row.append(cell)

            # Insert at the beginning to maintain coordinate system
            # where grid[0] refers to the last row from bottom
            grid.appendleft(row)

        return grid

    def get_cell_at_coordinate(self, x: float, y: float) -> Optional[GridCell]:
        """
        Get the GridCell at the specified coordinates.

        Args:
            x: X coordinate in grid units
            y: Y coordinate in grid units

        Returns:
            GridCell at the specified coordinates, or None if out of bounds
        """
        col = math.floor(x / constants.GRID_CELL_LENGTH)
        row = (
                constants.NO_OF_GRID_CELLS_PER_SIDE
                - math.floor(y / constants.GRID_CELL_LENGTH)
                - 1
        )

        try:
            return self.gridcells[row][col]
        except IndexError:
            return None

    def copy(self) -> 'Grid':
        """
        Create a deep copy of the grid.

        Returns:
            Grid: A new Grid instance with copied cells
        """
        new_grid = Grid(self.obstacles)
        new_grid.gridcells = self._deep_copy_cells(self.gridcells)
        new_grid.gridcells2 = self._deep_copy_cells(self.gridcells2)
        return new_grid

    def _deep_copy_cells(self, cells: deque) -> List[List[GridCell]]:
        """
        Create a deep copy of the cell structure.

        Args:
            cells: Original cell structure to copy

        Returns:
            List of lists containing copied GridCell objects
        """
        copied_cells = []
        for row in cells:
            new_row = [cell.copy() for cell in row]
            copied_cells.append(new_row)
        return copied_cells

    def is_adjacent_to_obstacle(self, x: int, y: int, min_separation: int) -> bool:
        """
        Check if a position is too close to any obstacle.

        Args:
            x: X coordinate to check
            y: Y coordinate to check
            min_separation: Minimum required separation distance

        Returns:
            bool: True if position is too close to an obstacle
        """
        return any(
            self._is_too_close_to_obstacle(obstacle, x, y, min_separation)
            for obstacle in self.obstacles
        )

    def _is_too_close_to_obstacle(self, obstacle: Obstacle, x: int, y: int,
                                  min_separation: int) -> bool:
        """
        Check if a position is too close to a specific obstacle.

        Args:
            obstacle: Obstacle to check against
            x: X coordinate
            y: Y coordinate
            min_separation: Minimum required separation

        Returns:
            bool: True if too close to the obstacle
        """
        return (
                (obstacle.position.x == x and
                 abs(obstacle.position.y - y) < min_separation + 1) or
                (obstacle.position.y == y and
                 abs(obstacle.position.x - x) < min_separation + 1)
        )

    def _is_valid_position(self, position: Position, ignore_obstacles: bool = False) -> bool:
        """
        Check if a position is valid (not blocked by obstacles or boundaries).

        Args:
            position: Position to check
            ignore_obstacles: If True, only check boundaries, not obstacles

        Returns:
            bool: True if position is valid
        """
        # Check obstacle collision
        if not ignore_obstacles and self._is_position_in_obstacle(position):
            return False

        # Check boundary constraints
        return self._is_within_boundaries(position)

    def _is_position_in_obstacle(self, position: Position) -> bool:
        """Check if position intersects with any obstacle."""
        return any(
            obstacle.check_within_boundary(position, False)
            for obstacle in self.obstacles
        )

    def _is_within_boundaries(self, position: Position) -> bool:
        """Check if position is within grid boundaries."""
        min_boundary = constants.GRID_CELL_LENGTH
        max_boundary = constants.GRID_LENGTH - constants.GRID_CELL_LENGTH

        return (
                min_boundary <= position.x < max_boundary and
                min_boundary <= position.y < max_boundary
        )

    # Drawing methods
    def draw(self, screen) -> None:
        """
        Draw the complete grid including nodes, borders, and obstacles.

        Args:
            screen: Pygame screen surface to draw on
        """
        self._draw_nodes(screen)
        self._draw_arena_borders(screen)
        self._draw_obstacles(screen)

    def _draw_nodes(self, screen) -> None:
        """Draw all grid cells."""
        for row in self.gridcells:
            for cell in row:
                cell.draw(screen)

    def _draw_obstacles(self, screen) -> None:
        """Draw all obstacles."""
        for obstacle in self.obstacles:
            obstacle.draw(screen)

    @staticmethod
    def _draw_arena_borders(screen) -> None:
        """
        Draw the arena borders and grid lines.

        Args:
            screen: Pygame screen surface to draw on
        """
        Grid._draw_grid_lines(screen)
        Grid._draw_boundary_lines(screen)
        Grid._draw_grid_labels(screen)

    @staticmethod
    def _draw_grid_lines(screen) -> None:
        """Draw internal grid lines."""
        for i in range(1, constants.NO_OF_GRID_CELLS_PER_SIDE):
            if i % 5 == 0:  # Draw thicker lines every 5 cells
                y_pos = i * constants.GRID_CELL_LENGTH
                x_pos = i * constants.GRID_CELL_LENGTH

                # Horizontal line
                pygame.draw.line(
                    screen, constants.DARK_GRAY,
                    (0, y_pos), (constants.GRID_LENGTH, y_pos)
                )

                # Vertical line
                pygame.draw.line(
                    screen, constants.DARK_GRAY,
                    (x_pos, 0), (x_pos, constants.GRID_LENGTH)
                )

    @staticmethod
    def _draw_boundary_lines(screen) -> None:
        """Draw the outer boundary of the arena."""
        grid_length = constants.GRID_LENGTH

        # Draw all four borders
        border_lines = [
            ((0, 0), (grid_length, 0)),  # Top
            ((0, grid_length), (grid_length, grid_length)),  # Bottom
            ((0, 0), (0, grid_length)),  # Left
            ((grid_length, 0), (grid_length, grid_length))  # Right
        ]

        for start_pos, end_pos in border_lines:
            pygame.draw.line(screen, constants.RED, start_pos, end_pos)

    @staticmethod
    def _draw_grid_labels(screen) -> None:
        """Draw coordinate labels on the grid."""
        font = pygame.freetype.SysFont(None, 18)
        font.origin = True

        # Draw column numbers (bottom)
        for i in range(constants.NO_OF_GRID_CELLS_PER_SIDE):
            x_pos = i * constants.GRID_CELL_LENGTH + 8
            y_pos = constants.GRID_LENGTH + 25
            font.render_to(screen, (x_pos, y_pos), f"{i}", pygame.Color("DarkBlue"))

        # Draw row numbers (right side)
        for j in range(constants.NO_OF_GRID_CELLS_PER_SIDE):
            x_pos = constants.GRID_LENGTH + 10
            y_pos = constants.GRID_LENGTH - j * constants.GRID_CELL_LENGTH - 8
            font.render_to(screen, (x_pos, y_pos), f"{j}", pygame.Color("DarkBlue"))

    # Public API methods for backwards compatibility
    def check_valid_position(self, position: Position, yolo: bool = False) -> bool:
        """
        Legacy method for checking position validity.

        Args:
            position: Position to check
            yolo: Renamed to ignore_obstacles for clarity

        Returns:
            bool: True if position is valid
        """
        return self._is_valid_position(position, ignore_obstacles=yolo)

    def get_grid_cell_corresponding_to_coordinate(self, x: float, y: float) -> Optional[GridCell]:
        """Legacy method name - use get_cell_at_coordinate instead."""
        return self.get_cell_at_coordinate(x, y)

    def is_adjacent_to_any_obstacle(self, x: int, y: int, min_separation: int) -> bool:
        """Legacy method name - use is_adjacent_to_obstacle instead."""
        return self.is_adjacent_to_obstacle(x, y, min_separation)

    def draw_arena_borders(self, screen) -> None:
        """Legacy method - use _draw_arena_borders instead."""
        self._draw_arena_borders(screen)

    def draw_obstacles(self, screen) -> None:
        """Legacy method - use _draw_obstacles instead."""
        self._draw_obstacles(screen)

    def draw_nodes(self, screen) -> None:
        """Legacy method - use _draw_nodes instead."""
        self._draw_nodes(screen)