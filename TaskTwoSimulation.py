import sys
from copy import deepcopy
import pygame
import constants
from misc.direction import Direction


class Simulation:
    """Robot simulation using pygame for visualization and movement."""

    def __init__(self, direction):
        """Initialize the simulation with pygame and basic settings."""
        pygame.init()
        self.running = True
        self.direction = direction
        self.font = pygame.font.SysFont("Arial", 25)
        self.screen = pygame.display.set_mode((900, 700), pygame.RESIZABLE)
        self.clock = None
        self.bot = None
        self.obstacles = []
        self.currentPos = (0, 0, Direction.TOP)

        # Add hover effect state management
        self.hovered_button = None
        self.last_mouse_pos = (0, 0)
        self.hover_animation_time = 0
        self.last_click_time = 0
        self.click_delay = 300  # Minimum delay between clicks (ms)

        pygame.mouse.set_visible(1)
        pygame.display.set_caption("Vroom Vroom Simulation - Enhanced")
        self.screen.fill(constants.BLACK)

    def reset(self, bot):
        """Reset the simulation to initial state."""
        print("Resetting Task 2 simulation...")
        self.screen.fill(constants.BLACK)

        # Set robot to proper starting position (bottom-left area of Task 2 grid)
        # Task 2 grid is 400x150, so 40x15 cells - start near bottom-left
        start_world_x = 370  # World units from left
        start_world_y = 70  # World units from bottom
        start_direction = Direction.TOP

        print(f"Resetting robot to world position: ({start_world_x}, {start_world_y})")

        # Convert to display coordinates for current position tracking
        start_grid_x = start_world_x // 10  # Convert to grid cells (37)
        start_grid_y = start_world_y // 10  # Convert to grid cells (7)

        print(f"Resetting robot to grid position: ({start_grid_x}, {start_grid_y})")

        # Set the display position
        self.currentPos = (start_grid_x, start_grid_y, start_direction)

        # Set the bot's actual position using Task 2 method
        self.bot.set_position_task2(start_grid_x, start_grid_y, start_direction)

        # Clear any existing commands
        if hasattr(self.bot, 'hamiltonian') and hasattr(self.bot.hamiltonian, 'commands'):
            self.bot.hamiltonian.commands.clear()
            print("Cleared command queue")

        print(f"Task 2 reset complete - Position: {self.currentPos}")

    def _get_hover_color(self, base_color, hover_intensity=0.3):
        """Generate a lighter version of a color for hover effects"""
        return tuple(min(255, int(c + (255 - c) * hover_intensity)) for c in base_color)

    def _draw_glow_effect(self, rect, color, intensity=2):
        """Create a glowing border effect around a rectangle"""
        for i in range(intensity):
            glow_rect = pygame.Rect(rect.x - i * 2, rect.y - i * 2,
                                    rect.width + i * 4, rect.height + i * 4)
            pygame.draw.rect(self.screen, color, glow_rect, max(1, 2 - i))

    def _check_button_hover(self, mouse_x, mouse_y):
        """Check which button is being hovered over"""
        button_width = constants.BUTTON_LENGTH
        button_height = constants.BUTTON_WIDTH
        button_x = 650

        # Define button areas
        buttons = [
            ("start", button_x, 500),
            ("reset", button_x, 450),
            ("coordinates", button_x, 550)
        ]

        for button_name, x, y in buttons:
            if (x <= mouse_x <= x + button_width and y <= mouse_y <= y + button_height):
                return button_name

        return None

    def _draw_cell(self, x, y, cell_size, color, border_width=2):
        """Draw a single cell at the specified grid position."""
        rect = pygame.Rect(y * cell_size, x * cell_size, cell_size, cell_size)
        self.screen.fill(color, rect)
        pygame.draw.rect(self.screen, color, rect, border_width)

    def _draw_direction_indicator(self, robot_pos, cell_size, direction_color):
        """Draw direction indicator on the robot."""
        direction_indicators = {
            Direction.TOP: pygame.Rect(
                robot_pos[1] * cell_size, robot_pos[0] * cell_size, cell_size, 5
            ),
            Direction.RIGHT: pygame.Rect(
                (robot_pos[1] * cell_size) + cell_size - 5, robot_pos[0] * cell_size, 5, cell_size
            ),
            Direction.BOTTOM: pygame.Rect(
                robot_pos[1] * cell_size, (robot_pos[0] * cell_size) + cell_size - 5, cell_size, 5
            ),
            Direction.LEFT: pygame.Rect(
                robot_pos[1] * cell_size, robot_pos[0] * cell_size, 5, cell_size
            ),
        }

        indicator = direction_indicators.get(robot_pos[2])
        if indicator:
            self.screen.fill(direction_color, indicator)
            pygame.draw.rect(self.screen, direction_color, indicator, 5)

    def drawRobot(self, robot_pos, cell_size, direction_color, bot_color, bot_area_color):
        """Draw the robot and its surrounding area."""
        # Draw the 3x3 robot area
        for x in range(robot_pos[0] - 1, robot_pos[0] + 2):
            for y in range(robot_pos[1] - 1, robot_pos[1] + 2):
                if self._is_within_bounds(x, y, cell_size):
                    if robot_pos[0] == x and robot_pos[1] == y:
                        # Draw robot center
                        self._draw_cell(robot_pos[0], robot_pos[1], cell_size, bot_color)
                        self._draw_direction_indicator(robot_pos, cell_size, direction_color)
                    else:
                        # Draw robot area
                        self._draw_cell(x, y, cell_size, bot_area_color, 1)

    def _is_within_bounds(self, x, y, cell_size):
        """Check if coordinates are within simulation bounds."""
        return (0 <= x * cell_size < constants.TASK2_LENGTH * constants.TASK2_SCALING_FACTOR and
                0 <= y * cell_size < constants.TASK2_WIDTH * constants.TASK2_SCALING_FACTOR)

    def drawGrid2(self, bot):
        """Draw the simulation grid."""
        cell_size = constants.GRID_CELL_LENGTH * constants.TASK2_SCALING_FACTOR

        for x in range(0, constants.TASK2_LENGTH * constants.TASK2_SCALING_FACTOR, cell_size):
            for y in range(0, constants.TASK2_WIDTH * constants.TASK2_SCALING_FACTOR, cell_size):
                rect = pygame.Rect(y, x, cell_size, cell_size)
                pygame.draw.rect(self.screen, constants.WHITE, rect, 2)

    def drawEnhancedButtons(self, x_pos, y_pos, bg_color, text, text_color, length, width,
                            is_hovered=False, button_type="normal"):
        """Draw UI buttons with hover effects."""
        # Determine button appearance based on hover state
        if is_hovered:
            # Enhanced hover colors
            if button_type == "start":
                hover_bg = self._get_hover_color(bg_color, 0.4)
                border_color = constants.WHITE
            elif button_type == "reset":
                hover_bg = self._get_hover_color(bg_color, 0.3)
                border_color = constants.WHITE
            else:
                hover_bg = self._get_hover_color(bg_color, 0.2)
                border_color = constants.YELLOW
        else:
            hover_bg = bg_color
            border_color = constants.BLACK

        button_rect = pygame.Rect(x_pos, y_pos, length, width)

        # Add glow effect for hovered buttons
        if is_hovered:
            self._draw_glow_effect(button_rect, hover_bg)

        # Draw main button
        pygame.draw.rect(self.screen, hover_bg, button_rect)

        # Enhanced border
        border_width = 4 if is_hovered else 2
        pygame.draw.rect(self.screen, border_color, button_rect, border_width)

        # Add subtle shadow effect
        if is_hovered:
            shadow_rect = pygame.Rect(x_pos + 2, y_pos + 2, length, width)
            pygame.draw.rect(self.screen, (50, 50, 50), shadow_rect, 1)

        # Enhanced text rendering
        font_to_use = self.font
        if is_hovered and button_type in ["start", "reset"]:
            # Make text slightly larger on hover for interactive buttons
            font_to_use = pygame.font.SysFont("Arial", 27)

        text_surface = font_to_use.render(text, True, text_color)
        text_rect = text_surface.get_rect(
            center=(x_pos + (length // 2), y_pos + (width // 2))
        )

        # Add text shadow for better readability on hover
        if is_hovered:
            shadow_surface = font_to_use.render(text, True, (0, 0, 0))
            shadow_rect = text_rect.copy()
            shadow_rect.x += 1
            shadow_rect.y += 1
            self.screen.blit(shadow_surface, shadow_rect)

        self.screen.blit(text_surface, text_rect)

    def _draw_wall_section(self, x, y, x_length, y_length, size, color):
        """Draw a wall section."""
        wall_rect = pygame.Rect(x * size, (y * size) + size, x_length * size, y_length * size)
        self.screen.fill(color, wall_rect)
        pygame.draw.rect(self.screen, color, wall_rect, 1)

    def drawObstacles(self, obstacles, color):
        """Draw obstacles and walls on the grid."""
        if not obstacles:
            return

        size = constants.GRID_CELL_LENGTH * constants.TASK2_SCALING_FACTOR

        # Draw obstacles
        for i, obstacle in enumerate(obstacles[:2]):  # Only handle first 2 obstacles
            y = (constants.TASK2_LENGTH - (
                    constants.GRID_CELL_LENGTH * 5 + obstacle.position.y)) // constants.GRID_CELL_LENGTH
            x = obstacle.position.x // constants.GRID_CELL_LENGTH

            self._draw_cell(y, x, size, constants.YELLOW)

            # Add obstacle indicator
            indicator_rect = pygame.Rect(x * size, (y * size) + size - 5, size, 5)
            self.screen.fill(color, indicator_rect)
            pygame.draw.rect(self.screen, color, indicator_rect, 5)

        # Draw walls (if obstacles exist)
        if len(obstacles) >= 2:
            obstacle = obstacles[0]  # Use first obstacle for wall positioning
            y = (constants.TASK2_LENGTH - (
                    constants.GRID_CELL_LENGTH * 5 + obstacle.position.y)) // constants.GRID_CELL_LENGTH
            x = obstacle.position.x // constants.GRID_CELL_LENGTH

            # Draw various wall sections
            wall_configs = [
                (x - 2.5, y - 1, 2.5, 1),
                (x + 1, y - 1, 2.5, 1),
                (5, (constants.TASK2_LENGTH - 5 * constants.GRID_CELL_LENGTH) // 10, 1, 4),
                (9, (constants.TASK2_LENGTH - 5 * constants.GRID_CELL_LENGTH) // 10, 1, 4),
                (5, (constants.TASK2_LENGTH - 2 * constants.GRID_CELL_LENGTH) // 10, 5, 1),
            ]

            for wall_x, wall_y, wall_w, wall_h in wall_configs:
                self._draw_wall_section(wall_x, wall_y, wall_w, wall_h, size, constants.YELLOW)

    def _check_collision(self, check_positions):
        """Check if any of the given positions collide with obstacles."""
        for x, y in check_positions:
            for obstacle in self.obstacles:
                obstacle_y = (
                                     constants.TASK2_LENGTH - constants.GRID_CELL_LENGTH * 5 - obstacle.position.y) // constants.GRID_CELL_LENGTH
                obstacle_x = obstacle.position.x // constants.GRID_CELL_LENGTH
                if x == obstacle_y and y == obstacle_x:
                    print("COLLISION!")
                    return True
        return False

    def _get_collision_positions_forward(self):
        """Get positions to check for collision when moving forward."""
        direction_offsets = {
            Direction.TOP: [(self.currentPos[0] - 2, x) for x in range(self.currentPos[1] - 1, self.currentPos[1] + 2)],
            Direction.RIGHT: [(x, self.currentPos[1] + 2) for x in
                              range(self.currentPos[0] - 1, self.currentPos[0] + 2)],
            Direction.BOTTOM: [(self.currentPos[0] + 2, y) for y in
                               range(self.currentPos[1] - 1, self.currentPos[1] + 2)],
            Direction.LEFT: [(x, self.currentPos[1] - 2) for x in
                             range(self.currentPos[0] - 1, self.currentPos[0] + 2)],
        }
        return direction_offsets.get(self.currentPos[2], [])

    def _get_collision_positions_backward(self):
        """Get positions to check for collision when moving backward."""
        direction_offsets = {
            Direction.TOP: [(self.currentPos[0] + 2, y) for y in range(self.currentPos[1] - 1, self.currentPos[1] + 2)],
            Direction.RIGHT: [(x, self.currentPos[1] - 2) for x in
                              range(self.currentPos[0] - 1, self.currentPos[0] + 2)],
            Direction.BOTTOM: [(self.currentPos[0] - 2, y) for y in
                               range(self.currentPos[1] - 1, self.currentPos[1] + 2)],
            Direction.LEFT: [(x, self.currentPos[1] + 2) for x in
                             range(self.currentPos[0] - 1, self.currentPos[0] + 2)],
        }
        return direction_offsets.get(self.currentPos[2], [])

    def _execute_movement(self, new_position, cell_size):
        """Execute the movement if valid."""
        self.drawRobot(self.currentPos, cell_size, constants.GREEN, constants.GREEN, constants.GREEN)
        self.bot.set_position_task2(new_position[0], new_position[1], new_position[2])
        return 1

    def moveForward(self, grid_length, grid_width, cell_size):
        """Move robot forward in current direction."""
        collision_positions = self._get_collision_positions_forward()
        if self._check_collision(collision_positions):
            return -1

        # Calculate new position based on direction
        direction_moves = {
            Direction.TOP: (self.currentPos[0] - 1, self.currentPos[1], self.currentPos[2]),
            Direction.RIGHT: (self.currentPos[0], self.currentPos[1] + 1, self.currentPos[2]),
            Direction.BOTTOM: (self.currentPos[0] + 1, self.currentPos[1], self.currentPos[2]),
            Direction.LEFT: (self.currentPos[0], self.currentPos[1] - 1, self.currentPos[2]),
        }

        new_position = direction_moves.get(self.currentPos[2])
        if new_position:
            return self._execute_movement(new_position, cell_size)
        return -1

    def moveBackward(self, grid_length, grid_width, cell_size):
        """Move robot backward (opposite to current direction)."""
        collision_positions = self._get_collision_positions_backward()
        if self._check_collision(collision_positions):
            return -1

        # Calculate new position (opposite of forward movement)
        direction_moves = {
            Direction.TOP: (self.currentPos[0] + 1, self.currentPos[1], self.currentPos[2]),
            Direction.RIGHT: (self.currentPos[0], self.currentPos[1] - 1, self.currentPos[2]),
            Direction.BOTTOM: (self.currentPos[0] - 1, self.currentPos[1], self.currentPos[2]),
            Direction.LEFT: (self.currentPos[0], self.currentPos[1] + 1, self.currentPos[2]),
        }

        new_position = direction_moves.get(self.currentPos[2])
        if new_position:
            # Check bounds
            if (0 <= new_position[0] * cell_size < grid_length and
                    0 <= new_position[1] * cell_size < grid_width):
                return self._execute_movement(new_position, cell_size)
        return -1

    def _get_turn_positions_and_destination(self, turn_type, direction_type):
        """Get collision check positions and destination for turns."""
        # This is a simplified version - you may need to expand based on your constants
        turn_constants = {
            ('right', 'forward'): {
                Direction.TOP: (constants.TURN_MED_RIGHT_TOP_FORWARD, Direction.RIGHT),
                Direction.RIGHT: (constants.TURN_MED_RIGHT_RIGHT_FORWARD, Direction.BOTTOM),
                Direction.BOTTOM: (constants.TURN_MED_RIGHT_BOTTOM_FORWARD, Direction.LEFT),
                Direction.LEFT: (constants.TURN_MED_RIGHT_LEFT_FORWARD, Direction.TOP),
            },
            ('left', 'forward'): {
                Direction.TOP: (constants.TURN_MED_LEFT_TOP_FORWARD, Direction.LEFT),
                Direction.RIGHT: (constants.TURN_MED_LEFT_RIGHT_FORWARD, Direction.TOP),
                Direction.BOTTOM: (constants.TURN_MED_LEFT_BOTTOM_FORWARD, Direction.RIGHT),
                Direction.LEFT: (constants.TURN_MED_LEFT_LEFT_FORWARD, Direction.BOTTOM),
            }
        }

        key = (turn_type, direction_type)
        if key in turn_constants:
            return turn_constants[key].get(self.currentPos[2])
        return None, None

    def turnRight(self, grid_length, grid_width, cell_size):
        """Turn robot right."""
        turn_offset, new_direction = self._get_turn_positions_and_destination('right', 'forward')
        if not turn_offset:
            return -1

        # Simplified collision check - you may need to implement the full range checking
        new_position = (
            self.currentPos[0] - (turn_offset[1] // 10),
            self.currentPos[1] + (turn_offset[0] // 10),
            new_direction
        )

        return self._execute_movement(new_position, cell_size)

    def turnLeft(self, grid_length, grid_width, cell_size):
        """Turn robot left."""
        turn_offset, new_direction = self._get_turn_positions_and_destination('left', 'forward')
        if not turn_offset:
            return -1

        new_position = (
            self.currentPos[0] - (turn_offset[1] // 10),
            self.currentPos[1] + (turn_offset[0] // 10),
            new_direction
        )

        return self._execute_movement(new_position, cell_size)

    # Note: Reverse turn methods would follow similar pattern but with different constants
    def reverseTurnRight(self, grid_length, grid_width, cell_size):
        """Reverse turn right - simplified implementation."""
        # Implementation follows same pattern as turnRight but with reverse constants
        return self.turnLeft(grid_length, grid_width, cell_size)  # Simplified

    def reverseTurnLeft(self, grid_length, grid_width, cell_size):
        """Reverse turn left - simplified implementation."""
        # Implementation follows same pattern as turnLeft but with reverse constants
        return self.turnRight(grid_length, grid_width, cell_size)  # Simplified

    def _execute_diagonal_move(self, move_type, cell_size):
        """Execute diagonal movement based on type and current direction."""
        # Diagonal movement constants mapping
        diagonal_constants = {
            ('northeast', Direction.TOP): constants.TURN_SMALL_RIGHT_TOP_FORWARD,
            ('northeast', Direction.RIGHT): constants.TURN_SMALL_RIGHT_RIGHT_FORWARD,
            ('northeast', Direction.BOTTOM): constants.TURN_SMALL_RIGHT_BOTTOM_FORWARD,
            ('northeast', Direction.LEFT): constants.TURN_SMALL_RIGHT_LEFT_FORWARD,
            ('northwest', Direction.TOP): constants.TURN_SMALL_LEFT_TOP_FORWARD,
            ('northwest', Direction.RIGHT): constants.TURN_SMALL_LEFT_RIGHT_FORWARD,
            ('northwest', Direction.BOTTOM): constants.TURN_SMALL_LEFT_BOTTOM_FORWARD,
            ('northwest', Direction.LEFT): constants.TURN_SMALL_LEFT_LEFT_FORWARD,
            ('southeast', Direction.TOP): constants.TURN_SMALL_RIGHT_TOP_REVERSE,
            ('southeast', Direction.RIGHT): constants.TURN_SMALL_RIGHT_RIGHT_REVERSE,
            ('southeast', Direction.BOTTOM): constants.TURN_SMALL_RIGHT_BOTTOM_REVERSE,
            ('southeast', Direction.LEFT): constants.TURN_SMALL_RIGHT_LEFT_REVERSE,
            ('southwest', Direction.TOP): constants.TURN_SMALL_LEFT_TOP_REVERSE,
            ('southwest', Direction.RIGHT): constants.TURN_SMALL_LEFT_RIGHT_REVERSE,
            ('southwest', Direction.BOTTOM): constants.TURN_SMALL_LEFT_BOTTOM_REVERSE,
            ('southwest', Direction.LEFT): constants.TURN_SMALL_LEFT_LEFT_REVERSE,
        }

        offset = diagonal_constants.get((move_type, self.currentPos[2]))
        if offset:
            new_position = (
                self.currentPos[0] - (offset[1] // 10),
                self.currentPos[1] + (offset[0] // 10),
                self.currentPos[2]
            )
            return self._execute_movement(new_position, cell_size)
        return -1

    def moveNorthEast(self, grid_length, grid_width, cell_size):
        """Move robot northeast diagonally."""
        return self._execute_diagonal_move('northeast', cell_size)

    def moveNorthWest(self, grid_length, grid_width, cell_size):
        """Move robot northwest diagonally."""
        return self._execute_diagonal_move('northwest', cell_size)

    def moveSouthEast(self, grid_length, grid_width, cell_size):
        """Move robot southeast diagonally."""
        return self._execute_diagonal_move('southeast', cell_size)

    def moveSouthWest(self, grid_length, grid_width, cell_size):
        """Move robot southwest diagonally."""
        return self._execute_diagonal_move('southwest', cell_size)

    def draw(self, x, y):
        """Draw UI elements with enhanced hover effects."""
        # Update hover state
        self.hovered_button = self._check_button_hover(x, y)
        self.hover_animation_time = pygame.time.get_ticks() / 1000.0

        # Enhanced Start button with hover
        is_start_hovered = (self.hovered_button == "start")
        start_color = constants.GREEN
        if is_start_hovered:
            # Add pulsing effect
            import math
            pulse = abs(math.sin(self.hover_animation_time * 3)) * 0.2 + 0.8
            start_color = tuple(int(c * pulse) for c in constants.GREEN)

        self.drawEnhancedButtons(650, 500, start_color, "START!", constants.BLACK,
                                 constants.BUTTON_LENGTH, constants.BUTTON_WIDTH,
                                 is_start_hovered, "start")

        # Enhanced coordinates display with hover
        is_coord_hovered = (self.hovered_button == "coordinates")
        coord_bg = constants.DARK_GRAY if is_coord_hovered else constants.BLACK
        coord_text = constants.YELLOW if is_coord_hovered else constants.WHITE

        self.drawEnhancedButtons(650, 550, coord_bg, f"({x}, {y})", coord_text,
                                 constants.BUTTON_LENGTH, constants.BUTTON_WIDTH,
                                 is_coord_hovered, "coordinates")

        # Enhanced Reset button with hover
        is_reset_hovered = (self.hovered_button == "reset")
        self.drawEnhancedButtons(650, 450, constants.GREY, "RESET", constants.BLACK,
                                 constants.BUTTON_LENGTH, constants.BUTTON_WIDTH,
                                 is_reset_hovered, "reset")

        # Draw obstacles
        self.drawObstacles(self.obstacles, constants.RED)

    def updatingTask2Display(self):
        """Update the display with current robot state."""
        self.clock.tick(100)
        self.drawGrid2(self.bot)

        # Update current position from bot
        current_pos = self.bot.get_current_pos()
        self.currentPos = (
            (constants.TASK2_LENGTH - constants.GRID_CELL_LENGTH - current_pos.x) // 10,
            current_pos.y // 10,
            current_pos.direction,
        )

        # Draw robot and obstacles
        cell_size = constants.GRID_CELL_LENGTH * constants.TASK2_SCALING_FACTOR
        self.drawRobot(self.currentPos, cell_size, constants.RED, constants.BLUE, constants.LIGHT_BLUE)
        self.drawObstacles(self.obstacles, constants.RED)
        pygame.time.delay(100)

    def _execute_obstacle_maneuver(self, obstacle_direction, movement):
        """Execute obstacle avoidance maneuver."""
        grid_length = constants.TASK2_LENGTH * constants.TASK2_SCALING_FACTOR
        grid_width = constants.TASK2_WIDTH * constants.TASK2_SCALING_FACTOR
        cell_size = constants.GRID_CELL_LENGTH * constants.TASK2_SCALING_FACTOR

        if obstacle_direction == "L":
            self.left(movement)
        elif obstacle_direction == "R":
            self.right(movement)

    def left(self, movement):
        """Execute left obstacle avoidance sequence."""
        grid_length = constants.TASK2_LENGTH * constants.TASK2_SCALING_FACTOR
        grid_width = constants.TASK2_WIDTH * constants.TASK2_SCALING_FACTOR
        cell_size = constants.GRID_CELL_LENGTH * constants.TASK2_SCALING_FACTOR

        # Move backward 3 steps
        for _ in range(3):
            self.moveBackward(grid_length, grid_width, cell_size)
            movement["forward"] -= 1
            self.updatingTask2Display()
            pygame.display.update()

        # Execute turn sequence
        turn_sequence = [self.turnLeft, self.turnRight, self.turnRight, self.turnLeft]
        for turn_func in turn_sequence:
            turn_func(grid_length, grid_width, cell_size)
            self.updatingTask2Display()
            pygame.display.update()

        movement["forward"] += 10

    def right(self, movement):
        """Execute right obstacle avoidance sequence."""
        grid_length = constants.TASK2_LENGTH * constants.TASK2_SCALING_FACTOR
        grid_width = constants.TASK2_WIDTH * constants.TASK2_SCALING_FACTOR
        cell_size = constants.GRID_CELL_LENGTH * constants.TASK2_SCALING_FACTOR

        # Move backward 3 steps
        for _ in range(3):
            self.moveBackward(grid_length, grid_width, cell_size)
            movement["forward"] -= 1
            self.updatingTask2Display()
            pygame.display.update()

        # Execute turn sequence
        turn_sequence = [self.turnRight, self.turnLeft, self.turnLeft, self.turnRight]
        for turn_func in turn_sequence:
            turn_func(grid_length, grid_width, cell_size)
            self.updatingTask2Display()
            pygame.display.update()

        movement["forward"] += 10

    def _execute_second_obstacle_maneuver(self, obstacle_direction, movement):
        """Execute second obstacle avoidance maneuver."""
        if obstacle_direction == "L":
            self.secondleft(movement)
        elif obstacle_direction == "R":
            self.secondright(movement)

    def secondleft(self, movement):
        """Execute second left obstacle avoidance sequence."""
        grid_length = constants.TASK2_LENGTH * constants.TASK2_SCALING_FACTOR
        grid_width = constants.TASK2_WIDTH * constants.TASK2_SCALING_FACTOR
        cell_size = constants.GRID_CELL_LENGTH * constants.TASK2_SCALING_FACTOR

        # Initial backward movement
        for _ in range(2):
            self.moveBackward(grid_length, grid_width, cell_size)
            movement["forward"] -= 1
            self.updatingTask2Display()
            pygame.display.update()

        movement["forward"] -= 1

        # Turn sequence
        self.turnLeft(grid_length, grid_width, cell_size)
        self.updatingTask2Display()
        pygame.display.update()

        self.turnRight(grid_length, grid_width, cell_size)
        self.updatingTask2Display()
        pygame.display.update()

        self.turnRight(grid_length, grid_width, cell_size)
        self.updatingTask2Display()
        pygame.display.update()

        # Move forward 5 steps
        for _ in range(5):
            self.moveForward(grid_length, grid_width, cell_size)
            self.updatingTask2Display()
            pygame.display.update()

        self.turnRight(grid_length, grid_width, cell_size)
        self.updatingTask2Display()
        pygame.display.update()

        # Move forward by remaining movement
        for _ in range(movement["forward"]):
            self.moveForward(grid_length, grid_width, cell_size)
            self.updatingTask2Display()
            pygame.display.update()

        # Final turns
        self.turnRight(grid_length, grid_width, cell_size)
        self.updatingTask2Display()
        pygame.display.update()

        self.turnLeft(grid_length, grid_width, cell_size)
        self.updatingTask2Display()
        pygame.display.update()

    def secondright(self, movement):
        """Execute second right obstacle avoidance sequence."""
        grid_length = constants.TASK2_LENGTH * constants.TASK2_SCALING_FACTOR
        grid_width = constants.TASK2_WIDTH * constants.TASK2_SCALING_FACTOR
        cell_size = constants.GRID_CELL_LENGTH * constants.TASK2_SCALING_FACTOR

        # Initial backward movement
        for _ in range(2):
            self.moveBackward(grid_length, grid_width, cell_size)
            movement["forward"] -= 1
            self.updatingTask2Display()
            pygame.display.update()

        movement["forward"] -= 1

        # Turn sequence (opposite of left)
        self.turnRight(grid_length, grid_width, cell_size)
        self.updatingTask2Display()
        pygame.display.update()

        self.turnLeft(grid_length, grid_width, cell_size)
        self.updatingTask2Display()
        pygame.display.update()

        self.turnLeft(grid_length, grid_width, cell_size)
        self.updatingTask2Display()
        pygame.display.update()

        # Move forward 5 steps
        for _ in range(5):
            self.moveForward(grid_length, grid_width, cell_size)
            self.updatingTask2Display()
            pygame.display.update()

        self.turnLeft(grid_length, grid_width, cell_size)
        self.updatingTask2Display()
        pygame.display.update()

        # Move forward by remaining movement
        for _ in range(movement["forward"]):
            self.moveForward(grid_length, grid_width, cell_size)
            self.updatingTask2Display()
            pygame.display.update()

        # Final turns
        self.turnLeft(grid_length, grid_width, cell_size)
        self.updatingTask2Display()
        pygame.display.update()

        self.turnRight(grid_length, grid_width, cell_size)
        self.updatingTask2Display()
        pygame.display.update()

    def task2Algo(self, direction):
        """Main algorithm for Task 2 obstacle navigation."""
        movement = {"forward": 0}
        grid_length = constants.TASK2_LENGTH * constants.TASK2_SCALING_FACTOR
        grid_width = constants.TASK2_WIDTH * constants.TASK2_SCALING_FACTOR
        cell_size = constants.GRID_CELL_LENGTH * constants.TASK2_SCALING_FACTOR

        # Move forward until obstacle is detected
        while True:
            result = self.moveForward(grid_length, grid_width, cell_size)
            if result == 1:  # No collision
                movement["forward"] += 1
                self.updatingTask2Display()
                pygame.display.update()
            elif result == -1:  # Collision detected
                break

        # Handle first obstacle
        self._execute_obstacle_maneuver(direction[0], movement)

        # Continue moving until second obstacle
        while True:
            result = self.moveForward(grid_length, grid_width, cell_size)
            if result == 1:  # No collision
                movement["forward"] += 1
                self.updatingTask2Display()
                pygame.display.update()
            elif result == -1:  # Collision detected
                break

        # Handle second obstacle
        self._execute_second_obstacle_maneuver(direction[1], movement)

    def _handle_movement_keys(self, keys):
        """Handle movement key combinations."""
        grid_length = constants.TASK2_LENGTH * constants.TASK2_SCALING_FACTOR
        grid_width = constants.TASK2_WIDTH * constants.TASK2_SCALING_FACTOR
        cell_size = constants.GRID_CELL_LENGTH * constants.TASK2_SCALING_FACTOR

        if keys[pygame.K_UP]:
            if keys[pygame.K_RIGHT]:
                self.turnRight(grid_length, grid_width, cell_size)
            elif keys[pygame.K_LEFT]:
                self.turnLeft(grid_length, grid_width, cell_size)
            else:
                self.moveForward(grid_length, grid_width, cell_size)
        elif keys[pygame.K_DOWN]:
            if keys[pygame.K_RIGHT]:
                self.reverseTurnRight(grid_length, grid_width, cell_size)
            elif keys[pygame.K_LEFT]:
                self.reverseTurnLeft(grid_length, grid_width, cell_size)
            else:
                self.moveBackward(grid_length, grid_width, cell_size)

    def _handle_diagonal_keys(self, event):
        """Handle diagonal movement keys."""
        grid_length = constants.TASK2_LENGTH * constants.TASK2_SCALING_FACTOR
        grid_width = constants.TASK2_WIDTH * constants.TASK2_SCALING_FACTOR
        cell_size = constants.GRID_CELL_LENGTH * constants.TASK2_SCALING_FACTOR

        diagonal_moves = {
            pygame.K_e: self.moveNorthEast,
            pygame.K_q: self.moveNorthWest,
            pygame.K_d: self.moveSouthEast,
            pygame.K_a: self.moveSouthWest,
        }

        move_func = diagonal_moves.get(event.key)
        if move_func:
            move_func(grid_length, grid_width, cell_size)

    def runTask2Simulation(self, bot):
        """Main simulation loop for Task 2."""
        self.bot = deepcopy(bot)
        self.clock = pygame.time.Clock()
        self.obstacles = self.bot.hamiltonian.grid.obstacles

        while True:
            self.updatingTask2Display()
            x, y = pygame.mouse.get_pos()

            # Store last mouse position for animations
            self.last_mouse_pos = (x, y)

            self.draw(x, y)

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()

                elif event.type == pygame.MOUSEBUTTONDOWN:
                    self._handle_mouse_clicks(x, y, bot)

                elif event.type == pygame.KEYDOWN:
                    keys = pygame.key.get_pressed()
                    self._handle_movement_keys(keys)
                    self._handle_diagonal_keys(event)

            pygame.display.update()

    def _handle_mouse_clicks(self, x, y, bot):
        """Handle mouse click events with click delay protection."""
        current_time = pygame.time.get_ticks()

        # Prevent rapid clicking
        if current_time - self.last_click_time < self.click_delay:
            return

        self.last_click_time = current_time

        button_bounds = (650, 650 + constants.BUTTON_LENGTH)

        if button_bounds[0] < x < button_bounds[1]:
            if 500 < y < 500 + constants.BUTTON_WIDTH:
                print("START BUTTON IS CLICKED!!! I REPEAT, START BUTTON IS CLICKED!!!")
                self.task2Algo(self.direction)
            elif 450 < y < 450 + constants.BUTTON_WIDTH:
                print("RESET BUTTON CLICKED!")
                self.reset(bot)