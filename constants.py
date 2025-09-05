import socket

from misc.direction import Direction

# =============================================================================
# DISPLAY & SIMULATION SETTINGS
# =============================================================================

# PyGame display settings
SCALING_FACTOR = 3
FRAMES = 50
WINDOW_SIZE = 800, 650
RUN_SIMULATION = True  # Set true for simulation mode

# =============================================================================
# NETWORK CONNECTION SETTINGS
# =============================================================================

# Connection to Raspberry Pi
RPI_HOST: str = "192.168.47.1"
RPI_PORT: int = 6000

# Connection to PC
PC_HOST: str = socket.gethostbyname(socket.gethostname())
PC_PORT: int = 4161

# =============================================================================
# ROBOT CONFIGURATION
# =============================================================================

# Physical attributes
ROBOT_LENGTH = 20
ROBOT_TURN_RADIUS = 30
ROBOT_SPEED_PER_SECOND = 100  # should be 33.3
ROBOT_SAFETY_DISTANCE = 10

# Derived robot parameters
# Please read briefing notes from Imperial
ROBOT_S_FACTOR = ROBOT_LENGTH / ROBOT_TURN_RADIUS

# Time provided for scanning an obstacle image in seconds
ROBOT_SCAN_TIME = 0.25

EXECUTION_TIMEOUT_SECONDS = 20

# =============================================================================
# GRID CONFIGURATION
# =============================================================================

# Main grid settings
GRID_LENGTH = 200
GRID_CELL_LENGTH = 10
GRID_START_BOX_LENGTH = 30
NO_OF_GRID_CELLS_PER_SIDE = GRID_LENGTH // GRID_CELL_LENGTH
OFFSET = GRID_CELL_LENGTH // 2

# Task 2 grid settings (30x10 grid)
TASK2_LENGTH = 230
TASK2_WIDTH = 150
TASK2_SCALING_FACTOR = 3

# =============================================================================
# ALGORITHM CONFIGURATION
# =============================================================================

# Algorithm types
MODIFIED_A_STAR = 0
WEIGHTED_A_STAR = 1

# Path finding parameters
PATH_TURN_COST = 999 * ROBOT_SPEED_PER_SECOND * ROBOT_TURN_RADIUS
SPOT_TURN_COST = 999 * ROBOT_SPEED_PER_SECOND * ROBOT_TURN_RADIUS

# NOTE: Higher number == Lower Granularity == Faster Checking.
# Must be an integer more than 0! Number higher than 3 not recommended.
PATH_TURN_CHECK_GRANULARITY = 1

# =============================================================================
# OBSTACLE CONFIGURATION
# =============================================================================

# Obstacle dimensions and safety margins
OBSTACLE_LENGTH = 10
OBSTACLE_SAFETY_WIDTH = 10
OBSTACLE_SAFETY_MULTIPLIER = 3
# Denotes the offset from the obstacle to the target position
OBSTACLE_SAFETY_OFFSET = OBSTACLE_SAFETY_WIDTH * OBSTACLE_SAFETY_MULTIPLIER

# =============================================================================
# UI COMPONENTS
# =============================================================================

# Button dimensions
BUTTON_LENGTH = 120
BUTTON_WIDTH = 30

# =============================================================================
# SIMULATION SCENARIOS
# =============================================================================

# Task 1 Simulator Config - obstacle positions [x, y, direction]
SIMULATOR_OBSTACLES = [
    [110, 0, Direction.RIGHT],    # or move this to the left gives enough clearance
    [190, 40, Direction.LEFT],    # removing this creates enough clearance for the robot to pass
    [190, 100, Direction.LEFT],
    [70, 70, Direction.LEFT],
    [70, 170, Direction.BOTTOM],
    [0, 140, Direction.BOTTOM],
    [140, 180, Direction.LEFT],
    [110, 90, Direction.RIGHT]
]

# Task 2 Simulator Config
DISTANCE1 = 60   # First obstacle distance from robot (60-150)
DISTANCE2 = 60   # Second obstacle distance from first obstacle (60-150)
OBSTACLE1 = "L"  # First obstacle direction (L/R)
OBSTACLE2 = "L"  # Second obstacle direction (L/R)

# =============================================================================
# COLOR DEFINITIONS
# =============================================================================

# Primary colors
RED = (242, 0, 0)
GREEN = (84, 238, 161)
GREEN_OLD = (26, 255, 0)
BLUE = (6, 46, 250)
YELLOW = (255, 255, 18)

# Grayscale colors
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
GREY = (163, 163, 194)
DARK_GRAY = (169, 169, 169)
DARKER_GRAY = (80, 80, 100)
SILVER = (192, 192, 192)
PLATINUM = (229, 228, 226)

# Specialized colors
DARK_GREEN = (0, 80, 0)
DARK_YELLOW = (236, 183, 83)
LIGHT_YELLOW = (255, 255, 153)
GOLD = (245, 216, 101)

PINK = (255, 51, 255)
PURPLE = (153, 51, 255)
ORANGE = (255, 154, 0)

DARK_BLUE = (51, 51, 255)
DEEP_BLUE = (20, 82, 108)
LIGHT_BLUE = (0, 205, 255)

# =============================================================================
# ROBOT TURNING COORDINATES
# =============================================================================

# Small turns - Forward direction
# Format: TYPE_OF_TURN ___ DIRECTION_TO_TURN ___ ROBOT_INITIAL_DIRECTION ___ FWD/REV

# Small left turns (forward)
TURN_SMALL_LEFT_TOP_FORWARD = (-10, 40)
TURN_SMALL_LEFT_RIGHT_FORWARD = (40, 10)
TURN_SMALL_LEFT_BOTTOM_FORWARD = (10, -40)
TURN_SMALL_LEFT_LEFT_FORWARD = (-40, -10)

# Small right turns (forward)
TURN_SMALL_RIGHT_TOP_FORWARD = (10, 40)
TURN_SMALL_RIGHT_RIGHT_FORWARD = (40, -10)
TURN_SMALL_RIGHT_BOTTOM_FORWARD = (-10, -40)
TURN_SMALL_RIGHT_LEFT_FORWARD = (-40, 10)

# Medium left turns (forward)
TURN_MED_LEFT_TOP_FORWARD = (-30, 20)
TURN_MED_LEFT_RIGHT_FORWARD = (20, 30)
TURN_MED_LEFT_BOTTOM_FORWARD = (30, -20)
TURN_MED_LEFT_LEFT_FORWARD = (-20, -30)

# Medium right turns (forward)
TURN_MED_RIGHT_TOP_FORWARD = (30, 20)
TURN_MED_RIGHT_RIGHT_FORWARD = (20, -30)
TURN_MED_RIGHT_BOTTOM_FORWARD = (-30, -20)
TURN_MED_RIGHT_LEFT_FORWARD = (-20, 30)

# Small left turns (reverse)
TURN_SMALL_LEFT_TOP_REVERSE = (-10, -40)
TURN_SMALL_LEFT_RIGHT_REVERSE = (-40, 10)
TURN_SMALL_LEFT_BOTTOM_REVERSE = (10, 40)
TURN_SMALL_LEFT_LEFT_REVERSE = (40, -10)

# Small right turns (reverse)
TURN_SMALL_RIGHT_TOP_REVERSE = (10, -40)
TURN_SMALL_RIGHT_RIGHT_REVERSE = (-40, -10)
TURN_SMALL_RIGHT_BOTTOM_REVERSE = (-10, 40)
TURN_SMALL_RIGHT_LEFT_REVERSE = (40, 10)

# Medium left turns (reverse)
TURN_MED_LEFT_TOP_REVERSE = (-20, -30)
TURN_MED_LEFT_RIGHT_REVERSE = (-30, 20)
TURN_MED_LEFT_BOTTOM_REVERSE = (20, 30)
TURN_MED_LEFT_LEFT_REVERSE = (30, -20)

# Medium right turns (reverse)
TURN_MED_RIGHT_TOP_REVERSE = (20, -30)
TURN_MED_RIGHT_RIGHT_REVERSE = (-30, -20)
TURN_MED_RIGHT_BOTTOM_REVERSE = (-20, 30)
TURN_MED_RIGHT_LEFT_REVERSE = (30, 20)