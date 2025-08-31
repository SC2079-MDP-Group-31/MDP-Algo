import pygame
from typing import List, Tuple

import constants
from misc.direction import Direction
from misc.positioning import Position, RobotPosition


class Obstacle:
    """
    Represents an obstacle in the robot navigation system.

    Each obstacle has a position, direction, and defines safety boundaries
    and target positions for robot navigation.
    """

    def __init__(self, position: Position, index: int):
        """
        Initialize an obstacle.

        Args:
            position: The center position of the obstacle
            index: Unique identifier for this obstacle

        Raises:
            AssertionError: If obstacle coordinates are not valid grid positions
        """
        self._validate_position(position)

        self.position = position
        self.index = index
        self.target_position = self._calculate_robot_target_position()

    def _validate_position(self, position: Position) -> None:
        """Validate that obstacle coordinates are centered in grid cells."""
        if position.x % 10 != 0 or position.y % 10 != 0:
            raise AssertionError("Obstacle center coordinates must be multiples of 10!")

    def __str__(self) -> str:
        return str(self.position)

    __repr__ = __str__

    def check_within_boundary(self, position: Position, collision_mode: int) -> bool:
        """
        Check if a position is within the safety boundary of this obstacle.

        Args:
            position: Position to check
            collision_mode: 1 for cross pattern, 2 for single cell, 0 for full 3x3

        Returns:
            True if position is within the safety boundary
        """
        check_positions = self._get_positions_to_check(position, collision_mode)

        for check_pos in check_positions:
            if self._is_position_in_safety_zone(check_pos):
                return True

        return False

    def _get_positions_to_check(self, position: Position, collision_mode: int) -> List[Tuple[int, int]]:
        """Get list of positions to check based on collision mode."""
        base_positions = [
            (position.x - constants.GRID_CELL_LENGTH, position.y - constants.GRID_CELL_LENGTH),
            (position.x - constants.GRID_CELL_LENGTH, position.y),
            (position.x - constants.GRID_CELL_LENGTH, position.y + constants.GRID_CELL_LENGTH),
            (position.x, position.y - constants.GRID_CELL_LENGTH),
            (position.x, position.y),
            (position.x, position.y + constants.GRID_CELL_LENGTH),
            (position.x + constants.GRID_CELL_LENGTH, position.y - constants.GRID_CELL_LENGTH),
            (position.x + constants.GRID_CELL_LENGTH, position.y),
            (position.x + constants.GRID_CELL_LENGTH, position.y + constants.GRID_CELL_LENGTH)
        ]

        if collision_mode == 1:  # Cross pattern
            return [(x, y) for x, y in base_positions if position.x == x or position.y == y]
        elif collision_mode == 2:  # Single cell
            return [(position.x, position.y)]
        else:  # Full 3x3 grid
            return base_positions

    def _is_position_in_safety_zone(self, check_position: Tuple[int, int]) -> bool:
        """Check if a single position is within the obstacle's safety zone."""
        x, y = check_position
        diff_x = abs(self.position.x - x)
        diff_y = abs(self.position.y - y)

        return (diff_y < constants.OBSTACLE_SAFETY_WIDTH + 1 and
                diff_x < constants.OBSTACLE_SAFETY_WIDTH + 1)

    def get_boundary_points(self) -> List[Position]:
        """
        Get the corner points of the obstacle's safety boundary.

        Returns:
            List of Position objects representing the four corners
        """
        half_width = constants.OBSTACLE_SAFETY_WIDTH

        return [
            Position(self.position.x - half_width, self.position.y - half_width),  # Bottom left
            Position(self.position.x + half_width, self.position.y - half_width),  # Bottom right
            Position(self.position.x - half_width, self.position.y + half_width),  # Top left
            Position(self.position.x + half_width, self.position.y + half_width),  # Top right
        ]

    def _calculate_robot_target_position(self) -> RobotPosition:
        """Calculate the target position for the robot to approach this obstacle."""
        corner_type = self._get_corner_type()
        edge_type = self._get_edge_type() if corner_type is None else None

        if corner_type:
            return self._get_corner_target_position(corner_type)
        elif edge_type:
            return self._get_edge_target_position(edge_type)
        else:
            return self._get_standard_target_position()

    def _get_corner_type(self) -> str:
        """Determine if obstacle is at a corner and return corner type."""
        corners = {
            (0, 0): "bottom_left",
            (0, 190): "top_left",
            (190, 190): "top_right",
            (190, 0): "bottom_right"
        }
        return corners.get((self.position.x, self.position.y))

    def _get_edge_type(self) -> str:
        """Determine if obstacle is at an edge and return edge type."""
        if self.position.y == 0:
            return "bottom"
        elif self.position.y == 190:
            return "top"
        elif self.position.x == 0:
            return "left"
        elif self.position.x == 190:
            return "right"
        return None

    def _get_corner_target_position(self, corner_type: str) -> RobotPosition:
        """Get target position for corner obstacles."""
        offset = constants.OBSTACLE_SAFETY_OFFSET + constants.OBSTACLE_LENGTH

        corner_adjustments = {
            "bottom_left": {"TOP": (10, 0), "RIGHT": (0, 10)},
            "top_left": {"BOTTOM": (10, 0), "RIGHT": (0, -10)},
            "top_right": {"BOTTOM": (-10, 0), "LEFT": (0, -10)},
            "bottom_right": {"TOP": (-10, 0), "LEFT": (0, 10)}
        }

        direction = self.position.direction.name
        base_target = self._get_standard_target_position()

        if corner_type in corner_adjustments and direction in corner_adjustments[corner_type]:
            x_adj, y_adj = corner_adjustments[corner_type][direction]
            return RobotPosition(
                base_target.x + x_adj,
                base_target.y + y_adj,
                base_target.direction
            )

        return base_target

    def _get_edge_target_position(self, edge_type: str) -> RobotPosition:
        """Get target position for edge obstacles."""
        offset = constants.OBSTACLE_SAFETY_OFFSET + constants.OBSTACLE_LENGTH

        edge_adjustments = {
            "bottom": {"LEFT": (0, 10), "RIGHT": (0, 10)},
            "top": {"LEFT": (0, -10), "RIGHT": (0, -10)},
            "left": {"TOP": (10, 0), "BOTTOM": (10, 0)},
            "right": {"TOP": (-10, 0), "BOTTOM": (-10, 0)}
        }

        direction = self.position.direction.name
        base_target = self._get_standard_target_position()

        if edge_type in edge_adjustments and direction in edge_adjustments[edge_type]:
            x_adj, y_adj = edge_adjustments[edge_type][direction]
            return RobotPosition(
                base_target.x + x_adj,
                base_target.y + y_adj,
                base_target.direction
            )

        return base_target

    def _get_standard_target_position(self) -> RobotPosition:
        """Get standard target position based on obstacle direction."""
        offset = constants.OBSTACLE_SAFETY_OFFSET + constants.OBSTACLE_LENGTH

        direction_targets = {
            Direction.TOP: (self.position.x, self.position.y + offset, Direction.BOTTOM),
            Direction.BOTTOM: (self.position.x, self.position.y - offset, Direction.TOP),
            Direction.LEFT: (self.position.x - offset, self.position.y, Direction.RIGHT),
            Direction.RIGHT: (self.position.x + offset, self.position.y, Direction.LEFT)
        }

        x, y, robot_direction = direction_targets[self.position.direction]
        return RobotPosition(x, y, robot_direction)

    def draw_obstacles(self, screen: pygame.Surface) -> None:
        """Draw the obstacle and its direction indicator."""
        # Draw main obstacle
        obstacle_rect = pygame.Rect(0, 0, constants.OBSTACLE_LENGTH, constants.OBSTACLE_LENGTH)
        obstacle_rect.center = self.position.xy_pygame()
        pygame.draw.rect(screen, constants.RED, obstacle_rect)

        # Draw direction indicator
        self._draw_direction_indicator(screen)

    def _draw_direction_indicator(self, screen: pygame.Surface) -> None:
        """Draw the direction indicator on the obstacle."""
        indicator_size = constants.OBSTACLE_LENGTH // 2
        indicator_rect = pygame.Rect(0, 0, indicator_size, indicator_size)
        indicator_rect.center = self.position.xy_pygame()

        # Adjust position based on direction
        quarter_length = constants.OBSTACLE_LENGTH // 4
        direction_offsets = {
            Direction.TOP: (0, -quarter_length),
            Direction.BOTTOM: (0, quarter_length),
            Direction.LEFT: (-quarter_length, 0),
            Direction.RIGHT: (quarter_length, 0)
        }

        if self.position.direction in direction_offsets:
            x_offset, y_offset = direction_offsets[self.position.direction]
            indicator_rect.centerx += x_offset
            indicator_rect.centery += y_offset

        pygame.draw.rect(screen, constants.DARK_BLUE, indicator_rect)

    def draw_virtual_boundary(self, screen: pygame.Surface) -> None:
        """Draw the safety boundary around the obstacle."""
        points = self.get_boundary_points()
        pygame_points = [point.xy_pygame() for point in points]

        # Draw boundary lines
        boundary_lines = [
            (pygame_points[0], pygame_points[2]),  # Left border
            (pygame_points[1], pygame_points[3]),  # Right border
            (pygame_points[2], pygame_points[3]),  # Top border
            (pygame_points[0], pygame_points[1])  # Bottom border
        ]

        for start, end in boundary_lines:
            pygame.draw.line(screen, constants.RED, start, end)

    def draw_robot_target(self, screen: pygame.Surface) -> None:
        """Draw the target position indicator for the robot."""
        # Note: This method assumes target_image is defined elsewhere
        # You may need to initialize self.target_image in __init__
        if not hasattr(self, 'target_image'):
            return

        target = self.target_position

        # Calculate rotation angle
        rotation_angles = {
            Direction.BOTTOM: 180,
            Direction.LEFT: 90,
            Direction.RIGHT: -90,
            Direction.TOP: 0
        }

        angle = rotation_angles.get(target.direction, 0)
        rotated_image = pygame.transform.rotate(self.target_image, angle)

        # Draw at target position
        rect = rotated_image.get_rect()
        rect.center = target.xy_pygame()
        screen.blit(rotated_image, rect)

    def draw(self, screen: pygame.Surface) -> None:
        """Draw the complete obstacle with all visual elements."""
        self.draw_obstacles(screen)
        self.draw_virtual_boundary(screen)
        self.draw_robot_target(screen)