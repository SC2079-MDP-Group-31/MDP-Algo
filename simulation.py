import sys
import time
from copy import deepcopy
import math

import pygame
import pygame.freetype

import constants
from commands.go_straight_command import StraightCommand
from commands.scan_obstacle_command import ScanCommand
from commands.turn_command import TurnCommand
from misc.direction import Direction
from misc.type_of_turn import TypeOfTurn


class Simulation:
    def __init__(self):
        pygame.init()
        self.running = True
        self.font = pygame.font.Font("fonts/Formula1-Regular.ttf", 20)
        self.screen = pygame.display.set_mode((800, 650), pygame.RESIZABLE)
        self.clock = None
        self.bot = None
        self.obstacles = []
        self.currentPos = (0, 0, Direction.TOP)

        # Add state management for buttons
        self.is_executing = False  # Prevent multiple START clicks
        self.last_click_time = 0  # Prevent rapid clicking
        self.click_delay = 500  # Minimum delay between clicks (ms)

        # Hover effect state management
        self.hovered_button = None
        self.hovered_movement = None
        self.hover_animation_time = 0
        self.last_mouse_pos = (0, 0)

        pygame.mouse.set_visible(True)
        pygame.display.set_caption("MDP 34 GRAND PRIX SIMULATOR")
        self.screen.fill(constants.DEEP_BLUE)
        self.drawGridBackground()

    def reset(self, bot):
        """Reset the simulation to initial state - robot back to bottom-left corner"""
        print("Resetting simulation...")

        # Stop any current execution
        self.is_executing = False

        # Clear the screen and redraw background
        self.screen.fill(constants.DEEP_BLUE)
        self.drawGridBackground()
        self.drawGrid()

        # Reset robot to initial starting position (bottom-left corner)
        # Starting position in world coordinates
        start_world_x = 180  # 1 cell from left edge
        start_world_y = 10  # 1 cell from bottom edge
        start_direction = Direction.TOP

        print(f"Resetting robot to world position: ({start_world_x}, {start_world_y})")

        # Update the robot's actual position
        if hasattr(self.bot, 'set_position'):
            grid_x = start_world_x // 10
            grid_y = start_world_y // 10
            self.bot.set_position(grid_x, grid_y, start_direction)
            print(f"Bot position set to grid: ({grid_x}, {grid_y})")

        # Update the display position
        display_x = grid_x
        display_y = grid_y
        self.currentPos = (display_x, display_y, start_direction)
        print(f"Display position set to: {self.currentPos}")

        # Clear all commands
        if hasattr(self.bot, 'hamiltonian') and hasattr(self.bot.hamiltonian, 'commands'):
            self.bot.hamiltonian.commands.clear()
            print("Cleared command queue")

        # Clear any path planning results
        if hasattr(self.bot.hamiltonian, 'simple_hamiltonian'):
            self.bot.hamiltonian.simple_hamiltonian = tuple()
            print("Cleared hamiltonian path")

        # Redraw the robot at the starting position
        self.drawRobot(self.currentPos,
                       constants.GRID_CELL_LENGTH * constants.SCALING_FACTOR,
                       constants.RED, constants.BLUE, constants.LIGHT_BLUE)

        print(f"Robot reset complete - Position: {self.currentPos}")

        # Force a display update
        pygame.display.update()

    def selectObstacles(self, y, x, cellSize, color):
        """Draw a single obstacle cell"""
        newRect = pygame.Rect(y * cellSize, x * cellSize, cellSize, cellSize)
        self.screen.fill(color, newRect)
        pygame.draw.rect(self.screen, color, newRect, 2)

    def _drawDirectionIndicator(self, robotPos, cellSize, directionColor):
        """Helper method to draw direction indicator on robot"""
        direction_rects = {
            Direction.TOP: pygame.Rect(
                robotPos[1] * cellSize, robotPos[0] * cellSize, cellSize, 5
            ),
            Direction.RIGHT: pygame.Rect(
                (robotPos[1] * cellSize) + cellSize - 5, robotPos[0] * cellSize, 5, cellSize
            ),
            Direction.BOTTOM: pygame.Rect(
                robotPos[1] * cellSize, (robotPos[0] * cellSize) + cellSize - 5, cellSize, 5
            ),
            Direction.LEFT: pygame.Rect(
                robotPos[1] * cellSize, robotPos[0] * cellSize, 5, cellSize
            )
        }

        rect = direction_rects.get(robotPos[2])
        if rect:
            self.screen.fill(directionColor, rect)
            pygame.draw.rect(self.screen, directionColor, rect, 5)

    def drawRobot(self, robotPos, cellSize, directionColor, botColor, botAreaColor):
        """Draw the robot on the grid"""
        for x in range(robotPos[0] - 1, robotPos[0] + 2):
            for y in range(robotPos[1] - 1, robotPos[1] + 2):
                if not (0 <= x * cellSize < constants.GRID_LENGTH * constants.SCALING_FACTOR and
                        0 <= y * cellSize < constants.GRID_LENGTH * constants.SCALING_FACTOR):
                    continue

                rect = pygame.Rect(y * cellSize, x * cellSize, cellSize, cellSize)

                if robotPos[0] == x and robotPos[1] == y:
                    # Center cell - draw robot body and direction indicator
                    self.screen.fill(botColor, rect)
                    pygame.draw.rect(self.screen, botColor, rect, 2)
                    self._drawDirectionIndicator(robotPos, cellSize, directionColor)
                else:
                    # Surrounding cells - draw robot area
                    self.screen.fill(botAreaColor, rect)
                    pygame.draw.rect(self.screen, botAreaColor, rect, 1)

    def drawGridBackground(self):
        """Draw the background grid"""
        cell_size = constants.GRID_CELL_LENGTH * constants.SCALING_FACTOR
        grid_size = constants.GRID_LENGTH * constants.SCALING_FACTOR

        for x in range(0, grid_size, cell_size):
            for y in range(0, grid_size, cell_size):
                rect = pygame.Rect(y, x, cell_size, cell_size)
                self.screen.fill(constants.GREY, rect)

    def drawGrid(self):
        """Draw the main game grid with special areas"""
        cell_size = constants.GRID_CELL_LENGTH * constants.SCALING_FACTOR
        grid_size = constants.GRID_LENGTH * constants.SCALING_FACTOR

        for x in range(0, grid_size, cell_size):
            for y in range(0, grid_size, cell_size):
                # Special orange area in top-right corner
                if (x > (constants.GRID_LENGTH - 5 * constants.GRID_CELL_LENGTH) * constants.SCALING_FACTOR and
                        y < 4 * constants.GRID_CELL_LENGTH * constants.SCALING_FACTOR):
                    rect = pygame.Rect(y, x, cell_size, cell_size)
                    self.screen.fill(constants.ORANGE, rect)
                    pygame.draw.rect(self.screen, constants.ORANGE, rect, 2)

                # Draw grid lines
                rect = pygame.Rect(y, x, cell_size, cell_size)
                pygame.draw.rect(self.screen, constants.BLACK, rect, 1)

    def _get_hover_color(self, base_color, hover_intensity=0.3):
        """Generate a lighter version of a color for hover effects"""
        return tuple(min(255, int(c + (255 - c) * hover_intensity)) for c in base_color)

    def _get_glow_effect(self, rect, color, intensity=20):
        """Create a glowing border effect around a rectangle"""
        for i in range(3):
            glow_rect = pygame.Rect(rect.x - i, rect.y - i, rect.width + 2 * i, rect.height + 2 * i)
            glow_color = (*color, max(50 - i * 15, 10))
            pygame.draw.rect(self.screen, color, glow_rect, 2)

    def drawButtons(self, xpos, ypos, bgcolor, text, textColor, length, width, is_hovered=False, is_disabled=False):
        """Draw a button with text and hover effects"""
        # Determine button colors based on state
        if is_disabled:
            bg_color = (100, 100, 100)
            text_color = (150, 150, 150)
            border_color = (80, 80, 80)
        elif is_hovered:
            bg_color = self._get_hover_color(bgcolor, 0.4)
            text_color = textColor
            border_color = constants.WHITE
        else:
            bg_color = bgcolor
            text_color = textColor
            border_color = constants.BLACK

        # Create button rectangle
        button_rect = pygame.Rect(xpos, ypos, length, width)

        # Add glow effect for hovered buttons
        if is_hovered and not is_disabled:
            self._get_glow_effect(button_rect, bg_color)

        # Draw main button
        pygame.draw.rect(self.screen, bg_color, button_rect)

        # Draw border with appropriate thickness
        border_width = 4 if is_hovered else 3
        pygame.draw.rect(self.screen, border_color, button_rect, border_width)

        # Add subtle shadow effect
        if not is_disabled:
            shadow_rect = pygame.Rect(xpos + 2, ypos + 2, length, width)
            pygame.draw.rect(self.screen, (50, 50, 50), shadow_rect, 2)

        # Draw text
        text_surface = self.font.render(text, True, text_color)
        text_rect = text_surface.get_rect(center=(xpos + length // 2, ypos + width // 2))
        self.screen.blit(text_surface, text_rect)

    def drawImage(self, image, xpos, ypos, bgcolor, length, width, is_hovered=False):
        """Draw an image centered in a rectangle with hover effects"""
        # Create background rectangle
        bg_rect = pygame.Rect(xpos, ypos, length, width)

        # Apply hover effects
        if is_hovered:
            hover_color = self._get_hover_color(bgcolor, 0.3)
            pygame.draw.rect(self.screen, hover_color, bg_rect)
            pygame.draw.rect(self.screen, constants.WHITE, bg_rect, 3)
            # Add a subtle scale effect by adjusting image position
            scale_offset = 2
            rect = image.get_rect()
            rect.center = (xpos + length // 2 - scale_offset, ypos + width // 2 - scale_offset)
        else:
            pygame.draw.rect(self.screen, bgcolor, bg_rect)
            rect = image.get_rect()
            rect.center = (xpos + length // 2, ypos + width // 2)

        self.screen.blit(image, rect)

    def _drawObstacleDirection(self, x, y, direction, color, size):
        """Helper to draw direction indicator on obstacles"""
        direction_rects = {
            Direction.TOP: pygame.Rect(x * size, y * size, size, 5),
            Direction.RIGHT: pygame.Rect((x * size) + size - 5, y * size, 5, size),
            Direction.BOTTOM: pygame.Rect(x * size, (y * size) + size - 5, size, 5),
            Direction.LEFT: pygame.Rect(x * size, y * size, 5, size)
        }

        rect = direction_rects.get(direction)
        if rect:
            self.screen.fill(color, rect)
            pygame.draw.rect(self.screen, color, rect, 5)

    def _check_button_hover(self, mouse_x, mouse_y):
        """Check which button is being hovered over"""
        button_width = 140
        button_height = 45
        button_x = 630
        button_spacing = 60

        # Check main control buttons
        buttons = [
            ("start", button_x, 300),
            ("reset", button_x, 300 + button_spacing),
            ("draw_path", button_x, 300 + button_spacing * 2)
        ]

        for button_name, x, y in buttons:
            if (x <= mouse_x <= x + button_width and y <= mouse_y <= y + button_height):
                return button_name

        return None

    def _check_movement_hover(self, mouse_x, mouse_y):
        """Check which movement control is being hovered over"""
        movement_buttons = [
            ("forward", 685, 110),
            ("backward", 685, 180),
            ("turn_right", 720, 132.5),
            ("turn_left", 650, 132.5),
            ("reverse_right", 720, 160),
            ("reverse_left", 650, 160),
            ("northeast", 720, 107.5),
            ("northwest", 650, 107.5),
            ("southeast", 720, 182.5),
            ("southwest", 650, 182.5)
        ]

        button_size = constants.GRID_CELL_LENGTH * constants.SCALING_FACTOR

        for button_name, x, y in movement_buttons:
            if (x <= mouse_x <= x + button_size and y <= mouse_y <= y + button_size):
                return button_name

        return None

    def drawObstaclesButton(self, obstacles, color):
        """Draw obstacles and control images with hover effects"""
        size = constants.GRID_CELL_LENGTH * constants.SCALING_FACTOR

        # Draw obstacles
        for obstacle in obstacles:
            y = (constants.GRID_LENGTH - constants.GRID_CELL_LENGTH - obstacle.position.y) // constants.GRID_CELL_LENGTH
            x = obstacle.position.x // constants.GRID_CELL_LENGTH
            direction = obstacle.position.direction

            self.selectObstacles(x, y, size, constants.GOLD)
            self._drawObstacleDirection(x, y, direction, color, size)

        # Draw control images with hover effects
        control_images = [
            ("images/MoveForward.png", 685, 110, "forward"),
            ("images/MoveBackward.png", 685, 180, "backward"),
            ("images/TurnForwardRight.png", 720, 132.5, "turn_right"),
            ("images/TurnForwardLeft.png", 650, 132.5, "turn_left"),
            ("images/TurnReverseRight.png", 720, 160, "reverse_right"),
            ("images/TurnReverseLeft.png", 650, 160, "reverse_left"),
            ("images/slantForwardRight.png", 720, 107.5, "northeast"),
            ("images/slantForwardLeft.png", 650, 107.5, "northwest"),
            ("images/slantBackwardsRight.png", 720, 182.5, "southeast"),
            ("images/slantBackwardsLeft.png", 650, 182.5, "southwest")
        ]

        for image_path, x_pos, y_pos, button_name in control_images:
            try:
                img = pygame.image.load(image_path).convert()
                is_hovered = (self.hovered_movement == button_name)
                self.drawImage(img, x_pos, y_pos, constants.GREY, size, size, is_hovered)
            except pygame.error:
                # Draw a placeholder rectangle if image not found
                is_hovered = (self.hovered_movement == button_name)
                bg_color = constants.LIGHT_BLUE if is_hovered else constants.GREY
                rect = pygame.Rect(x_pos, y_pos, size, size)
                pygame.draw.rect(self.screen, bg_color, rect)
                pygame.draw.rect(self.screen, constants.BLACK, rect, 2)

    def _checkBounds(self, new_x, new_y, gridSize, cellSize):
        """Check if new position is within grid bounds"""
        return (0 <= new_x * cellSize < gridSize and
                0 <= new_y * cellSize < gridSize)

    def _moveRobotTo(self, new_x, new_y, direction, gridSize, cellSize):
        """Helper to move robot to new position if valid"""
        if self._checkBounds(new_x, new_y, gridSize, cellSize):
            self.drawRobot(self.currentPos, cellSize, constants.GREEN, constants.GREEN, constants.GREEN)
            self.bot.set_position(new_x, new_y, direction)
            return True
        return False

    def moveForward(self, gridSize, cellSize):
        """Move robot forward based on current direction"""
        steps = 1
        direction_moves = {
            Direction.TOP: (self.currentPos[0] - steps, self.currentPos[1]),
            Direction.RIGHT: (self.currentPos[0], self.currentPos[1] + steps),
            Direction.BOTTOM: (self.currentPos[0] + steps, self.currentPos[1]),
            Direction.LEFT: (self.currentPos[0], self.currentPos[1] - steps)
        }

        new_x, new_y = direction_moves.get(self.currentPos[2], self.currentPos[:2])
        self._moveRobotTo(new_x, new_y, self.currentPos[2], gridSize, cellSize)

    def moveBackward(self, gridSize, cellSize):
        """Move robot backward based on current direction"""
        steps = 1
        direction_moves = {
            Direction.TOP: (self.currentPos[0] + steps, self.currentPos[1]),
            Direction.RIGHT: (self.currentPos[0], self.currentPos[1] - steps),
            Direction.BOTTOM: (self.currentPos[0] - steps, self.currentPos[1]),
            Direction.LEFT: (self.currentPos[0], self.currentPos[1] + steps)
        }

        new_x, new_y = direction_moves.get(self.currentPos[2], self.currentPos[:2])
        self._moveRobotTo(new_x, new_y, self.currentPos[2], gridSize, cellSize)

    def _performTurn(self, turn_constants, new_direction, gridSize, cellSize, turn_type="TURN"):
        """Generic method to perform turns with given constants"""
        turn_constant = turn_constants.get(self.currentPos[2])
        if not turn_constant:
            return

        new_x = self.currentPos[0] - (turn_constant[1] // 10)
        new_y = self.currentPos[1] + (turn_constant[0] // 10)

        if self._checkBounds(new_x, new_y, gridSize, cellSize):
            print(f"{turn_type}\t{self.currentPos}")
            self.drawRobot(self.currentPos, cellSize, constants.GREEN, constants.GREEN, constants.GREEN)
            self.bot.set_position(new_x, new_y, new_direction[self.currentPos[2]])

    def turnRight(self, gridSize, cellSize):
        """Turn robot right"""
        turn_constants = {
            Direction.TOP: constants.TURN_MED_RIGHT_TOP_FORWARD,
            Direction.RIGHT: constants.TURN_MED_RIGHT_RIGHT_FORWARD,
            Direction.BOTTOM: constants.TURN_MED_RIGHT_BOTTOM_FORWARD,
            Direction.LEFT: constants.TURN_MED_RIGHT_LEFT_FORWARD
        }
        new_directions = {
            Direction.TOP: Direction.RIGHT,
            Direction.RIGHT: Direction.BOTTOM,
            Direction.BOTTOM: Direction.LEFT,
            Direction.LEFT: Direction.TOP
        }
        self._performTurn(turn_constants, new_directions, gridSize, cellSize, "TURNING RIGHT")

    def turnLeft(self, gridSize, cellSize):
        """Turn robot left"""
        turn_constants = {
            Direction.TOP: constants.TURN_MED_LEFT_TOP_FORWARD,
            Direction.RIGHT: constants.TURN_MED_LEFT_RIGHT_FORWARD,
            Direction.BOTTOM: constants.TURN_MED_LEFT_BOTTOM_FORWARD,
            Direction.LEFT: constants.TURN_MED_LEFT_LEFT_FORWARD
        }
        new_directions = {
            Direction.TOP: Direction.LEFT,
            Direction.RIGHT: Direction.TOP,
            Direction.BOTTOM: Direction.RIGHT,
            Direction.LEFT: Direction.BOTTOM
        }
        self._performTurn(turn_constants, new_directions, gridSize, cellSize, "TURNING LEFT")

    def reverseTurnRight(self, gridSize, cellSize):
        """Reverse turn right"""
        turn_constants = {
            Direction.TOP: constants.TURN_MED_RIGHT_TOP_REVERSE,
            Direction.RIGHT: constants.TURN_MED_RIGHT_RIGHT_REVERSE,
            Direction.BOTTOM: constants.TURN_MED_RIGHT_BOTTOM_REVERSE,
            Direction.LEFT: constants.TURN_MED_RIGHT_LEFT_REVERSE
        }
        new_directions = {
            Direction.TOP: Direction.LEFT,
            Direction.RIGHT: Direction.TOP,
            Direction.BOTTOM: Direction.RIGHT,
            Direction.LEFT: Direction.BOTTOM
        }
        self._performTurn(turn_constants, new_directions, gridSize, cellSize, "REVERSE RIGHT")

    def reverseTurnLeft(self, gridSize, cellSize):
        """Reverse turn left"""
        turn_constants = {
            Direction.TOP: constants.TURN_MED_LEFT_TOP_REVERSE,
            Direction.RIGHT: constants.TURN_MED_LEFT_RIGHT_REVERSE,
            Direction.BOTTOM: constants.TURN_MED_LEFT_BOTTOM_REVERSE,
            Direction.LEFT: constants.TURN_MED_LEFT_LEFT_REVERSE
        }
        new_directions = {
            Direction.TOP: Direction.RIGHT,
            Direction.RIGHT: Direction.BOTTOM,
            Direction.BOTTOM: Direction.LEFT,
            Direction.LEFT: Direction.TOP
        }
        self._performTurn(turn_constants, new_directions, gridSize, cellSize, "REVERSE LEFT")

    def _performSlantMove(self, turn_constants, gridSize, cellSize):
        """Generic method for slant moves (NE, NW, SE, SW)"""
        turn_constant = turn_constants.get(self.currentPos[2])
        if not turn_constant:
            return

        new_x = self.currentPos[0] - (turn_constant[1] // 10)
        new_y = self.currentPos[1] + (turn_constant[0] // 10)

        self._moveRobotTo(new_x, new_y, self.currentPos[2], gridSize, cellSize)

    def moveNorthEast(self, gridSize, cellSize):
        """Move northeast (slant forward right)"""
        turn_constants = {
            Direction.TOP: constants.TURN_SMALL_RIGHT_TOP_FORWARD,
            Direction.RIGHT: constants.TURN_SMALL_RIGHT_RIGHT_FORWARD,
            Direction.BOTTOM: constants.TURN_SMALL_RIGHT_BOTTOM_FORWARD,
            Direction.LEFT: constants.TURN_SMALL_RIGHT_LEFT_FORWARD
        }
        self._performSlantMove(turn_constants, gridSize, cellSize)

    def moveNorthWest(self, gridSize, cellSize):
        """Move northwest (slant forward left)"""
        turn_constants = {
            Direction.TOP: constants.TURN_SMALL_LEFT_TOP_FORWARD,
            Direction.RIGHT: constants.TURN_SMALL_LEFT_RIGHT_FORWARD,
            Direction.BOTTOM: constants.TURN_SMALL_LEFT_BOTTOM_FORWARD,
            Direction.LEFT: constants.TURN_SMALL_LEFT_LEFT_FORWARD
        }
        self._performSlantMove(turn_constants, gridSize, cellSize)

    def moveSouthEast(self, gridSize, cellSize):
        """Move southeast (slant backward right)"""
        turn_constants = {
            Direction.TOP: constants.TURN_SMALL_RIGHT_TOP_REVERSE,
            Direction.RIGHT: constants.TURN_SMALL_RIGHT_RIGHT_REVERSE,
            Direction.BOTTOM: constants.TURN_SMALL_RIGHT_BOTTOM_REVERSE,
            Direction.LEFT: constants.TURN_SMALL_RIGHT_LEFT_REVERSE
        }
        self._performSlantMove(turn_constants, gridSize, cellSize)

    def moveSouthWest(self, gridSize, cellSize):
        """Move southwest (slant backward left)"""
        turn_constants = {
            Direction.TOP: constants.TURN_SMALL_LEFT_TOP_REVERSE,
            Direction.RIGHT: constants.TURN_SMALL_LEFT_RIGHT_REVERSE,
            Direction.BOTTOM: constants.TURN_SMALL_LEFT_BOTTOM_REVERSE,
            Direction.LEFT: constants.TURN_SMALL_LEFT_LEFT_REVERSE
        }
        self._performSlantMove(turn_constants, gridSize, cellSize)

    def movement(self, x, y, buttonLength, buttonWidth):
        """Handle movement based on button clicks"""
        grid_size = constants.GRID_LENGTH * constants.SCALING_FACTOR
        cell_size = constants.GRID_CELL_LENGTH * constants.SCALING_FACTOR

        # Movement button mappings
        movement_map = [
            ((685, 110), self.moveForward),  # North
            ((685, 180), self.moveBackward),  # South
            ((720, 132.5), self.turnRight),  # Forward East
            ((650, 132.5), self.turnLeft),  # Forward West
            ((720, 160), self.reverseTurnRight),  # Backward East
            ((650, 160), self.reverseTurnLeft),  # Backward West
            ((720, 107.5), self.moveNorthEast),  # NE
            ((650, 107.5), self.moveNorthWest),  # NW
            ((720, 182.5), self.moveSouthEast),  # SE
            ((650, 182.5), self.moveSouthWest)  # SW
        ]

        for (btn_x, btn_y), action in movement_map:
            if (btn_x < x < btn_x + buttonLength and
                    btn_y < y < btn_y + buttonWidth):
                action(grid_size, cell_size)
                break

    def draw(self, x, y):
        """Draw all UI elements with hover effects"""
        # Update hover states
        self.hovered_button = self._check_button_hover(x, y)
        self.hovered_movement = self._check_movement_hover(x, y)

        # Update animation timer for subtle effects
        self.hover_animation_time = pygame.time.get_ticks() / 1000.0

        # Improved button layout with better spacing and colors
        button_width = 140
        button_height = 45
        button_x = 630
        button_spacing = 60

        # Change START button color based on execution state
        start_color = (34, 139, 34) if not self.is_executing else (100, 100, 100)
        start_text = "START!" if not self.is_executing else "RUNNING..."
        start_disabled = self.is_executing

        # Button specifications with hover states
        button_specs = [
            ("start", button_x, 300, start_color, start_text, constants.WHITE, start_disabled),
            ("reset", button_x, 300 + button_spacing, (220, 20, 60), "RESET", constants.WHITE, False),
            ("draw_path", button_x, 300 + button_spacing * 2, (70, 130, 180), "DRAW PATH", constants.WHITE, False)
        ]

        for button_name, x_pos, y_pos, bg_color, text, text_color, is_disabled in button_specs:
            is_hovered = (self.hovered_button == button_name and not is_disabled)

            # Add pulsing effect for START button when ready
            if button_name == "start" and not is_disabled and is_hovered:
                pulse = abs(math.sin(self.hover_animation_time * 3)) * 0.2 + 0.8
                bg_color = tuple(int(c * pulse) for c in bg_color)

            self.drawButtons(x_pos, y_pos, bg_color, text, text_color,
                             button_width, button_height, is_hovered, is_disabled)

        # Draw obstacles and movement controls with hover effects
        obstacles_to_draw = self.obstacles if self.obstacles else []
        self.drawObstaclesButton(obstacles_to_draw, constants.RED)

    def drawShortestPath(self, bot):
        """Draw the shortest path line"""
        half_cell = (constants.GRID_CELL_LENGTH // 2) * constants.SCALING_FACTOR
        path_points = []

        # Add current position
        y = (constants.GRID_LENGTH - constants.GRID_CELL_LENGTH - self.currentPos[1]) // constants.GRID_CELL_LENGTH
        x = self.currentPos[0] // constants.GRID_CELL_LENGTH
        path_points.append((
            (x * constants.GRID_CELL_LENGTH * constants.SCALING_FACTOR) + half_cell,
            (y * constants.GRID_CELL_LENGTH * constants.SCALING_FACTOR) + half_cell
        ))

        # Add obstacle positions
        for obstacle in self.bot.hamiltonian.simple_hamiltonian:
            print(obstacle)
            y = (constants.GRID_LENGTH - constants.GRID_CELL_LENGTH - obstacle.position.y) // constants.GRID_CELL_LENGTH
            x = obstacle.position.x // constants.GRID_CELL_LENGTH
            path_points.append((
                (x * constants.GRID_CELL_LENGTH * constants.SCALING_FACTOR) + half_cell,
                (y * constants.GRID_CELL_LENGTH * constants.SCALING_FACTOR) + half_cell
            ))

        # Draw path lines with animated effect
        for i in range(1, len(path_points)):
            print(f"Drawing line from {path_points[i - 1]} to {path_points[i]}")
            self.updatingDisplay()

            # Draw thicker line with glow effect
            for thickness in range(5, 0, -1):
                alpha = 255 - (5 - thickness) * 40
                color = (*constants.RED, alpha)
                pygame.draw.lines(self.screen, constants.RED, False,
                                  [path_points[i - 1], path_points[i]], thickness)
            pygame.display.update()

    # Add to constants.py
    EXECUTION_TIMEOUT_SECONDS = 300  # 5 minutes timeout

    # Modify the execution loop in simulation.py _handleMouseClick method
    def _handleMouseClick(self, x, y, start_time_ref):
        """Handle mouse click events"""
        # ... existing code ...

        # Start button
        if (button_x < x < button_x + button_width) and (300 < y < 300 + button_height):
            if not self.is_executing:
                print("START BUTTON IS CLICKED!!! I REPEAT, START BUTTON IS CLICKED!!!")
                self.is_executing = True

                try:
                    # Plan the path
                    self.bot.hamiltonian.plan_path()
                    start_time_ref[0] = time.time()
                    self.updateTime(start_time_ref[0], start_time_ref[0])

                    # Execute commands with timeout check
                    for cmd in self.bot.hamiltonian.commands:
                        # Check current elapsed time
                        current_time = time.time()
                        elapsed_time = current_time - start_time_ref[0]

                        # Check for timeout
                        if elapsed_time > constants.EXECUTION_TIMEOUT_SECONDS:
                            print(f"TIMEOUT! Execution stopped after {elapsed_time:.1f} seconds")
                            self.is_executing = False
                            break

                        # Check if user wants to stop (ESC key or window close)
                        for event in pygame.event.get():
                            if event.type == pygame.QUIT:
                                pygame.quit()
                                sys.exit()
                            elif event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                                self.is_executing = False
                                return

                        if not self.is_executing:  # Stop if execution was cancelled
                            break

                        self.parseCmd(cmd, start_time_ref[0])
                        pygame.display.update()

                except Exception as e:
                    print(f"Error during execution: {e}")
                finally:
                    self.is_executing = False

    # You could also add a visual timeout indicator to updateTime method
    def updateTime(self, startTime, currentTime):
        """Update the timer display with timeout indicator"""
        if not startTime:
            return

        # Position timer below the buttons with proper spacing
        timer_x = 630
        timer_y = 480
        timer_width = 140
        timer_height = 35

        # Calculate elapsed and remaining time
        elapsed_time = currentTime - startTime
        remaining_time = max(0, constants.EXECUTION_TIMEOUT_SECONDS - elapsed_time)

        # Main timer display
        rect = pygame.Rect(timer_x, timer_y, timer_width, timer_height)
        pygame.draw.rect(self.screen, constants.DEEP_BLUE, rect)
        pygame.draw.rect(self.screen, constants.DARK_BLUE,
                         pygame.Rect(timer_x, timer_y, timer_width, timer_height // 2))
        pygame.draw.rect(self.screen, constants.WHITE, rect, 2)

        timer_text = f"Time: {elapsed_time:.1f}s"
        timer_font = pygame.font.Font("fonts/Formula1-Regular.ttf", 16)
        text_surface = timer_font.render(timer_text, True, constants.WHITE)
        text_rect = text_surface.get_rect(center=rect.center)
        self.screen.blit(text_surface, text_rect)

        # Timeout display (positioned below main timer with gap)
        timeout_y = timer_y + timer_height + 10  # 10px gap
        timeout_rect = pygame.Rect(timer_x, timeout_y, timer_width, timer_height)

        # Change color based on remaining time
        if remaining_time < 30:  # Last 30 seconds
            timeout_bg_color = constants.RED
            text_color = constants.WHITE
        elif remaining_time < 60:  # Last minute
            timeout_bg_color = constants.YELLOW
            text_color = constants.BLACK
        else:
            timeout_bg_color = constants.DARK_GRAY
            text_color = constants.WHITE

        # Draw timeout background
        pygame.draw.rect(self.screen, timeout_bg_color, timeout_rect)
        pygame.draw.rect(self.screen, constants.WHITE, timeout_rect, 2)

        # Draw timeout text
        timeout_text = f"Timeout: {remaining_time:.0f}s"
        timeout_surface = timer_font.render(timeout_text, True, text_color)
        timeout_text_rect = timeout_surface.get_rect(center=timeout_rect.center)
        self.screen.blit(timeout_surface, timeout_text_rect)

    def updatingDisplay(self, start=None):
        """Update the display with current state"""
        self.clock.tick(5)
        self.drawGrid()

        # Update current position from bot
        current_pos = self.bot.get_current_pos()
        self.currentPos = (
            (constants.GRID_LENGTH - constants.GRID_CELL_LENGTH - current_pos.x) // 10,
            current_pos.y // 10,
            current_pos.direction
        )

        self.drawRobot(self.currentPos, constants.GRID_CELL_LENGTH * constants.SCALING_FACTOR,
                       constants.RED, constants.BLUE, constants.LIGHT_BLUE)
        self.drawObstaclesButton(self.obstacles, constants.RED)

        pygame.time.delay(250)
        self.updateTime(start, time.time())

    def parseCmd(self, cmd, start):
        """Parse and execute a command"""
        grid_size = constants.GRID_LENGTH * constants.SCALING_FACTOR
        cell_size = constants.GRID_CELL_LENGTH * constants.SCALING_FACTOR

        if isinstance(cmd, StraightCommand):
            steps = abs(cmd.dist // 10)
            move_func = self.moveForward if cmd.dist >= 0 else self.moveBackward

            for _ in range(steps):
                move_func(grid_size, cell_size)
                self.updatingDisplay(start)
                pygame.display.update()

        elif isinstance(cmd, TurnCommand):
            self.updatingDisplay(start)

            turn_actions = {
                (TypeOfTurn.MEDIUM, True, False, False): self.turnRight,
                (TypeOfTurn.MEDIUM, False, True, False): self.turnLeft,
                (TypeOfTurn.MEDIUM, True, False, True): self.reverseTurnRight,
                (TypeOfTurn.MEDIUM, False, True, True): self.reverseTurnLeft,
                (TypeOfTurn.SMALL, True, False, False): self.moveNorthEast,
                (TypeOfTurn.SMALL, False, True, False): self.moveNorthWest,
                (TypeOfTurn.SMALL, True, False, True): self.moveSouthEast,
                (TypeOfTurn.SMALL, False, True, True): self.moveSouthWest
            }

            action_key = (cmd.type_of_turn, cmd.right, cmd.left, cmd.reverse)
            action = turn_actions.get(action_key)
            if action:
                action(grid_size, cell_size)

            pygame.display.update()
            self.updatingDisplay(start)

        elif isinstance(cmd, ScanCommand):
            self.updatingDisplay(start)
            self.drawRobot(self.currentPos, cell_size, constants.RED,
                           constants.ORANGE, constants.PINK)
            pygame.display.update()
            self.updatingDisplay(start)
        else:
            print("Unknown command type!")

    def _handleMouseClick(self, x, y, start_time_ref):
        """Handle mouse click events"""
        current_time = pygame.time.get_ticks()

        # Prevent rapid clicking
        if current_time - self.last_click_time < self.click_delay:
            return

        self.last_click_time = current_time

        button_width = 140
        button_height = 45
        button_x = 630
        button_spacing = 60

        # Start button
        if (button_x < x < button_x + button_width) and (300 < y < 300 + button_height):
            if not self.is_executing:
                print("START BUTTON IS CLICKED!!! I REPEAT, START BUTTON IS CLICKED!!!")
                self.is_executing = True

                try:
                    # Plan the path
                    self.bot.hamiltonian.plan_path()
                    start_time_ref[0] = time.time()
                    self.updateTime(start_time_ref[0], start_time_ref[0])

                    # Execute commands with timeout check
                    for cmd in self.bot.hamiltonian.commands:
                        # Check current elapsed time
                        current_time = time.time()
                        elapsed_time = current_time - start_time_ref[0]

                        # Check for timeout
                        if elapsed_time > constants.EXECUTION_TIMEOUT_SECONDS:
                            print(f"TIMEOUT! Execution stopped after {elapsed_time:.1f} seconds")
                            self.is_executing = False
                            break

                        # Check if user wants to stop (ESC key or window close)
                        for event in pygame.event.get():
                            if event.type == pygame.QUIT:
                                pygame.quit()
                                sys.exit()
                            elif event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                                self.is_executing = False
                                return

                        if not self.is_executing:  # Stop if execution was cancelled
                            break

                        self.parseCmd(cmd, start_time_ref[0])
                        pygame.display.update()

                except Exception as e:
                    print(f"Error during execution: {e}")
                finally:
                    self.is_executing = False
            else:
                print("Already executing! Please wait or press RESET to stop.")

        # Reset button
        elif (button_x < x < button_x + button_width) and (
                300 + button_spacing < y < 300 + button_spacing + button_height):
            print("RESET BUTTON CLICKED!")
            self.is_executing = False  # Stop any current execution

            # Clear the old robot from display first
            if hasattr(self, 'currentPos'):
                self.drawRobot(self.currentPos,
                               constants.GRID_CELL_LENGTH * constants.SCALING_FACTOR,
                               constants.GREY, constants.GREY, constants.GREY)

            # Reset everything
            self.reset(self.bot)
            start_time_ref[0] = None  # Reset timer

            print("Reset complete!")

        # Movement area
        elif (650 < x < 720 + constants.GRID_CELL_LENGTH * constants.SCALING_FACTOR and
              115 < y < 185 + constants.GRID_CELL_LENGTH * constants.SCALING_FACTOR):
            if not self.is_executing:  # Only allow manual movement when not executing
                self.movement(x, y, constants.GRID_CELL_LENGTH * constants.SCALING_FACTOR, 25)

        # Draw shortest path button
        elif (button_x < x < button_x + button_width) and (
                300 + button_spacing * 2 < y < 300 + button_spacing * 2 + button_height):
            if not self.is_executing:  # Only allow when not executing
                self.drawShortestPath(self.bot)

    def _handleKeyDown(self, event):
        """Handle keyboard input"""
        # Add ESC key to stop execution
        if event.key == pygame.K_ESCAPE:
            if self.is_executing:
                print("Execution stopped by user (ESC)")
                self.is_executing = False
            return

        # Only allow manual movement when not executing
        if self.is_executing:
            return

        keys = pygame.key.get_pressed()
        grid_size = constants.GRID_LENGTH * constants.SCALING_FACTOR
        cell_size = constants.GRID_CELL_LENGTH * constants.SCALING_FACTOR

        key_actions = {
            pygame.K_e: self.moveNorthEast,
            pygame.K_q: self.moveNorthWest,
            pygame.K_d: self.moveSouthEast,
            pygame.K_a: self.moveSouthWest
        }

        if keys[pygame.K_UP]:
            if keys[pygame.K_RIGHT]:
                self.turnRight(grid_size, cell_size)
            elif keys[pygame.K_LEFT]:
                self.turnLeft(grid_size, cell_size)
            else:
                self.moveForward(grid_size, cell_size)
        elif keys[pygame.K_DOWN]:
            if keys[pygame.K_RIGHT]:
                self.reverseTurnRight(grid_size, cell_size)
            elif keys[pygame.K_LEFT]:
                self.reverseTurnLeft(grid_size, cell_size)
            else:
                self.moveBackward(grid_size, cell_size)
        elif event.key in key_actions:
            key_actions[event.key](grid_size, cell_size)

    def runSimulation(self, bot):
        """Main simulation loop"""
        self.bot = deepcopy(bot)
        self.clock = pygame.time.Clock()
        self.obstacles = self.bot.hamiltonian.grid.obstacles
        start_time_ref = [None]  # Use list for mutable reference

        while True:
            self.updatingDisplay()
            x, y = pygame.mouse.get_pos()

            # Store last mouse position for smooth animations
            self.last_mouse_pos = (x, y)

            self.draw(x, y)

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
                elif event.type == pygame.MOUSEBUTTONDOWN:
                    self._handleMouseClick(x, y, start_time_ref)
                elif event.type == pygame.KEYDOWN:
                    self._handleKeyDown(event)
                elif event.type == pygame.VIDEORESIZE:
                    self.screen = pygame.display.set_mode((event.w, event.h), pygame.RESIZABLE)
                    self.screen.fill(constants.DEEP_BLUE)

            pygame.display.update()