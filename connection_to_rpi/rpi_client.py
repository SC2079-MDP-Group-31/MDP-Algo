# Cleaned

import socket
import logging
from typing import List, Optional, Union


class RPiClient:
    """
    Client for connecting to Raspberry Pi via TCP socket.

    Supports context manager usage for automatic resource cleanup.
    """

    def __init__(self, host: str, port: int, buffer_size: int = 1024, timeout: Optional[float] = None):
        """
        Initialize the RPI client.

        Args:
            host: The hostname or IP address to connect to
            port: The port number to connect to
            buffer_size: Size of receive buffer in bytes
            timeout: Socket timeout in seconds (None for no timeout)
        """
        self.host = host
        self.port = port
        self.buffer_size = buffer_size
        self.timeout = timeout
        self.socket: Optional[socket.socket] = None
        self._connected = False

        self.logger = logging.getLogger(__name__)

    def connect(self) -> None:
        """
        Establish connection to the RPI server.

        Raises:
            ConnectionError: If connection fails
            OSError: If socket creation fails
        """
        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            if self.timeout:
                self.socket.settimeout(self.timeout)

            self.socket.connect((self.host, self.port))
            self._connected = True
            self.logger.info(f"Connected to {self.host}:{self.port}")

        except (socket.error, OSError) as e:
            self.logger.error(f"Failed to connect to {self.host}:{self.port}: {e}")
            raise ConnectionError(f"Could not connect to {self.host}:{self.port}") from e

    def send_message(self, messages: Union[str, List[str]]) -> None:
        """
        Send message(s) to the server.

        Args:
            messages: Single message string or list of message strings

        Raises:
            ConnectionError: If not connected or connection lost
            ValueError: If message is empty or invalid type
        """
        if not self.is_connected():
            raise ConnectionError("Not connected to server")

        # Handle both single string and list of strings
        if isinstance(messages, str):
            messages = [messages]
        elif not isinstance(messages, (list, tuple)):
            raise ValueError("Messages must be a string or list of strings")

        if not messages:
            raise ValueError("No messages to send")

        try:
            for message in messages:
                if not isinstance(message, str):
                    raise ValueError(f"All messages must be strings, got {type(message)}")
                if not message:
                    self.logger.warning("Skipping empty message")
                    continue

                self.socket.send(message.encode("utf-8"))
                self.logger.debug(f"Sent message: {message[:50]}...")

        except (socket.error, OSError) as e:
            self.logger.error(f"Failed to send message: {e}")
            self._connected = False
            raise ConnectionError("Connection lost while sending") from e

    def receive_message(self) -> Optional[bytes]:
        """
        Receive message from the server.

        Returns:
            Received data as bytes, or None if no data received

        Raises:
            ConnectionError: If not connected or connection lost
        """
        if not self.is_connected():
            raise ConnectionError("Not connected to server")

        try:
            data = self.socket.recv(self.buffer_size)
            if not data:
                self.logger.info("Server closed connection")
                self._connected = False
                return None

            self.logger.debug(f"Received {len(data)} bytes")
            return data

        except (socket.error, OSError) as e:
            self.logger.error(f"Failed to receive message: {e}")
            self._connected = False
            raise ConnectionError("Connection lost while receiving") from e

    def is_connected(self) -> bool:
        """Check if client is connected to server."""
        return self._connected and self.socket is not None

    def close(self) -> None:
        """Close the connection and clean up resources."""
        if self.socket:
            try:
                self.socket.close()
                self.logger.info("Connection closed")
            except OSError as e:
                self.logger.warning(f"Error closing socket: {e}")
            finally:
                self.socket = None
                self._connected = False

    def __enter__(self):
        """Context manager entry."""
        self.connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit with automatic cleanup."""
        self.close()

    def __del__(self):
        """Destructor to ensure socket is closed."""
        self.close()