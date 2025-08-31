import constants
from grid.grid import Grid
from grid.obstacle import Obstacle
from misc.direction import Direction
from misc.positioning import Position
from robot.robot import Robot
from TaskTwoSimulation import Simulation


def create_obstacles():
    """Create and return a list of obstacles for the simulation."""
    # Define obstacle positions and orientations
    obstacle_configs = [
        [70, constants.DISTANCE1, Direction.BOTTOM],
        [70, constants.DISTANCE1 + constants.DISTANCE2 + constants.GRID_CELL_LENGTH, Direction.BOTTOM],
    ]

    obstacles = []
    for obstacle_id, (x, y, direction) in enumerate(obstacle_configs):
        position = Position(x, y, direction)
        obstacle = Obstacle(position, obstacle_id)
        obstacles.append(obstacle)

    return obstacles


def setup_robot_initial_position():
    """Calculate and return the robot's initial position."""
    robot_x = 70
    robot_y = constants.TASK2_LENGTH - constants.GRID_CELL_LENGTH - 20

    # Convert to grid coordinates
    grid_row = robot_y // 10
    grid_col = robot_x // 10

    return grid_row, grid_col


def main():
    """Main simulation setup and execution."""
    # Create grid with obstacles
    obstacles = create_obstacles()
    grid = Grid(obstacles)

    # Initialize robot
    robot = Robot(grid)
    initial_direction = robot.get_current_pos().direction

    # Set robot's starting position
    grid_row, grid_col = setup_robot_initial_position()
    current_position = (grid_row, grid_col, initial_direction)
    print(f"CURRENT POS: {current_position}")

    robot.set_position_task2(grid_row, grid_col, initial_direction)

    # Prepare obstacle directions for simulation
    obstacle_directions = [
        constants.OBSTACLE1,
        constants.OBSTACLE2
    ]

    # Run simulation
    simulation = Simulation(obstacle_directions)
    simulation.runTask2Simulation(robot)


if __name__ == "__main__":
    main()