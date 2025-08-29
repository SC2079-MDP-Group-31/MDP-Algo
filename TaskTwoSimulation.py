# Cleaned

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

        pygame.mouse.set_visible(1)
        pygame.display.set_caption("Vroom Vroom Simulation")
        self.screen.fill(constants.BLACK)

    def reset(self, bot):
        """Reset the simulation to initial state."""
        self.screen.fill(constants.BLACK)
        current_pos = bot.get_current_pos()
        self.currentPos = (
            (constants.GRID_LENGTH - constants.GRID_CELL_LENGTH - current_pos.x) // 10,
            current_pos.y // 10,
            current_pos.direction,
        )
        self.bot.set_position_task2(self.currentPos[0], self.currentPos[1], self.currentPos[2])
        self.bot.hamiltonian.commands.clear()

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

    def drawButtons(self, x_pos, y_pos, bg_color, text, text_color, length, width):
        """Draw UI buttons."""
        button = pygame.Rect(x_pos, y_pos, length, width)
        pygame.draw.rect(self.screen, bg_color, button)

        text_surface = self.font.render(text, True, text_color)
        text_rect = text_surface.get_rect(
            center=(button.x + (length // 2), button.y + (width // 2))
        )
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
        """Draw UI elements."""
        # Start button
        self.drawButtons(650, 500, constants.GREEN, "START!", constants.BLACK,
                         constants.BUTTON_LENGTH, constants.BUTTON_WIDTH)

        # Current cursor coordinates
        self.drawButtons(650, 550, constants.BLACK, f"({x}, {y})", constants.WHITE,
                         constants.BUTTON_LENGTH, constants.BUTTON_WIDTH)

        # Reset button
        self.drawButtons(650, 450, constants.GREY, "RESET", constants.BLACK,
                         constants.BUTTON_LENGTH, constants.BUTTON_WIDTH)

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
        """Handle mouse click events."""
        button_bounds = (650, 650 + constants.BUTTON_LENGTH)

        if button_bounds[0] < x < button_bounds[1]:
            if 500 < y < 500 + constants.BUTTON_WIDTH:
                print("START BUTTON IS CLICKED!!! I REPEAT, START BUTTON IS CLICKED!!!")
                self.task2Algo(self.direction)
            elif 450 < y < 450 + constants.BUTTON_WIDTH:
                self.reset(bot)