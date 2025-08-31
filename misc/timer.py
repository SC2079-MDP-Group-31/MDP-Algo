import pygame
import pygame.freetype
import constants


class Timer:
    def __init__(self):
        self.start_time = 0
        self.end_time = 0
        self.is_running = False
        self.is_finished = False

    def start(self):
        """Start the timer."""
        self.is_running = True
        self.is_finished = False
        self.start_time = pygame.time.get_ticks()

    def stop(self):
        """Stop the timer."""
        if self.is_running:
            self.end_time = pygame.time.get_ticks()
            self.is_running = False
            self.is_finished = True

    def get_elapsed_time(self):
        """Get elapsed time in milliseconds."""
        if self.is_running:
            return pygame.time.get_ticks() - self.start_time
        elif self.is_finished:
            return self.end_time - self.start_time
        return 0

    def format_time(self):
        """Format elapsed time as MM:SS:mmm string."""
        elapsed_ms = self.get_elapsed_time()

        milliseconds = elapsed_ms % 1000
        total_seconds = elapsed_ms // 1000
        seconds = total_seconds % 60
        minutes = total_seconds // 60

        return f"{minutes:02d}:{seconds:02d}:{milliseconds:03d}"

    def render(self, screen, position=None):
        """Render the timer on the screen."""
        if position is None:
            position = (constants.GRID_LENGTH + 40, constants.GRID_LENGTH // 2)

        font = pygame.freetype.SysFont(None, 34)
        font.origin = True

        time_text = self.format_time()
        font.render_to(screen, position, time_text, pygame.Color("dodgerblue"))