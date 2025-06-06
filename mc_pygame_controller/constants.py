import pygame

# Initialize Pygame
pygame.init()

# Window constants
WINDOW_WIDTH = 1600  # Increased from 1000
WINDOW_HEIGHT = 900  # Increased from 600
FPS = 60

# Custom pygame events for MCP integration
CUSTOM_MCP_TASK_EVENT = pygame.USEREVENT + 1
CUSTOM_MCP_RESULT_EVENT = pygame.USEREVENT + 2

# Colors
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
GRAY = (128, 128, 128)
LIGHT_GRAY = (200, 200, 200)
DARK_GRAY = (64, 64, 64)
BLUE = (0, 100, 255)
GREEN = (0, 255, 0)
RED = (255, 0, 0)
YELLOW = (255, 255, 0)
ORANGE = (255, 165, 0)
PURPLE = (128, 0, 128)
CYAN = (0, 255, 255)
PINK = (255, 192, 203)
