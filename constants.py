# made by SSJMarx with the help of GLM 4.6

import pygame
import random
import math

# Initialize pygame
pygame.init()


# Utility Functions
def get_largest_4_3_resolution():
    """Calculate the largest 4:3 resolution that fits on the current monitor."""
    info = pygame.display.Info()
    monitor_width = info.current_w
    monitor_height = info.current_h

    if monitor_width / monitor_height > 4 / 3:
        height = monitor_height * 0.9
        width = height * 4 / 3
    else:
        width = monitor_width * 0.9
        height = width * 3 / 4

    return int(width), int(height)


# Display and Scaling Constants
SCREEN_WIDTH, SCREEN_HEIGHT = get_largest_4_3_resolution()
BASE_WIDTH = 800
BASE_HEIGHT = 600
SCALE_X = SCREEN_WIDTH / BASE_WIDTH
SCALE_Y = SCREEN_HEIGHT / BASE_HEIGHT
screen_diagonal = math.sqrt(SCREEN_WIDTH ** 2 + SCREEN_HEIGHT ** 2)

# Color Constants
BACKGROUND_BLUE = (10, 20, 40)
WHITE = (255, 255, 255)
RED = (255, 0, 0)
PLAYER_COLOR = (0, 255, 100)  # Bright green for the player (was CYAN)
YELLOW = (255, 255, 0)
SINGLE_FIRE_COLOR = (0, 255, 255)  # Cyan for single shots
AUTO_FIRE_COLOR = (255, 255, 0)  # Yellow for auto-fire

# Player Constants
PLAYER_WIDTH = 25
PLAYER_HEIGHT = 25
PLAYER_MAX_SPEED = screen_diagonal / 3.0
PLAYER_ACCELERATION = 6000.0
PLAYER_FRICTION = 0.95

# Circle Constants
MIN_RADIUS = 20
MAX_RADIUS = 50
MIN_SPEED = 40
MAX_SPEED = 200
MIN_SPLIT_RADIUS = 10

# Projectile Constants
PROJECTILE_SPEED = 900
PROJECTILE_SIZE = 3
PROJECTILE_HITBOX_BONUS = 5 * SCALE_X
HOMING_STRENGTH = 0.001
SINGLE_FIRE_HOMING_STRENGTH = 1
AUTO_FIRE_BASE_DELAY = 6
AUTO_FIRE_MIN_DELAY = 2
AUTO_FIRE_RAMP_UP_TIME = 1.0
RAPID_CLICK_THRESHOLD = 0.5
PROJECTILE_MAX_SIZE_MULTIPLIER = 2.0
SINGLE_FIRE_SIZE_MULTIPLIER = 5.0

# Particle Constants
PARTICLE_LIFETIME = 30
PUSH_RANGE = SCREEN_WIDTH / 4
PUSH_STRENGTH = 2.0

# Game Logic Constants
AUTO_FIRE_DELAY = 6
SCREEN_SHAKE_DURATION = 3

# Performance and Timing Constants
TARGET_LOGIC_FPS = 20
LOGIC_TIMESTEP = 1.0 / TARGET_LOGIC_FPS
PLAYER_LOGIC_FPS = 120
PLAYER_LOGIC_TIMESTEP = 1.0 / PLAYER_LOGIC_FPS
FPS_CHECK_INTERVAL = 15
INITIAL_MAX_OBJECTS = 2000
OBJECT_BUFFER = 20
PARTICLE_CLEANUP_RATIO = 0.7

# Particle Generation Variables
INITIAL_PARTICLE_COUNT = 20  # Base number of particles when game starts

# Performance Variables (truly global, will persist across game sessions) - DISABLED
# max_objects = INITIAL_MAX_OBJECTS  # Current maximum number of objects
# current_particle_count = INITIAL_PARTICLE_COUNT  # Current number of particles (will be reduced)

# Fixed values to use instead of dynamic optimization
max_objects = INITIAL_MAX_OBJECTS  # Fixed maximum number of objects
current_particle_count = INITIAL_PARTICLE_COUNT  # Fixed particle count

# Particle Cloud Tracking
particle_clouds = []  # List to track active particle clouds
explosions = []  # List to track active explosions

# Star Constants
STAR_COUNT = 100
STAR_MIN_SIZE = 0.5
STAR_MAX_SIZE = 2.0
STAR_SPEED = 50
STAR_COLORS = [
    (255, 255, 255),  # White
    (255, 255, 200),  # Light yellow
    (200, 200, 255),  # Light blue
    (255, 200, 200),  # Light cyan
]

# Sound Constants
SOUND_ENABLED = True
SOUND_VOLUME = 0.5
SOUND_SHOOT_FREQ = 660  # Hz
SOUND_HIT_FREQ = 330    # Hz
SOUND_DEATH_START_FREQ = 880  # Hz
SOUND_DEATH_END_FREQ = 110    # Hz
SOUND_COLLISION_FREQ1 = 440    # Hz
SOUND_COLLISION_FREQ2 = 220    # Hz
