# Cleaned

import socket
import sys
import time
from typing import List, Union

import constants
from commands.go_straight_command import StraightCommand
from commands.scan_obstacle_command import ScanCommand
from connection_to_rpi.rpi_client import RPiClient
from grid.grid import Grid
from grid.obstacle import Obstacle
from misc.direction import Direction
from misc.positioning import Position
from pygame_app import AlgoMinimal
from robot.robot import Robot
from simulation import Simulation


class Main:
    """Main controller class for the robotics algorithm system."""

    def __init__(self):
        self.client = None
        self.commands = None
        self.count = 0

    def parse_obstacle_data(self, data: List[List]) -> List[Obstacle]:
        """
        Parse obstacle data from the format [[x, y, orient, index], ...] into Obstacle objects.

        Args:
            data: List of obstacle parameters [x, y, orientation, index]

        Returns:
            List of Obstacle objects
        """
        obstacles = []
        for obstacle_params in data:
            if len(obstacle_params) < 4:
                continue

            obstacle = Obstacle(
                Position(
                    obstacle_params[0],
                    obstacle_params[1],
                    Direction(obstacle_params[2]),
                ),
                obstacle_params[3],
            )
            obstacles.append(obstacle)
        return obstacles

    def run_simulator(self):
        """Run the simulation mode for testing."""
        obstacles = []

        for i, (x, y, direction) in enumerate(constants.SIMULATOR_OBSTACLES):
            position = Position(x, y, direction)
            obstacle = Obstacle(position, i)
            obstacles.append(obstacle)

        grid = Grid(obstacles)
        bot = Robot(grid)
        sim = Simulation()
        sim.runSimulation(bot)

    def _connect_to_rpi(self):
        """Establish connection to the Raspberry Pi."""
        if self.client is None:
            print(f"Attempting to connect to {constants.RPI_HOST}:{constants.RPI_PORT}")
            self.client = RPiClient(constants.RPI_HOST, constants.RPI_PORT)

            # Wait to connect to RPi
            while True:
                try:
                    self.client.connect()
                    break
                except OSError:
                    pass
                except KeyboardInterrupt:
                    self.client.close()
                    sys.exit(1)
            print("Connected to RPi!\n")

    def _parse_rpi_message(self, message: str) -> List[List[int]]:
        """
        Parse message from RPI in format: ALG:x,y,direction,id;x,y,direction,id;...

        Args:
            message: Raw message string from RPI

        Returns:
            Parsed obstacle data
        """
        # Remove ALG: prefix and split by semicolon
        data = message[4:].split(";")[:-1]  # Last element is empty string
        parsed_obstacles = []

        for obstacle_str in data:
            parts = obstacle_str.split(",")
            if len(parts) != 4:
                continue

            # Convert coordinates (multiply by 10 for correct scale)
            x = int(parts[0]) * 10
            y = int(parts[1]) * 10

            # Convert direction
            direction_map = {"N": 90, "S": -90, "E": 0, "W": 180}
            direction = direction_map.get(parts[2], 0)

            obstacle_id = int(parts[3])
            parsed_obstacles.append([x, y, direction, obstacle_id])

        return parsed_obstacles

    def run_minimal(self, also_run_simulator: bool):
        """
        Run the minimal mode - connect to RPI and process commands.

        Args:
            also_run_simulator: Whether to run simulator alongside
        """
        self._connect_to_rpi()

        # Wait for message from RPI
        print("Waiting to receive data from RPi...")
        raw_data = self.client.receive_message()
        print("Decoding data from RPi:")

        decoded_data = raw_data.decode("utf-8")
        print(f"Received: {decoded_data}")

        if decoded_data.startswith("ALG:"):
            obstacle_data = self._parse_rpi_message(decoded_data)
            print(f"Parsed obstacle data: {obstacle_data}")
            self._process_obstacle_data(obstacle_data, also_run_simulator)
        else:
            self._process_string_command(decoded_data)

    def _process_obstacle_data(self, data: List[List[int]], also_run_simulator: bool):
        """Process obstacle data and execute algorithm."""
        obstacles = self.parse_obstacle_data(data)
        app = AlgoMinimal(obstacles)
        app.init()

        if also_run_simulator:
            app.simulate()
        else:
            app.execute()

        # Get path planning results
        obs_priority = app.robot.hamiltonian.get_simple_hamiltonian()

        # Convert to commands and send to RPI
        print("Sending list of commands to RPi...")
        self.commands = app.robot.convert_all_commands()
        print(f"Commands to send: {self.commands}")

        if self.commands:
            self.client.send_message(self.commands)
        else:
            print("ERROR!! NO COMMANDS TO SEND TO RPI")

    def _process_string_command(self, command: str):
        """Process string commands from RPI."""
        print(f"Processing string command: {command}")
        command_parts = command.split(',')

        try:
            # Handle NONE command with obstacle ID
            if len(command_parts) >= 2:
                obstacle_id = int(command_parts[1])
                commands = [
                    StraightCommand(-10).convert_to_message(),
                    ScanCommand(0, obstacle_id).convert_to_message(),
                    StraightCommand(10).convert_to_message(),
                ]
                self.client.send_message(commands)
        except (IndexError, ValueError) as e:
            print(f"Error processing command: {e}")

    def run_rpi(self):
        """Main loop for RPI communication."""
        # Test obstacle configurations for different scenarios
        test_scenarios = {
            'scenario_a': "ALG:2,17,S,0;16,17,W,1;10,11,S,2;4,6,N,3;9,2,E,4;17,5,W,5;",
            'scenario_b': "ALG:4,18,E,0;18,18,S,1;13,13,E,2;15,1,N,3;9,2,W,4;0,14,E,5;7,7,N,6;",
            'scenario_c': "ALG:2,9,N,0;0,17,E,1;14,15,S,2;6,2,N,3;19,4,W,4;10,5,W,5;17,19,S,6;9,18,W,7;",
            'week8_test': "ALG:16,1,L,0;8,5,R,1;6,12,N,2;2,18,S,3;15,16,S,4;",
            'simple_test': "ALG:3,11,E,0;7,14,S,1;9,5,N,2;",
        }

        while True:
            self.run_minimal(constants.RUN_SIMULATION)
            time.sleep(5)

    @staticmethod
    def test_connection():
        """Test connection to RPI server."""
        print("Starting connection test")
        try:
            server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            server.connect(("192.168.47.1", 6000))
            print("Connected successfully")

            server.send("12345".encode('utf-8'))
            response = server.recv(1024)
            print(f"Response: {response.decode('utf-8')}")
            server.close()

        except Exception as e:
            print(f"Connection test failed: {e}")


def initialize():
    """Initialize and run the main RPI controller."""
    algo = Main()
    algo.run_rpi()


def run_simulation():
    """Run the virtual simulator."""
    algo = Main()
    algo.run_simulator()


if __name__ == "__main__":
    # Uncomment the desired mode:

    # Test connection with RPI
    # Main.test_connection()

    # Run virtual simulator
    run_simulation()

    # Run on RPI
    # initialize()