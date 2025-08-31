from abc import ABC, abstractmethod
from typing import List

from grid.grid import Grid
from grid.obstacle import Obstacle
from misc.direction import Direction
from robot.robot import Robot


class AlgoApp(ABC):
    """Abstract base class for algorithm applications."""

    def __init__(self, obstacles: List[Obstacle]) -> None:
        self.grid = Grid(obstacles)
        self.robot = Robot(self.grid)
        self.direction = Direction.TOP
        self.obstacles = obstacles

    @abstractmethod
    def initialize(self) -> None:
        """Initialize the algorithm application."""
        pass

    @abstractmethod
    def execute(self) -> None:
        """Execute the main algorithm logic."""
        pass


class AlgoMinimal(AlgoApp):
    """
    Minimal algorithm application that calculates a Hamiltonian path
    and sends commands to the robot.
    """

    def __init__(self, obstacles: List[Obstacle]) -> None:
        super().__init__(obstacles)

    def initialize(self) -> None:
        """Initialize the minimal algorithm (no additional setup required)."""
        pass

    def execute(self) -> None:
        """Calculate and execute the Hamiltonian path."""
        print("Calculating path...")
        self.robot.hamiltonian.plan_path()
        print("Path calculation complete!")