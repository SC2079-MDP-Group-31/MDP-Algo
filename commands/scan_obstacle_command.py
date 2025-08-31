from commands.command import Command


class ScanCommand(Command):
    """
    A command that instructs a robot to scan a specific object.

    Args:
        time: The time when this command should be executed
        obj_index: The index of the object to scan
    """

    def __init__(self, time, obj_index):
        super().__init__(time)
        self.obj_index = obj_index

    def __str__(self):
        return f"ScanCommand(time={self.time}, obj_index={self.obj_index})"

    __repr__ = __str__

    def process_one_tick(self, robot):
        """Process one tick of the scan command."""
        if self.total_ticks == 0:
            return

        self.tick()

    def apply_on_pos(self, curr_pos):
        """
        Apply the scan command on the current position.
        Scan commands don't modify position, so this is a no-op.
        """
        pass

    def convert_to_message(self):
        """
        Convert the scan command to a message format.

        Returns:
            str: Message in the format "SCAN_{obj_index}"
        """
        return f"SCAN_{self.obj_index}"