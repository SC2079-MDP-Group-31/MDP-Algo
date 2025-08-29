# Cleaned

import json
import socket
import logging
from typing import Optional, Any, Tuple
from contextlib import contextmanager


class RPiServer:
    """
    A secure server for Raspberry Pi with proper error handling and resource management.
    Uses JSON serialization instead of pickle for security.
    """

    def __init__(self, host: str = 'localhost', port: int = 8080, buffer_size: int = 1024):
        self.host = host
        self.port = port
        self.buffer_size = buffer_size
        self.socket: Optional[socket.socket] = None

        # Setup logging
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)

    def start(self) -> None:
        """Initialize and start the server socket."""
        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.socket.bind((self.host, self.port))
            self.socket.listen(5)
            self.logger.info(f"Server started at {self.host}:{self.port}")
        except Exception as e:
            self.logger.error(f"Failed to start server: {e}")
            self.close()
            raise

    @contextmanager
    def accept_connection(self):
        """Context manager for handling client connections safely."""
        if not self.socket:
            raise RuntimeError("Server not started. Call start() first.")

        conn, address = None, None
        try:
            self.logger.info("Waiting for connection...")
            conn, address = self.socket.accept()
            self.logger.info(f"Connection established from {address}")
            yield conn, address
        except Exception as e:
            self.logger.error(f"Connection error: {e}")
            raise
        finally:
            if conn:
                conn.close()
                self.logger.info(f"Connection closed for {address}")

    def receive_data(self, conn: socket.socket) -> Any:
        """
        Safely receive and deserialize data from client connection.
        Uses JSON instead of pickle for security.
        """
        data_chunks = []

        try:
            while True:
                chunk = conn.recv(self.buffer_size)
                if not chunk:
                    break
                data_chunks.append(chunk)

                # Check if we received a complete JSON message
                try:
                    combined_data = b"".join(data_chunks).decode('utf-8')
                    # Try to parse as JSON to see if message is complete
                    json.loads(combined_data)
                    break
                except (json.JSONDecodeError, UnicodeDecodeError):
                    # Continue receiving if JSON is incomplete or corrupted
                    continue

            if not data_chunks:
                self.logger.warning("No data received from client")
                return None

            # Combine and deserialize data
            raw_data = b"".join(data_chunks).decode('utf-8')
            return json.loads(raw_data)

        except json.JSONDecodeError as e:
            self.logger.error(f"Failed to deserialize data: {e}")
            raise ValueError("Invalid JSON data received")
        except UnicodeDecodeError as e:
            self.logger.error(f"Failed to decode data: {e}")
            raise ValueError("Invalid UTF-8 data received")
        except Exception as e:
            self.logger.error(f"Error receiving data: {e}")
            raise

    def send_data(self, conn: socket.socket, data: Any) -> None:
        """Send data to client connection."""
        try:
            json_data = json.dumps(data).encode('utf-8')
            conn.sendall(json_data)
            self.logger.info("Data sent successfully")
        except Exception as e:
            self.logger.error(f"Failed to send data: {e}")
            raise

    def handle_client(self) -> Any:
        """Handle a single client connection and return received data."""
        with self.accept_connection() as (conn, address):
            return self.receive_data(conn)

    def run_server(self, handler_callback=None) -> None:
        """
        Run the server continuously, handling multiple client connections.

        Args:
            handler_callback: Optional function to process received data
        """
        try:
            self.start()
            while True:
                try:
                    with self.accept_connection() as (conn, address):
                        data = self.receive_data(conn)

                        if handler_callback and data is not None:
                            response = handler_callback(data)
                            if response is not None:
                                self.send_data(conn, response)

                except KeyboardInterrupt:
                    self.logger.info("Server shutdown requested")
                    break
                except Exception as e:
                    self.logger.error(f"Error handling client: {e}")
                    continue
        finally:
            self.close()

    def close(self) -> None:
        """Clean up and close the server socket."""
        if self.socket:
            try:
                self.socket.close()
                self.logger.info("Server socket closed")
            except Exception as e:
                self.logger.error(f"Error closing socket: {e}")
            finally:
                self.socket = None

    def __enter__(self):
        """Context manager entry."""
        self.start()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()