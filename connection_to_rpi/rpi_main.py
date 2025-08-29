# Cleaned

import sys
import time
from contextlib import contextmanager
from typing import List, Tuple, Optional

from rpi_client import RPiClient
from rpi_server import RPiServer


# Configuration constants
SERVER_PORT = 4160
CLIENT_PORT = 4161
CONNECTION_RETRY_DELAY = 0.1  # seconds
DEFAULT_OBSTACLE_DATA = [[23, 23, 90], [45, 45, 78]]


@contextmanager
def managed_server(host: str, port: int):
    """Context manager for proper server resource management."""
    server = RPiServer(host, port)
    try:
        yield server
    finally:
        server.close()


@contextmanager
def managed_client(host: str, port: int):
    """Context manager for proper client resource management."""
    client = RPiClient(host, port)
    try:
        yield client
    finally:
        client.close()


def establish_server_connection() -> Tuple[RPiServer, str]:
    """
    Start server and wait for PC connection.
    Returns the server instance and the connected PC's IP address.
    """
    print("Starting server and waiting for PC connection...")

    with managed_server("", SERVER_PORT) as server:
        try:
            server.start()
            pc_host = server.address[0]
            print(f"PC connected from {pc_host}")
            return server, pc_host
        except Exception as e:
            print(f"Failed to establish server connection: {e}")
            sys.exit(1)


def connect_to_pc_server(pc_host: str) -> RPiClient:
    """
    Connect to the PC's server with retry logic.
    Returns the connected client instance.
    """
    print(f"Attempting to connect to PC server at {pc_host}:{CLIENT_PORT}")

    try:
        with managed_client(pc_host, CLIENT_PORT) as client:
            while True:
                try:
                    client.connect()
                    print("Successfully connected to PC server")
                    return client
                except OSError:
                    time.sleep(CONNECTION_RETRY_DELAY)
                except Exception as e:
                    print(f"Failed to connect to PC server: {e}")
                    sys.exit(1)
    except OSError as e:
        print(f"Failed to create client: {e}")
        sys.exit(1)


def send_obstacle_data(client: RPiClient, obstacle_data: Optional[List[List[int]]] = None) -> None:
    """Send obstacle data to the PC."""
    if obstacle_data is None:
        obstacle_data = DEFAULT_OBSTACLE_DATA
        print("Using default obstacle data (TODO: Replace with actual sensor data)")

    print("Sending obstacle data to PC...")
    try:
        client.send_message(obstacle_data)
        print("Obstacle data sent successfully")
    except Exception as e:
        print(f"Failed to send obstacle data: {e}")
        raise


def receive_robot_commands(server: RPiServer) -> List:
    """Receive and return robot commands from the PC."""
    print("Waiting for robot commands from PC...")
    try:
        commands = server.receive_data()
        print("Robot commands received successfully")
        print(f"Commands: {commands}")
        return commands
    except Exception as e:
        print(f"Failed to receive robot commands: {e}")
        raise


def main() -> None:
    """Main communication workflow between RPi and PC."""
    try:
        # Establish bidirectional communication
        with managed_server("", SERVER_PORT) as server:
            # Wait for PC to connect to our server
            server.start()
            pc_host = server.address[0]
            print(f"PC connected from {pc_host}")

            # Connect to PC's server and send obstacle data
            with managed_client(pc_host, CLIENT_PORT) as client:
                # Connect to PC with retry logic
                print(f"Connecting to PC server at {pc_host}:{CLIENT_PORT}")
                while True:
                    try:
                        client.connect()
                        print("Connected to PC server")
                        break
                    except OSError:
                        time.sleep(CONNECTION_RETRY_DELAY)

                # Send obstacle data
                send_obstacle_data(client)

            # Receive commands from PC
            receive_robot_commands(server)

    except KeyboardInterrupt:
        print("\nOperation interrupted by user")
        sys.exit(0)
    except Exception as e:
        print(f"Unexpected error in main workflow: {e}")
        sys.exit(1)

    print("Communication workflow completed successfully")


if __name__ == "__main__":
    main()