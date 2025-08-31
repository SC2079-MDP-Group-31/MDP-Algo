import random
from collections import deque
from typing import Tuple, List, Optional
from dataclasses import dataclass
import itertools

import constants
from commands.go_straight_command import StraightCommand
from commands.scan_obstacle_command import ScanCommand
from grid.grid import Grid
from grid.obstacle import Obstacle
from misc.direction import Direction
from misc.positioning import Position
from path_finding.modified_a_star import ModifiedAStar
from path_finding.weighted_a_star import WeightedAStar


@dataclass
class PathMetrics:
    """Metrics for evaluating path quality"""
    total_distance: float
    direction_changes: int
    complexity_score: float


class Hamiltonian:
    """Optimized Hamiltonian path planner for robot obstacle navigation"""

    # Configuration constants
    DISTANCE_SCALE_FACTOR = 10
    DIRECTION_CHANGE_WEIGHT = 5
    DIRECTION_DEGREE_UNIT = 90
    MAX_OBSTACLES_FOR_BRUTE_FORCE = 8
    GENETIC_POPULATION_SIZE = 100
    GENETIC_GENERATIONS = 500
    GENETIC_MUTATION_RATE = 0.02
    NEAREST_NEIGHBOR_ATTEMPTS = 5
    MAX_PATH_ATTEMPTS = 3

    def __init__(self, robot, grid: Grid):
        """
        Initialize Hamiltonian path planner.

        Args:
            robot: Robot object with position information
            grid: Grid containing obstacles to visit
        """
        self.robot = robot
        self.grid = grid
        self.simple_hamiltonian = tuple()
        self.commands = deque()

        # Precompute distance matrix for efficiency
        self._distance_matrix = {}
        self._obstacles_list = list(self.grid.obstacles)

        if self._obstacles_list:
            self._precompute_distances()

    def _safe_copy_position(self, position) -> Position:
        """Safely copy a position object."""
        if hasattr(position, 'copy'):
            return position.copy()
        elif hasattr(position, '__dict__'):
            # Create new instance with same attributes
            new_pos = type(position).__new__(type(position))
            for attr, value in position.__dict__.items():
                setattr(new_pos, attr, value)
            return new_pos
        else:
            # Fallback: assume it's immutable
            return position

    def _get_position_coordinates(self, position) -> Tuple[float, float]:
        """Extract x, y coordinates from position object."""
        if hasattr(position, 'x') and hasattr(position, 'y'):
            return position.x, position.y
        else:
            raise ValueError(f"Position object {position} missing x or y attributes")

    def _get_position_direction(self, position) -> Optional[Direction]:
        """Extract direction from position object if available."""
        return getattr(position, 'direction', None)

    def _precompute_distances(self):
        """Precompute distances between all obstacle pairs and from start position"""
        if not self._obstacles_list:
            return

        start_pos = self.robot.pos

        # Distance from start to each obstacle
        for i, obstacle in enumerate(self._obstacles_list):
            try:
                target_pos = self._get_obstacle_target_position(obstacle)
                if target_pos:
                    key = ('start', i)
                    self._distance_matrix[key] = self._calculate_weighted_distance(
                        start_pos, target_pos, is_first=True
                    )
            except Exception as e:
                print(f"Warning: Could not compute distance to obstacle {i}: {e}")
                # Set a default high distance
                self._distance_matrix[('start', i)] = float('inf')

        # Distance between each pair of obstacles
        for i, obs1 in enumerate(self._obstacles_list):
            for j, obs2 in enumerate(self._obstacles_list):
                if i != j:
                    try:
                        target1 = self._get_obstacle_target_position(obs1)
                        target2 = self._get_obstacle_target_position(obs2)

                        if target1 and target2:
                            key = (i, j)
                            self._distance_matrix[key] = self._calculate_weighted_distance(
                                target1, target2, is_first=False
                            )
                    except Exception as e:
                        print(f"Warning: Could not compute distance between obstacles {i}-{j}: {e}")
                        # Set a default high distance
                        self._distance_matrix[(i, j)] = float('inf')

    def _get_obstacle_target_position(self, obstacle: Obstacle):
        """Get target position from obstacle, handling different method names."""
        # Try different method names for compatibility
        methods_to_try = ['target_position', 'get_robot_target_pos']

        for method_name in methods_to_try:
            if hasattr(obstacle, method_name):
                attr_or_method = getattr(obstacle, method_name)
                if callable(attr_or_method):
                    return attr_or_method()
                else:
                    return attr_or_method

        print(f"Warning: Could not find target position for obstacle {obstacle}")
        return None

    def _calculate_weighted_distance(self, source_pos, dest_pos, is_first: bool = False) -> float:
        """Calculate weighted distance between two positions with error handling."""
        try:
            # Get coordinates
            sx, sy = self._get_position_coordinates(source_pos)
            dx, dy = self._get_position_coordinates(dest_pos)

            # Calculate grid distance using Chebyshev distance (diagonal movement allowed)
            abs_x_diff = abs(sx - dx)
            abs_y_diff = abs(sy - dy)

            diag_distance = min(abs_x_diff, abs_y_diff)
            remaining_x = abs_x_diff - diag_distance
            remaining_y = abs_y_diff - diag_distance

            grid_distance = (diag_distance + remaining_x + remaining_y) / self.DISTANCE_SCALE_FACTOR

            # Calculate direction change penalty
            direction_penalty = 0
            source_dir = self._get_position_direction(source_pos)
            dest_dir = self._get_position_direction(dest_pos)

            if source_dir and dest_dir:
                direction_diff = abs(source_dir.value - dest_dir.value)
                # Handle wrap-around (e.g., 350° to 10° should be 20°, not 340°)
                if direction_diff > 180:
                    direction_diff = 360 - direction_diff
                direction_penalty = (direction_diff / self.DIRECTION_DEGREE_UNIT) * self.DIRECTION_CHANGE_WEIGHT

            return grid_distance + direction_penalty

        except Exception as e:
            print(f"Error calculating distance between {source_pos} and {dest_pos}: {e}")
            return float('inf')

    def _get_path_distance(self, path: List[int]) -> float:
        """Calculate total distance for a given path using precomputed distances"""
        if not path:
            return 0.0

        total_distance = 0

        # Distance from start to first obstacle
        start_key = ('start', path[0])
        if start_key in self._distance_matrix:
            total_distance += self._distance_matrix[start_key]
        else:
            return float('inf')  # Invalid path

        # Distance between consecutive obstacles
        for i in range(len(path) - 1):
            key = (path[i], path[i + 1])
            if key in self._distance_matrix:
                total_distance += self._distance_matrix[key]
            else:
                return float('inf')  # Invalid path

        return total_distance

    def _nearest_neighbor_heuristic(self) -> List[int]:
        """Fast nearest neighbor heuristic for TSP"""
        if not self._obstacles_list:
            return []

        obstacles_indices = list(range(len(self._obstacles_list)))
        best_path = None
        best_distance = float('inf')

        # Try multiple starting points for better results
        attempts = min(self.NEAREST_NEIGHBOR_ATTEMPTS, len(obstacles_indices))

        for start_idx in range(attempts):
            if start_idx >= len(obstacles_indices):
                break

            path = []
            unvisited = set(obstacles_indices)
            current = obstacles_indices[start_idx]
            unvisited.remove(current)
            path.append(current)

            while unvisited:
                # Find nearest unvisited obstacle
                min_distance = float('inf')
                nearest = None

                for candidate in unvisited:
                    key = (current, candidate)
                    if key in self._distance_matrix:
                        distance = self._distance_matrix[key]
                        if distance < min_distance:
                            min_distance = distance
                            nearest = candidate

                if nearest is None:
                    break  # No valid connections

                path.append(nearest)
                unvisited.remove(nearest)
                current = nearest

            # Only consider complete paths
            if len(path) == len(obstacles_indices):
                distance = self._get_path_distance(path)
                if distance < best_distance:
                    best_distance = distance
                    best_path = path

        return best_path if best_path else obstacles_indices

    def _genetic_algorithm_tsp(self) -> List[int]:
        """Genetic algorithm for larger TSP instances"""
        obstacles_indices = list(range(len(self._obstacles_list)))

        if len(obstacles_indices) <= 2:
            return obstacles_indices

        def create_individual():
            individual = obstacles_indices.copy()
            random.shuffle(individual)
            return individual

        def fitness(individual):
            distance = self._get_path_distance(individual)
            return 1.0 / (1.0 + distance) if distance != float('inf') else 0.0

        def crossover(parent1, parent2):
            """Order crossover (OX)"""
            size = len(parent1)
            if size < 2:
                return parent1.copy()

            start, end = sorted(random.sample(range(size), 2))
            child = [-1] * size
            child[start:end] = parent1[start:end]

            pointer = end % size
            for item in parent2[end:] + parent2[:end]:
                if item not in child:
                    while child[pointer] != -1:
                        pointer = (pointer + 1) % size
                    child[pointer] = item

            return child

        def mutate(individual):
            if random.random() < self.GENETIC_MUTATION_RATE and len(individual) >= 2:
                i, j = random.sample(range(len(individual)), 2)
                individual[i], individual[j] = individual[j], individual[i]

        # Initialize population
        population = [create_individual() for _ in range(self.GENETIC_POPULATION_SIZE)]

        # Add nearest neighbor solution to population if available
        nn_solution = self._nearest_neighbor_heuristic()
        if nn_solution and len(population) > 0:
            population[0] = nn_solution

        for generation in range(self.GENETIC_GENERATIONS):
            # Evaluate fitness
            fitness_scores = []
            for individual in population:
                score = fitness(individual)
                fitness_scores.append((individual, score))

            fitness_scores.sort(key=lambda x: x[1], reverse=True)

            # Selection (top 50%)
            survivors = [individual for individual, _ in fitness_scores[:len(population) // 2]]

            if not survivors:  # Fallback if no valid solutions
                return obstacles_indices

            # Generate new population
            new_population = survivors.copy()
            while len(new_population) < self.GENETIC_POPULATION_SIZE:
                parent1, parent2 = random.choices(survivors, k=2)
                child = crossover(parent1, parent2)
                mutate(child)
                new_population.append(child)

            population = new_population

        # Return best solution
        if population:
            best_individual = max(population, key=fitness)
            return best_individual
        else:
            return obstacles_indices

    def _optimize_with_2opt(self, path: List[int]) -> List[int]:
        """Apply 2-opt local optimization"""
        if len(path) < 3:
            return path.copy()

        def reverse_segment(tour, i, j):
            """Reverse segment between indices i and j"""
            new_tour = tour.copy()
            new_tour[i:j + 1] = list(reversed(new_tour[i:j + 1]))
            return new_tour

        best_path = path.copy()
        best_distance = self._get_path_distance(best_path)

        if best_distance == float('inf'):
            return path.copy()

        improved = True
        max_iterations = 100  # Prevent infinite loops

        iteration = 0
        while improved and iteration < max_iterations:
            improved = False
            iteration += 1

            for i in range(len(path)):
                for j in range(i + 2, len(path)):
                    new_path = reverse_segment(best_path, i, j)
                    new_distance = self._get_path_distance(new_path)

                    if new_distance < best_distance:
                        best_path = new_path
                        best_distance = new_distance
                        improved = True
                        break
                if improved:
                    break

        return best_path

    def compute_optimal_hamiltonian_path(self) -> Tuple[Obstacle, ...]:
        """
        Compute the optimal Hamiltonian path using appropriate algorithm based on problem size
        """
        if not self._obstacles_list:
            print("No obstacles to compute path for.")
            return tuple()

        num_obstacles = len(self._obstacles_list)
        print(f"Computing optimal path for {num_obstacles} obstacles...")

        try:
            if num_obstacles <= self.MAX_OBSTACLES_FOR_BRUTE_FORCE:
                # Use brute force for small instances
                print("Using brute force approach...")
                obstacle_indices = list(range(num_obstacles))
                perms = itertools.permutations(obstacle_indices)
                best_path_indices = min(perms, key=self._get_path_distance)
            else:
                # Use genetic algorithm for larger instances
                print("Using genetic algorithm approach...")
                best_path_indices = self._genetic_algorithm_tsp()

                # Apply 2-opt optimization
                print("Applying 2-opt optimization...")
                best_path_indices = self._optimize_with_2opt(best_path_indices)

        except Exception as e:
            print(f"Error during optimization: {e}")
            # Fallback to simple ordering
            best_path_indices = list(range(num_obstacles))

        # Convert indices to obstacle objects
        optimal_path = tuple(self._obstacles_list[i] for i in best_path_indices)

        print("Optimal path found:")
        for i, obstacle in enumerate(optimal_path):
            print(f"  {i + 1}. {obstacle}")

        total_distance = self._get_path_distance(list(best_path_indices))
        print(f"Total estimated cost: {total_distance:.2f}")

        return optimal_path

    def get_simple_hamiltonian(self) -> Tuple[Obstacle, ...]:
        """Get the computed Hamiltonian path"""
        return self.simple_hamiltonian

    def _compress_commands(self):
        """Compress consecutive straight line commands"""
        print("Compressing commands...", end=" ")

        if not self.commands:
            print("No commands to compress.")
            return

        compressed = deque()
        current_command = None

        try:
            current_command = self.commands.popleft()
        except IndexError:
            print("No commands to compress.")
            return

        while self.commands:
            try:
                next_command = self.commands.popleft()

                if (isinstance(current_command, StraightCommand) and
                        isinstance(next_command, StraightCommand)):
                    # Merge straight commands
                    current_command = StraightCommand(
                        current_command.dist + next_command.dist
                    )
                else:
                    compressed.append(current_command)
                    current_command = next_command
            except Exception as e:
                print(f"Error compressing commands: {e}")
                break

        # Add the last command
        if current_command:
            compressed.append(current_command)

        self.commands = compressed
        print("Done!")

    def _find_path_with_fallback(self, curr_pos, target_pos, obstacle) -> Optional[Position]:
        """Find path with multiple fallback strategies"""
        algorithms = [
            (constants.WEIGHTED_A_STAR, "Weighted A*"),
            (constants.MODIFIED_A_STAR, "Modified A*")
        ]

        for rerun in range(self.MAX_PATH_ATTEMPTS):
            for mode, name in algorithms:
                try:
                    print(f"  Trying {name} (attempt {rerun + 1})...")

                    if mode == constants.MODIFIED_A_STAR:
                        result, commands = ModifiedAStar(
                            self.grid, self, curr_pos, target_pos, rerun
                        ).start_astar(True)
                    else:
                        result, commands = WeightedAStar(
                            self.grid, self, curr_pos, target_pos, rerun
                        ).start_astar(True)

                    if result is not None:
                        print(f"  Path found with {name}!")
                        return result

                except Exception as e:
                    print(f"  Error with {name}: {e}")
                    continue

        print(f"  No path found to {obstacle} after all attempts!")
        return None

    def plan_path(self):
        """Plan the complete path with optimized algorithms"""
        print("-" * 50)
        print("STARTING OPTIMIZED PATH COMPUTATION...")

        try:
            # Compute optimal Hamiltonian path
            self.simple_hamiltonian = self.compute_optimal_hamiltonian_path()

            if not self.simple_hamiltonian:
                print("No obstacles to visit!")
                return

            print("\nPlanning detailed paths...")
            print("-" * 30)

            # Plan path to each obstacle
            current_pos = self._safe_copy_position(self.robot.pos)
            successful_paths = 0

            for i, obstacle in enumerate(self.simple_hamiltonian):
                try:
                    target_pos = self._get_obstacle_target_position(obstacle)
                    if target_pos is None:
                        print(f"  WARNING: Could not get target position for obstacle {obstacle}")
                        continue

                    print(f"Planning path {i + 1}/{len(self.simple_hamiltonian)}")
                    print(f"  From: {current_pos}")
                    print(f"  To: {target_pos} (Obstacle: {obstacle})")

                    result_pos = self._find_path_with_fallback(current_pos, target_pos, obstacle)

                    if result_pos is not None:
                        current_pos = result_pos

                        # Get obstacle index safely
                        obstacle_index = getattr(obstacle, 'index', i)
                        self.commands.append(
                            ScanCommand(constants.ROBOT_SCAN_TIME, obstacle_index)
                        )
                        successful_paths += 1
                    else:
                        print(f"  WARNING: Skipping obstacle {obstacle} - no path found!")

                except Exception as e:
                    print(f"  ERROR planning path to obstacle {obstacle}: {e}")
                    continue

            print(f"\nSuccessfully planned paths to {successful_paths}/{len(self.simple_hamiltonian)} obstacles")

            # Compress commands
            self._compress_commands()

            # Output final command sequence
            print("\nFINAL COMMAND SEQUENCE:")
            print("-" * 60)
            for i, command in enumerate(self.commands):
                print(f"{i + 1:2d}. {command}")
            print("-" * 60)
            print(f"Total commands: {len(self.commands)}")
            print()

        except Exception as e:
            print(f"ERROR during path planning: {e}")
            import traceback
            traceback.print_exc()
