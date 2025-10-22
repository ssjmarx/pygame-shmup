# made by SSJMarx with the help of GLM 4.6

import pygame
import random
import sys
import time
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

# Performance Variables (truly global, will persist across game sessions)
max_objects = INITIAL_MAX_OBJECTS  # Current maximum number of objects
current_particle_count = INITIAL_PARTICLE_COUNT  # Current number of particles (will be reduced)

# Particle Cloud Tracking
particle_clouds = []  # List to track active particle clouds
explosions = []  # List to track active explosions

# Starfield Variables
global_star_direction = random.uniform(0, 2 * math.pi)  # Random direction for star movement
stars = []  # List to store all stars
STAR_COUNT = 100  # Number of stars to generate


# Game Classes
class Explosion:
    """Represents an explosion that applies outward force to particles."""

    def __init__(self, x, y, radius, strength, lifetime):
        self.x = x
        self.y = y
        self.radius = radius
        self.strength = strength
        self.lifetime = lifetime
        self.max_lifetime = lifetime

    def update(self, dt):
        """Update the explosion's lifetime."""
        self.lifetime -= dt

    def is_expired(self):
        """Check if the explosion has expired."""
        return self.lifetime <= 0

    def apply_force(self, particle):
        """Apply explosion force to a particle (only persistent particles)."""
        # Only apply force to persistent particles
        if not particle.is_persistent:
            return

        dx = particle.x - self.x
        dy = particle.y - self.y
        distance = math.sqrt(dx ** 2 + dy ** 2)

        if 0 < distance < self.radius:
            # Calculate force based on distance (stronger when closer)
            distance_ratio = distance / self.radius
            force = self.strength * (1 - distance_ratio ** 2)

            # Apply force in the direction away from explosion center
            if distance > 0:
                particle.dx += (dx / distance) * force
                particle.dy += (dy / distance) * force

    def apply_force_to_player(self, player):
        """Apply explosion force to the player and return the push strength."""
        dx = player.rect.centerx - self.x
        dy = player.rect.centery - self.y
        distance = math.sqrt(dx ** 2 + dy ** 2)

        # Increased effective radius by 50% for player
        effective_radius = self.radius * 1.5

        if 0 < distance < effective_radius:
            # Calculate force based on distance (stronger when closer)
            distance_ratio = distance / effective_radius
            force = self.strength * (1 - distance_ratio ** 2) * 15.0  # Increased from 10.0 to 15.0

            # Apply force to player's velocity
            if distance > 0:
                player.vx += (dx / distance) * force
                player.vy += (dy / distance) * force
                player.apply_push_visual()  # Trigger visual effect

                # Return the force strength for shake effect
                return force * 0.5  # Return a portion of the force for shake
        return 0  # No force applied, no shake


class ParticleCloud:
    """Represents an area where particles were recently generated."""

    def __init__(self, x, y, lifetime):
        self.x = x
        self.y = y
        self.lifetime = lifetime
        self.max_lifetime = lifetime
        print(f"New ParticleCloud created at ({x:.1f}, {y:.1f}) with lifetime {lifetime}")

    def update(self, dt):
        """Update the cloud's lifetime."""
        self.lifetime -= dt

    def is_expired(self):
        """Check if the cloud has expired."""
        return self.lifetime <= 0

    def is_too_close(self, x, y, min_distance):
        """Check if a position is too close to this cloud."""
        distance = math.sqrt((self.x - x) ** 2 + (self.y - y) ** 2)
        is_close = distance < min_distance
        if is_close:
            print(f"Position ({x:.1f}, {y:.1f}) is too close to cloud at ({self.x:.1f}, {self.y:.1f}) - distance: {distance:.1f}")
        return is_close


class Player:
    """Represents the player's ship."""

    def __init__(self, x, y):
        self.rect = pygame.Rect(x, y, PLAYER_WIDTH, PLAYER_HEIGHT)
        self.prev_rect = self.rect.copy()  # For interpolation
        self.color = PLAYER_COLOR  # Use the new player color constant
        self.vx = 0.0
        self.vy = 0.0
        self.push_effect_timer = 0  # Timer for visual push effect
        self.shake_offset_x = 0.0  # Shake offset for X position
        self.shake_offset_y = 0.0  # Shake offset for Y position
        self.shake_decay = 0.8  # How quickly shake decays
        self.death_timer = 0.0  # Timer for death animation
        self.is_dying = False  # Track if player is in death animation

    def apply_push_visual(self):
        """Called when player is pushed by particles."""
        self.push_effect_timer = 10  # Show effect for 10 frames

    def apply_shake(self, force):
        """Apply shake effect to the player's position."""
        # Apply random shake based on force strength
        shake_magnitude = min(force * 2.0, 10.0)  # Cap the shake magnitude
        self.shake_offset_x += random.uniform(-shake_magnitude, shake_magnitude)
        self.shake_offset_y += random.uniform(-shake_magnitude, shake_magnitude)

    def update_shake(self):
        """Update shake offsets (decay over time)."""
        self.shake_offset_x *= self.shake_decay
        self.shake_offset_y *= self.shake_decay

        # If shake is very small, reset to 0
        if abs(self.shake_offset_x) < 0.1:
            self.shake_offset_x = 0
        if abs(self.shake_offset_y) < 0.1:
            self.shake_offset_y = 0

    def start_death_animation(self):
        """Start the death animation."""
        self.is_dying = True
        self.death_timer = 1.0  # 1 second death animation

    def update_death_animation(self, dt):
        """Update the death animation timer."""
        if self.is_dying:
            self.death_timer -= dt

            # Apply continuous shake during death animation
            shake_amount = self.death_timer * 5.0  # Shake decreases as timer counts down
            self.shake_offset_x += random.uniform(-shake_amount, shake_amount)
            self.shake_offset_y += random.uniform(-shake_amount, shake_amount)

            if self.death_timer <= 0:
                return True  # Death animation complete
        return False

    def draw(self, screen, alpha):
        """Draws the player at an interpolated position with shake effect."""
        interpolated_x = self.prev_rect.x + (self.rect.x - self.prev_rect.x) * alpha
        interpolated_y = self.prev_rect.y + (self.rect.y - self.prev_rect.y) * alpha

        # Apply shake offset to the interpolated position
        shake_x = interpolated_x + self.shake_offset_x
        shake_y = interpolated_y + self.shake_offset_y

        draw_rect = pygame.Rect(shake_x, shake_y, self.rect.width, self.rect.height)

        # Change color based on state
        color = self.color
        if self.is_dying:
            # Flash red and white during death animation
            flash = int(self.death_timer * 15) % 2  # Faster flashing
            color = (255, 255, 255) if flash else (255, 0, 0)
        elif self.push_effect_timer > 0:
            # Flash white when pushed
            color = (255, 255, 255)
            self.push_effect_timer -= 1

        pygame.draw.rect(screen, color, draw_rect)

    def move(self, keys, dt):
        """Updates player position and velocity based on input."""
        # Don't move if in death animation
        if self.is_dying:
            return

        # Apply push force before handling input
        # Store the current velocity to add push force
        current_vx = self.vx
        current_vy = self.vy

        # Get normalized input direction from keyboard state
        input_x, input_y = 0, 0
        if keys[pygame.K_LEFT] or keys[pygame.K_a]:
            input_x -= 1
        if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
            input_x += 1
        if keys[pygame.K_UP] or keys[pygame.K_w]:
            input_y -= 1
        if keys[pygame.K_DOWN] or keys[pygame.K_s]:
            input_y += 1

        if input_x != 0 or input_y != 0:
            input_magnitude = math.sqrt(input_x ** 2 + input_y ** 2)
            if input_magnitude > 0:
                input_x /= input_magnitude
                input_y /= input_magnitude

            # Calculate current speed and apply smooth, direction-based acceleration
            current_speed = math.sqrt(self.vx ** 2 + self.vy ** 2)
            speed_capacity = 1.0

            if current_speed > 0.1:
                vel_x = self.vx / current_speed
                vel_y = self.vy / current_speed
                dot = (vel_x * input_x) + (vel_y * input_y)

                # Calculate a smooth turn factor based on the angle between velocity and input
                turn_factor = ((1.0 - dot) / 2.0) ** 0.4
                forward_taper = 1.0 - (current_speed / PLAYER_MAX_SPEED)
                speed_capacity = max(turn_factor, forward_taper)

            # Apply acceleration and clamp to max speed
            self.vx += input_x * PLAYER_ACCELERATION * dt * speed_capacity
            self.vy += input_y * PLAYER_ACCELERATION * dt * speed_capacity
            new_speed = math.sqrt(self.vx ** 2 + self.vy ** 2)
            if new_speed > PLAYER_MAX_SPEED:
                self.vx = (self.vx / new_speed) * PLAYER_MAX_SPEED
                self.vy = (self.vy / new_speed) * PLAYER_MAX_SPEED
        else:
            # Apply friction when no input is given
            self.vx *= PLAYER_FRICTION
            self.vy *= PLAYER_FRICTION
            if abs(self.vx) < 0.1:
                self.vx = 0
            if abs(self.vy) < 0.1:
                self.vy = 0

        # Update position and keep player on screen
        self.rect.x += self.vx * dt
        self.rect.y += self.vy * dt
        self.rect.clamp_ip(pygame.Rect(0, 0, SCREEN_WIDTH, SCREEN_HEIGHT))

        # Update shake effect
        self.update_shake()


class Circle:
    """Represents an enemy circle."""

    def __init__(self):
        max_radius = MAX_RADIUS * 1.5
        self.radius = max(random.randint(MIN_RADIUS, int(max_radius)) * SCALE_X, MIN_RADIUS * SCALE_X)
        self.speed = random.uniform(MIN_SPEED, MAX_SPEED) * SCALE_X
        self.prev_x = self.x = 0
        self.prev_y = self.y = 0
        self.color = self._get_random_color()
        self._spawn_from_edge()
        self.prev_x = self.x
        self.prev_y = self.y

    @staticmethod
    def _get_random_color():
        """Generates a random warm color for the circle."""
        color_choice = random.choice(['red', 'orange', 'yellow', 'pink'])
        if color_choice == 'red':
            return random.randint(200, 255), random.randint(0, 100), random.randint(0, 100)
        elif color_choice == 'orange':
            return random.randint(200, 255), random.randint(100, 200), random.randint(0, 100)
        elif color_choice == 'yellow':
            return random.randint(200, 255), random.randint(200, 255), random.randint(0, 100)
        else:  # pink
            return random.randint(200, 255), random.randint(100, 200), random.randint(150, 255)

    def _spawn_from_edge(self):
        """Spawns the circle at a random edge of the screen."""
        side = random.choice(['left', 'right', 'top', 'bottom'])
        if side == 'left':
            self.x, self.y = -self.radius, random.randint(int(self.radius), int(SCREEN_HEIGHT - self.radius))
            angle = random.uniform(-math.pi / 4, math.pi / 4)
        elif side == 'right':
            self.x, self.y = SCREEN_WIDTH + self.radius, random.randint(int(self.radius),
                                                                        int(SCREEN_HEIGHT - self.radius))
            angle = random.uniform(3 * math.pi / 4, 5 * math.pi / 4)
        elif side == 'top':
            self.x, self.y = random.randint(int(self.radius), int(SCREEN_WIDTH - self.radius)), -self.radius
            angle = random.uniform(math.pi / 4, 3 * math.pi / 4)
        else:  # bottom
            self.x, self.y = random.randint(int(self.radius),
                                            int(SCREEN_WIDTH - self.radius)), SCREEN_HEIGHT + self.radius
            angle = random.uniform(-3 * math.pi / 4, -math.pi / 4)

        # Calculate initial direction
        self.dx = math.cos(angle) * self.speed
        self.dy = math.sin(angle) * self.speed

        # Add bias toward center
        center_x = SCREEN_WIDTH / 2
        center_y = SCREEN_HEIGHT / 2
        to_center_x = center_x - self.x
        to_center_y = center_y - self.y
        to_center_dist = math.sqrt(to_center_x ** 2 + to_center_y ** 2)

        if to_center_dist > 0:
            # Normalize the direction to center
            to_center_x /= to_center_dist
            to_center_y /= to_center_dist

            # Apply bias (adjust this factor to control how much circles aim for center)
            bias_strength = 0.5  # Adjust this value to change bias strength
            self.dx = self.dx * (1 - bias_strength) + to_center_x * self.speed * bias_strength
            self.dy = self.dy * (1 - bias_strength) + to_center_y * self.speed * bias_strength

            # Ensure the speed remains consistent
            current_speed = math.sqrt(self.dx ** 2 + self.dy ** 2)
            if current_speed > 0:
                self.dx = (self.dx / current_speed) * self.speed
                self.dy = (self.dy / current_speed) * self.speed

    def update(self, dt):
        """Updates the circle's position."""
        self.prev_x = self.x
        self.prev_y = self.y
        self.x += self.dx * dt
        self.y += self.dy * dt

    def is_off_screen(self):
        """Checks if the circle is completely off-screen."""
        margin = 50
        return (self.x < -self.radius - margin or
                self.x > SCREEN_WIDTH + self.radius + margin or
                self.y < -self.radius - margin or
                self.y > SCREEN_HEIGHT + self.radius + margin)

    def draw(self, screen, alpha):
        """Draws the circle at an interpolated position."""
        interpolated_x = self.prev_x + (self.x - self.prev_x) * alpha
        interpolated_y = self.prev_y + (self.y - self.prev_y) * alpha
        pygame.draw.circle(screen, self.color, (int(interpolated_x), int(interpolated_y)), int(self.radius))

    def collides_with(self, player):
        """Checks collision with the player rectangle."""
        closest_x = max(player.rect.left, min(self.x, player.rect.right))
        closest_y = max(player.rect.top, min(self.y, player.rect.bottom))
        distance_sq = (self.x - closest_x) ** 2 + (self.y - closest_y) ** 2
        return distance_sq < (self.radius ** 2)

    def collides_with_circle(self, other_circle):
        """Checks collision with another circle."""
        distance = math.sqrt((self.x - other_circle.x) ** 2 + (self.y - other_circle.y) ** 2)
        return distance < (self.radius + other_circle.radius)

    def split(self):
        """Splits the circle into smaller circles."""
        min_split_radius = MIN_SPLIT_RADIUS * SCALE_X

        # Check if the circle is large enough to split
        if self.radius < min_split_radius * 2:
            return []

        # Determine number of splits (2-6)
        num_splits = random.randint(2, 6)

        new_circles = []
        split_angle = random.uniform(0, 2 * math.pi)

        # Calculate the total area we want to distribute (80% of original)
        total_target_area = math.pi * (self.radius ** 2) * 0.8

        # Generate random sizes that sum to the target area
        # We'll use a method that ensures fairness in size distribution
        size_ratios = []
        remaining_ratio = 1.0

        for i in range(num_splits - 1):
            # Each circle gets a random portion of the remaining area
            ratio = random.uniform(0.1, remaining_ratio * 0.8)
            size_ratios.append(ratio)
            remaining_ratio -= ratio

        # Last circle gets the remaining area
        size_ratios.append(remaining_ratio)

        # Shuffle to randomize which circle gets which size
        random.shuffle(size_ratios)

        # Calculate minimum area needed for all circles
        min_total_area = num_splits * math.pi * (min_split_radius ** 2)

        # If we can't create circles of minimum size, reduce the number
        if total_target_area < min_total_area:
            # Calculate maximum number of circles we can create
            max_possible = int(total_target_area / (math.pi * (min_split_radius ** 2)))
            num_splits = max(2, min(max_possible, 6))  # Ensure at least 2, max 6

            # Recalculate size ratios with the new number
            size_ratios = []
            remaining_ratio = 1.0

            for i in range(num_splits - 1):
                ratio = random.uniform(0.1, remaining_ratio * 0.8)
                size_ratios.append(ratio)
                remaining_ratio -= ratio

            size_ratios.append(remaining_ratio)
            random.shuffle(size_ratios)

        for i in range(num_splits):
            new_circle = Circle.__new__(Circle)

            # Calculate radius based on the area ratio
            target_area = total_target_area * size_ratios[i]

            # Ensure we don't try to calculate square root of negative
            if target_area <= 0:
                target_area = math.pi * (min_split_radius ** 2)

            new_circle.radius = math.sqrt(target_area / math.pi)

            # Ensure minimum size
            if new_circle.radius < min_split_radius:
                new_circle.radius = min_split_radius

            new_circle.speed = self.speed * 1.2  # Slightly faster than parent
            new_circle.color = self.color

            # Distribute circles evenly around the original circle
            current_angle = split_angle + (2 * math.pi * i / num_splits)

            # Position them closer together - use a fraction of the parent radius
            # This ensures they're closer together but not touching
            # Use 70% of the parent radius for positioning
            separation_distance = self.radius * 0.7
            new_circle.x = self.x + math.cos(current_angle) * separation_distance
            new_circle.y = self.y + math.sin(current_angle) * separation_distance

            # Set velocity moving outward from the center
            new_circle.dx = math.cos(current_angle) * new_circle.speed
            new_circle.dy = math.sin(current_angle) * new_circle.speed

            new_circle.prev_x = new_circle.x
            new_circle.prev_y = new_circle.y
            new_circles.append(new_circle)

        return new_circles

    def create_particles(self, current_objects, max_objects):
        """Creates a particle cloud upon destruction."""
        global particle_clouds  # Access the global particle_clouds list

        particles = []
        available_slots = max_objects - current_objects - OBJECT_BUFFER

        # Debug print to check available slots
        print(
            f"Creating particles: available_slots={available_slots}, current_objects={current_objects}, max_objects={max_objects}")

        if available_slots > 0:
            # Check if this location is too close to existing particle clouds
            min_distance = 100 * SCALE_X  # Minimum distance between particle clouds
            too_close = False

            for cloud in particle_clouds:
                if cloud.is_too_close(self.x, self.y, min_distance):
                    too_close = True
                    print(f"Particle generation blocked: too close to existing cloud at ({cloud.x}, {cloud.y})")
                    break

            # If too close to another cloud, reduce particle count significantly
            if too_close:
                particle_count = min(2, available_slots)  # Only generate a few particles
                print(f"Reduced particle count to {particle_count} due to proximity")
            else:
                # Use the current_particle_count (starts at 20, can be reduced by performance system)
                particle_count = min(current_particle_count, available_slots)
                print(f"Generating {particle_count} particles (current_particle_count={current_particle_count})")

                # Add a new cloud to track this area
                # Use PARTICLE_LIFETIME as the cloud's lifetime
                particle_clouds.append(ParticleCloud(self.x, self.y, PARTICLE_LIFETIME))
                print(f"Added new particle cloud at ({self.x}, {self.y})")

            # Scale particle size based on circle size
            # Calculate size ratio relative to the maximum possible circle size
            # This ensures max size circles create max sized particles
            max_possible_radius = MAX_RADIUS * 1.5 * SCALE_X  # Match the max radius in __init__
            size_ratio = self.radius / max_possible_radius
            size_ratio = max(0.25, min(1.0, size_ratio))  # Clamp between 0.25x and 1.0x of max particle size

            # Calculate base speed based on circle size
            # Larger circles should create faster particles
            base_speed = (self.radius / MIN_RADIUS) * 150 * SCALE_X  # Scale with circle size
            base_speed = max(100 * SCALE_X, min(base_speed, 500 * SCALE_X))  # Clamp between reasonable values

            for _ in range(particle_count):
                # Reduced chance of creating persistent particles from 5% to 2%
                is_persistent = random.random() < 0.02

                # Calculate random angle for particle direction
                angle = random.uniform(0, 2 * math.pi)

                # Calculate initial velocity with more variation
                # Use a random factor between 0.7 and 1.3 to add variety
                velocity_factor = random.uniform(0.7, 1.3)
                initial_speed = base_speed * velocity_factor

                # Calculate velocity components
                dx = math.cos(angle) * initial_speed
                dy = math.sin(angle) * initial_speed

                # Create particle with initial velocity
                particle = Particle(self.x, self.y, is_persistent, (dx, dy))

                # Scale the particle size based on the size ratio
                # Updated min/max sizes: 8 * SCALE_X to 24 * SCALE_X
                min_particle_size = 8 * SCALE_X
                max_particle_size = 24 * SCALE_X
                particle.size = min_particle_size + (max_particle_size - min_particle_size) * size_ratio

                # Store the initial size for shrinking effect
                particle.initial_size = particle.size

                particles.append(particle)
        else:
            print(f"No particles created: no available slots")

        return particles


class Projectile:
    """Represents a projectile fired by the player."""

    def __init__(self, x, y, target_x, target_y, player_vx: float = 0.0, player_vy: float = 0.0,
                 homing_strength: float = HOMING_STRENGTH, color: tuple = YELLOW, size_multiplier: float = 1.0):
        self.prev_x = self.x = x
        self.prev_y = self.y = y
        dx, dy = target_x - x, target_y - y
        distance = math.sqrt(dx ** 2 + dy ** 2)

        if distance > 0:
            # Normalize the shooting direction
            shoot_dir_x = dx / distance
            shoot_dir_y = dy / distance

            # Calculate the perpendicular component of player velocity
            # This is the component that affects aiming the most
            dot_product = player_vx * shoot_dir_x + player_vy * shoot_dir_y
            perp_vx = player_vx - dot_product * shoot_dir_x
            perp_vy = player_vy - dot_product * shoot_dir_y

            # Apply compensation (adjust this factor to control the strength)
            compensation_factor = 0.4  # Adjust this value to change compensation strength
            compensated_dx = shoot_dir_x * PROJECTILE_SPEED * SCALE_X - perp_vx * compensation_factor
            compensated_dy = shoot_dir_y * PROJECTILE_SPEED * SCALE_Y - perp_vy * compensation_factor

            self.dx = compensated_dx
            self.dy = compensated_dy
        else:
            self.dx, self.dy = 0, -PROJECTILE_SPEED * SCALE_X

        # Still add the player's velocity for the parallel component
        # This maintains the feeling of momentum
        self.dx += player_vx * 0.3  # Reduced influence
        self.dy += player_vy * 0.3  # Reduced influence

        self.angle = math.atan2(self.dy, self.dx)
        self.homing_strength = homing_strength  # Store the homing strength for this projectile
        self.color = color  # Store the color for this projectile
        self.size = PROJECTILE_SIZE * SCALE_X * size_multiplier  # Calculate the projectile size

    def update(self, circles, dt):
        """Updates projectile position and applies homing."""
        self.prev_x = self.x
        self.prev_y = self.y
        self.x += self.dx * dt
        self.y += self.dy * dt

        if circles:
            nearest_circle = min(circles, key=lambda c: math.sqrt((self.x - c.x) ** 2 + (self.y - c.y) ** 2))
            distance = math.sqrt((self.x - nearest_circle.x) ** 2 + (self.y - nearest_circle.y) ** 2)
            if nearest_circle and distance < 200 * SCALE_X:
                dx, dy = nearest_circle.x - self.x, nearest_circle.y - self.y
                dist = math.sqrt(dx ** 2 + dy ** 2)
                if dist > 0:
                    desired_dx = (dx / dist) * PROJECTILE_SPEED * SCALE_X
                    desired_dy = (dy / dist) * PROJECTILE_SPEED * SCALE_X
                    # Use the projectile's specific homing strength
                    self.dx = self.dx * (1 - self.homing_strength) + desired_dx * self.homing_strength
                    self.dy = self.dy * (1 - self.homing_strength) + desired_dy * self.homing_strength
                    self.angle = math.atan2(self.dy, self.dx)

    def is_off_screen(self):
        """Checks if the projectile is off-screen."""
        margin = 50
        return (self.x < -margin or self.x > SCREEN_WIDTH + margin or
                self.y < -margin or self.y > SCREEN_HEIGHT + margin)

    def draw(self, screen, alpha):
        """Draws the projectile as a triangle at an interpolated position."""
        interpolated_x = self.prev_x + (self.x - self.prev_x) * alpha
        interpolated_y = self.prev_y + (self.y - self.prev_y) * alpha
        cos_a, sin_a = math.cos(self.angle), math.sin(self.angle)
        points = [
            (self.size, 0),
            (-self.size / 2, self.size / 2),
            (-self.size / 2, -self.size / 2)
        ]
        rotated_points = [(px * cos_a - py * sin_a + interpolated_x, px * sin_a + py * cos_a + interpolated_y) for
                          px, py in points]
        pygame.draw.polygon(screen, self.color, rotated_points)

    def collides_with(self, circle):
        """Checks collision with a circle."""
        distance = math.sqrt((self.x - circle.x) ** 2 + (self.y - circle.y) ** 2)
        return distance < (circle.radius + PROJECTILE_HITBOX_BONUS)


class Particle:
    """Represents a visual particle effect."""

    def __init__(self, x, y, is_persistent=False, initial_velocity=None):
        self.x = x
        self.y = y
        self.is_persistent = is_persistent
        self.draw_in_front = random.random() < 0.5

        # Generate cool blue colors (higher blue values, moderate green, low red)
        self.color = (
            random.randint(0, 50),  # Red: 0-50 (very low)
            random.randint(100, 200),  # Green: 100-200 (moderate)
            random.randint(200, 255)  # Blue: 200-255 (high)
        )

        # Size will be set by the create_particles method
        self.size = random.randint(8, 24) * SCALE_X  # Default size, will be overridden
        self.initial_size = self.size  # Store initial size for shrinking

        self.lifetime = 1.0  # Set to 1 second for non-persistent particles
        self.persistent_timer = 0.0
        self.creation_time = time.time()  # Track when the particle was created
        self.shrink_timer = 0.0  # Timer for shrinking effect
        self.shrink_duration = 0.5  # Shrink over 0.5 seconds

        # Set initial velocity
        if initial_velocity:
            self.dx, self.dy = initial_velocity
        else:
            # Default random velocity if none provided
            self.dx = random.uniform(-4, 4) * SCALE_X
            self.dy = random.uniform(-4, 4) * SCALE_X

    def update(self, dt):
        """Updates particle position and lifetime."""
        self.x += self.dx * dt
        self.y += self.dy * dt

        if not self.is_persistent:
            self.lifetime -= dt  # Use dt directly instead of decrementing by 1

        # Update shrinking effect (independent of particle type)
        self.shrink_timer += dt
        if self.shrink_timer < self.shrink_duration:
            # Shrink from full size to half size over shrink_duration
            shrink_ratio = self.shrink_timer / self.shrink_duration  # 0.0 to 1.0
            # Linear interpolation from full size to half size
            self.size = self.initial_size * (1.0 - shrink_ratio * 0.5)
        else:
            # After shrink_duration, maintain half size
            self.size = self.initial_size * 0.5

        # Apply friction
        self.dx *= 0.96
        self.dy *= 0.96

        # Update persistent timer
        if self.is_persistent:
            self.persistent_timer += dt

    def is_expired(self):
        """Checks if a particle has exceeded its lifetime."""
        if self.is_persistent:
            return self.persistent_timer >= 30.0
        else:
            return self.lifetime <= 0

    def draw(self, screen):
        """Draws the particle."""
        if not self.is_persistent:
            alpha = self.lifetime / 1.0  # Use the actual lifetime value (1.0)
            base_color = self.color
            fade_color = (0, 0, 50)
            color = tuple(int(base_color[i] * alpha + fade_color[i] * (1 - alpha)) for i in range(3))
        else:
            color = self.color
        pygame.draw.circle(screen, color, (int(self.x), int(self.y)), int(self.size))

    def is_off_screen(self):
        """Checks if the particle is off-screen."""
        margin = 50
        return (self.x < -margin or self.x > SCREEN_WIDTH + margin or
                self.y < -margin or self.y > SCREEN_HEIGHT + margin)


class Star:
    """Represents a background star."""

    def __init__(self, x=None, y=None):
        # Initialize size first
        self.size = random.uniform(0.5, 1.5) * SCALE_X
        self.brightness = random.uniform(0.5, 1.0)
        self.twinkle_speed = random.uniform(0.01, 0.05)
        self.twinkle_phase = random.uniform(0, math.pi * 2)

        # If position is not specified, spawn at the edge of the screen
        if x is None or y is None:
            self._spawn_from_edge()
        else:
            self.x = x
            self.y = y

    def _spawn_from_edge(self):
        """Spawns the star at the edge of the screen opposite to the movement direction."""
        # Determine which edge to spawn at based on movement direction
        angle = global_star_direction  # Use the global direction

        # Normalize angle to 0-2π
        angle = angle % (2 * math.pi)

        # For diagonal movement, randomly choose between two possible edges
        if (math.pi / 8 < angle < 3 * math.pi / 8) or (7 * math.pi / 8 < angle < 9 * math.pi / 8) or \
                (15 * math.pi / 8 < angle < 17 * math.pi / 8):
            # Moving diagonally down-right, up-left, or up-right
            if random.random() < 0.5:
                # Choose one of the two edges
                if math.pi / 8 < angle < 3 * math.pi / 8:  # Down-right
                    self.x = random.uniform(0, SCREEN_WIDTH)
                    self.y = -self.size
                elif 7 * math.pi / 8 < angle < 9 * math.pi / 8:  # Up-left
                    self.x = SCREEN_WIDTH + self.size
                    self.y = random.uniform(0, SCREEN_HEIGHT)
                else:  # 15 * math.pi / 8 < angle < 17 * math.pi / 8 (Up-right)
                    self.x = -self.size
                    self.y = random.uniform(0, SCREEN_HEIGHT)
            else:
                # Choose the other edge
                if math.pi / 8 < angle < 3 * math.pi / 8:  # Down-right
                    self.x = -self.size
                    self.y = random.uniform(0, SCREEN_HEIGHT)
                elif 7 * math.pi / 8 < angle < 9 * math.pi / 8:  # Up-left
                    self.x = random.uniform(0, SCREEN_WIDTH)
                    self.y = SCREEN_HEIGHT + self.size
                else:  # 15 * math.pi / 8 < angle < 17 * math.pi / 8 (Up-right)
                    self.x = random.uniform(0, SCREEN_WIDTH)
                    self.y = -self.size
        elif (5 * math.pi / 8 < angle < 7 * math.pi / 8) or (11 * math.pi / 8 < angle < 13 * math.pi / 8):
            # Moving diagonally down-left or up-right
            if random.random() < 0.5:
                # Choose one of the two edges
                if 5 * math.pi / 8 < angle < 7 * math.pi / 8:  # Down-left
                    self.x = random.uniform(0, SCREEN_WIDTH)
                    self.y = -self.size
                else:  # 11 * math.pi / 8 < angle < 13 * math.pi / 8 (Up-right)
                    self.x = -self.size
                    self.y = random.uniform(0, SCREEN_HEIGHT)
            else:
                # Choose the other edge
                if 5 * math.pi / 8 < angle < 7 * math.pi / 8:  # Down-left
                    self.x = SCREEN_WIDTH + self.size
                    self.y = random.uniform(0, SCREEN_HEIGHT)
                else:  # 11 * math.pi / 8 < angle < 13 * math.pi / 8 (Up-right)
                    self.x = random.uniform(0, SCREEN_WIDTH)
                    self.y = SCREEN_HEIGHT + self.size
        else:
            # Non-diagonal movement (horizontal or vertical)
            if 0 <= angle < math.pi / 8 or 15 * math.pi / 8 <= angle < 2 * math.pi:
                # Moving right, spawn on left edge
                self.x = -self.size
                self.y = random.uniform(0, SCREEN_HEIGHT)
            elif math.pi / 8 <= angle < 3 * math.pi / 8:
                # Moving down-right, spawn on top or left edge
                if random.random() < 0.5:
                    self.x = -self.size
                    self.y = random.uniform(0, SCREEN_HEIGHT)
                else:
                    self.x = random.uniform(0, SCREEN_WIDTH)
                    self.y = -self.size
            elif 3 * math.pi / 8 <= angle < 5 * math.pi / 8:
                # Moving down, spawn on top edge
                self.x = random.uniform(0, SCREEN_WIDTH)
                self.y = -self.size
            elif 5 * math.pi / 8 <= angle < 7 * math.pi / 8:
                # Moving down-left, spawn on top or right edge
                if random.random() < 0.5:
                    self.x = SCREEN_WIDTH + self.size
                    self.y = random.uniform(0, SCREEN_HEIGHT)
                else:
                    self.x = random.uniform(0, SCREEN_WIDTH)
                    self.y = -self.size
            elif 7 * math.pi / 8 <= angle < 9 * math.pi / 8:
                # Moving left, spawn on right edge
                self.x = SCREEN_WIDTH + self.size
                self.y = random.uniform(0, SCREEN_HEIGHT)
            elif 9 * math.pi / 8 <= angle < 11 * math.pi / 8:
                # Moving up-left, spawn on bottom or right edge
                if random.random() < 0.5:
                    self.x = SCREEN_WIDTH + self.size
                    self.y = random.uniform(0, SCREEN_HEIGHT)
                else:
                    self.x = random.uniform(0, SCREEN_WIDTH)
                    self.y = SCREEN_HEIGHT + self.size
            elif 11 * math.pi / 8 <= angle < 13 * math.pi / 8:
                # Moving up, spawn on bottom edge
                self.x = random.uniform(0, SCREEN_WIDTH)
                self.y = SCREEN_HEIGHT + self.size
            else:  # 13 * math.pi / 8 <= angle < 15 * math.pi / 8
                # Moving up-right, spawn on bottom or left edge
                if random.random() < 0.5:
                    self.x = -self.size
                    self.y = random.uniform(0, SCREEN_HEIGHT)
                else:
                    self.x = random.uniform(0, SCREEN_WIDTH)
                    self.y = SCREEN_HEIGHT + self.size

    def update(self, dt):
        """Updates the star's position."""
        # Move the star in the global direction
        speed = 20 * SCALE_X  # Slow movement speed
        self.x += math.cos(global_star_direction) * speed * dt
        self.y += math.sin(global_star_direction) * speed * dt

        # Update twinkle
        self.twinkle_phase += self.twinkle_speed

    def draw(self, screen):
        """Draws the star."""
        # Calculate current brightness based on twinkle phase
        current_brightness = self.brightness * (0.7 + 0.3 * math.sin(self.twinkle_phase))
        color = (int(255 * current_brightness), int(255 * current_brightness), int(255 * current_brightness))
        pygame.draw.circle(screen, color, (int(self.x), int(self.y)), int(self.size))

    def is_off_screen(self):
        """Checks if the star is off-screen."""
        margin = 10
        return (self.x < -margin or self.x > SCREEN_WIDTH + margin or
                self.y < -margin or self.y > SCREEN_HEIGHT + margin)


# Game Functions
def initialize_stars():
    """Initializes the starfield background."""
    global stars, global_star_direction

    # Only initialize if stars list is empty (to persist between game restarts)
    if not stars:
        # Set the global direction for star movement
        global_star_direction = random.uniform(0, 2 * math.pi)

        # Create initial stars
        for _ in range(STAR_COUNT):
            stars.append(Star(random.uniform(0, SCREEN_WIDTH), random.uniform(0, SCREEN_HEIGHT)))


def destroy_circle(circle, circles_list, particles_list, max_obj_limit):
    """Handles the destruction of a circle, creating splits, particles, and explosions."""
    if circle in circles_list:
        circles_list.remove(circle)
        circles_list.extend(circle.split())
        total_objects = len(circles_list) + len(particles_list)
        new_particles = circle.create_particles(total_objects, max_obj_limit)
        particles_list.extend(new_particles)

        # Create an explosion at the circle's position - size based on circle size
        # All circles now use the same explosion scaling
        explosion_radius = circle.radius * 5  # Base radius multiplier
        explosion_strength = circle.radius / 10  # Make the explosion strength proportional to the circle size

        explosions.append(Explosion(circle.x, circle.y, explosion_radius, explosion_strength, 0.5))


def cleanup_and_update_max(objects_dict, current_max):
    """Cleans up particles and updates the max object count on slowdown."""
    global max_objects, current_particle_count  # Add this to access the global variables

    particles = objects_dict['particles']
    total_objects = len(objects_dict['circles']) + len(objects_dict['projectiles']) + len(particles)
    new_max = int(total_objects * 0.8)
    new_max = max(new_max, INITIAL_MAX_OBJECTS // 10)

    # Only print debug message if we're actually reducing the max_objects value
    if new_max < current_max and new_max < max_objects:
        print(f"Slowdown detected! Reducing max_objects from {max_objects} to {new_max}")

        # Calculate the percentage of max_objects remaining
        percentage_remaining = new_max / max_objects

        # Reduce particle count proportionally
        new_particle_count = max(1, int(INITIAL_PARTICLE_COUNT * percentage_remaining * 0.5))

        # Only print particle message if we're actually reducing it
        if new_particle_count < current_particle_count:
            print(f"Particle count reduced to {new_particle_count} (was {current_particle_count})")
            current_particle_count = new_particle_count

        # Update the global max_objects
        max_objects = new_max

    # Calculate how many particles to remove (30% of total)
    particles_to_remove = int(len(particles) * 0.3)

    if particles_to_remove > 0:
        # Separate particles into categories
        non_persistent = [p for p in particles if not p.is_persistent]
        persistent = [p for p in particles if p.is_persistent]

        # Sort non-persistent by lifetime (oldest first)
        non_persistent.sort(key=lambda p: p.lifetime)

        # Sort persistent by persistent_timer (oldest first)
        persistent.sort(key=lambda p: p.persistent_timer)

        # Create a list of particles to remove in the specified order
        particles_to_remove_list = []

        # 1. Oldest non-persistent particles
        remove_count = min(particles_to_remove, len(non_persistent) // 2)
        particles_to_remove_list.extend(non_persistent[:remove_count])

        # 2. Youngest non-persistent particles
        if len(particles_to_remove_list) < particles_to_remove:
            remove_count = min(particles_to_remove - len(particles_to_remove_list),
                               len(non_persistent) - len(particles_to_remove_list))
            particles_to_remove_list.extend(non_persistent[-remove_count:])

        # 3. Oldest persistent particles
        if len(particles_to_remove_list) < particles_to_remove:
            remove_count = min(particles_to_remove - len(particles_to_remove_list),
                               len(persistent) // 2)
            particles_to_remove_list.extend(persistent[:remove_count])

        # 4. Youngest persistent particles
        if len(particles_to_remove_list) < particles_to_remove:
            remove_count = min(particles_to_remove - len(particles_to_remove_list),
                               len(persistent) - len(persistent) // 2)
            particles_to_remove_list.extend(persistent[-remove_count:])

        # Remove all marked particles at once
        for particle in particles_to_remove_list:
            if particle in particles:
                particles.remove(particle)

    return max_objects  # Return the updated max_objects value


def game_over_screen(screen, clock, score):
    """Displays the game over screen."""
    font_large = pygame.font.SysFont(None, int(72 * SCALE_X))
    font_medium = pygame.font.SysFont(None, int(36 * SCALE_X))

    waiting = True
    while waiting:
        # Update stars
        for star in stars[:]:
            star.update(1 / 120)  # Use a fixed timestep for consistent star movement
            if star.is_off_screen():
                stars.remove(star)
                stars.append(Star())

        # Draw everything
        screen.fill(BACKGROUND_BLUE)
        for star in stars:
            star.draw(screen)

        # Draw UI elements
        game_over_text = font_large.render("GAME OVER", True, RED)
        score_text = font_medium.render(f"Time survived: {score:.2f} seconds", True, WHITE)
        restart_text = font_medium.render("Press SPACE to play again or ESC to quit", True, WHITE)

        screen.blit(game_over_text,
                    game_over_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - 50 * SCALE_Y)))
        screen.blit(score_text, score_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 20 * SCALE_Y)))
        screen.blit(restart_text, restart_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 80 * SCALE_Y)))

        pygame.display.flip()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE:
                    waiting = False
                elif event.key == pygame.K_ESCAPE:
                    pygame.quit()
                    sys.exit()

        clock.tick(120)  # Limit to 60 FPS for the game over screen


def start_game_screen(screen, clock):
    """Displays the start game screen."""
    font_large = pygame.font.SysFont(None, int(72 * SCALE_X))
    font_medium = pygame.font.SysFont(None, int(36 * SCALE_X))

    waiting = True
    while waiting:
        # Update stars
        for star in stars[:]:
            star.update(1 / 120)  # Use a fixed timestep for consistent star movement
            if star.is_off_screen():
                stars.remove(star)
                stars.append(Star())

        # Draw everything
        screen.fill(BACKGROUND_BLUE)
        for star in stars:
            star.draw(screen)

        # Draw UI elements
        title_text = font_large.render("DODGE THE CIRCLES", True, WHITE)
        start_text = font_medium.render("Press SPACE to start or ESC to quit", True, WHITE)

        screen.blit(title_text, title_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - 50 * SCALE_Y)))
        screen.blit(start_text, start_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 20 * SCALE_Y)))

        pygame.display.flip()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE:
                    waiting = False
                elif event.key == pygame.K_ESCAPE:
                    pygame.quit()
                    sys.exit()

        clock.tick(120)  # Limit to 60 FPS for the start screen


def main():
    """Main game function."""
    # Declare global variables at the beginning of the function
    global particle_clouds, stars, explosions, max_objects, current_particle_count

    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption("Dodge the Circles")
    clock = pygame.time.Clock()

    # Initialize fonts
    font_small = pygame.font.SysFont(None, int(24 * SCALE_X))

    # Initialize stars (only once, persists between game restarts)
    initialize_stars()

    # Show start screen
    start_game_screen(screen, clock)  # Pass clock as parameter

    # Game State
    game_over = False
    start_time = time.time()
    score = 0.0
    circle_hits = 0
    show_performance = False

    # Display and Timing
    accumulator = 0.0
    player_accumulator = 0.0
    game_over_accumulator = 0.0
    global_frame_counter = 0
    last_cleanup_frame = 0
    screen_shake_timer = 0

    # Game Objects
    player = Player(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2)
    circles = []
    projectiles = []
    particles = []

    # Game Logic Variables
    mouse_held = False
    auto_fire_timer = 0
    spawn_timer = 0
    spawn_delay = 15
    single_fire_shot = False  # Track if we've already fired a single shot for this click
    mouse_hold_time = 0.0  # Track how long the mouse has been held
    current_fire_delay = AUTO_FIRE_BASE_DELAY  # Current firing delay
    last_click_time = 0.0  # Track the time of the last click
    click_count = 0  # Track consecutive clicks

    running = True
    while running:
        frame_time = clock.get_time() / 1000.0
        accumulator += frame_time
        global_frame_counter += 1
        current_time = time.time()  # Get current time for click tracking

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_F2:
                    show_performance = not show_performance  # Toggle performance display
                elif event.key == pygame.K_SPACE and game_over:
                    # Reset game state but keep performance settings
                    game_over = False
                    start_time = time.time()
                    score = 0.0
                    player = Player(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2)
                    circles, projectiles, particles = [], [], []
                    circle_hits = 0
                    auto_fire_timer = 0
                    spawn_timer = 0
                    spawn_delay = 15
                    mouse_held = False
                    single_fire_shot = False
                    mouse_hold_time = 0.0
                    current_fire_delay = AUTO_FIRE_BASE_DELAY
                    last_click_time = 0.0
                    click_count = 0
                    screen_shake_timer = 0
                    accumulator = 0.0
                    player_accumulator = 0.0
                    game_over_accumulator = 0.0
                    explosions = []  # Reset explosions list
                elif event.key == pygame.K_ESCAPE:
                    running = False
            # Move mouse events outside the KEYDOWN check
            if event.type == pygame.MOUSEBUTTONDOWN:
                mouse_held = True
                single_fire_shot = False  # Reset single fire flag when mouse is pressed
                mouse_hold_time = 0.0  # Reset hold time
                current_fire_delay = AUTO_FIRE_BASE_DELAY  # Reset firing delay

                # Check for rapid clicking
                if current_time - last_click_time < RAPID_CLICK_THRESHOLD:
                    click_count += 1
                else:
                    click_count = 1  # Reset click count if it's been a while
                last_click_time = current_time

            if event.type == pygame.MOUSEBUTTONUP:
                mouse_held = False
                single_fire_shot = False  # Reset single fire flag when mouse is released
                mouse_hold_time = 0.0  # Reset hold time
                current_fire_delay = AUTO_FIRE_BASE_DELAY  # Reset firing delay

                # Check for rapid clicking
                if current_time - last_click_time < RAPID_CLICK_THRESHOLD:
                    click_count += 1
                else:
                    click_count = 1  # Reset click count if it's been a while
                last_click_time = current_time

            if event.type == pygame.MOUSEBUTTONUP:
                mouse_held = False
                single_fire_shot = False  # Reset single fire flag when mouse is released
                mouse_hold_time = 0.0  # Reset hold time
                current_fire_delay = AUTO_FIRE_BASE_DELAY  # Reset firing delay

        if not game_over:
            # Update score continuously
            score = time.time() - start_time

            # Performance monitoring and cleanup
            if global_frame_counter % FPS_CHECK_INTERVAL == 0:
                current_fps = clock.get_fps()
                if current_fps < 60 and (global_frame_counter - last_cleanup_frame) > FPS_CHECK_INTERVAL * 2:
                    objects_dict = {'circles': circles, 'projectiles': projectiles, 'particles': particles}
                    max_objects = cleanup_and_update_max(objects_dict, max_objects)
                    particles = objects_dict['particles']
                    last_cleanup_frame = global_frame_counter

            # Player-specific update loop (120 FPS)
            player_accumulator += frame_time
            while player_accumulator >= PLAYER_LOGIC_TIMESTEP:
                player.prev_rect = player.rect.copy()
                player.move(pygame.key.get_pressed(), PLAYER_LOGIC_TIMESTEP)
                player_accumulator -= PLAYER_LOGIC_TIMESTEP

            # Main game logic update loop (20 FPS)
            while accumulator >= LOGIC_TIMESTEP:
                for circle in circles:
                    circle.prev_x, circle.prev_y = circle.x, circle.y

                for projectile in projectiles:
                    projectile.prev_x, projectile.prev_y = projectile.x, projectile.y

                # Update explosions and apply forces to particles
                for explosion in explosions[:]:
                    explosion.update(LOGIC_TIMESTEP)
                    if explosion.is_expired():
                        explosions.remove(explosion)
                    else:
                        # Apply explosion force to all particles
                        for particle in particles:
                            explosion.apply_force(particle)

                        # Apply explosion force to the player and get shake strength
                        shake_force = explosion.apply_force_to_player(player)
                        if shake_force > 0:
                            player.apply_shake(shake_force)

                        # Apply explosion force to the player if close enough
                        dx = player.rect.centerx - explosion.x
                        dy = player.rect.centery - explosion.y
                        distance = math.sqrt(dx ** 2 + dy ** 2)
                        if 0 < distance < explosion.radius:
                            distance_ratio = distance / explosion.radius
                            force = explosion.strength * (1 - distance_ratio ** 2) * 3.0  # Triple the effect on player
                            if distance > 0:
                                player.vx += (dx / distance) * force
                                player.vy += (dy / distance) * force
                                player.apply_push_visual()  # Trigger visual effect

                # Update circles after applying explosion forces
                for circle in circles[:]:
                    circle.update(LOGIC_TIMESTEP)
                    if circle.is_off_screen():
                        circles.remove(circle)
                        continue
                    if circle.collides_with(player) and not player.is_dying:
                        # Start death animation instead of immediately setting game_over
                        player.start_death_animation()

                        # Create more particles for player death, but respect the particle limit
                        total_objects = len(circles) + len(projectiles) + len(particles)
                        available_slots = max_objects - total_objects - OBJECT_BUFFER

                        # Calculate how many particles we can create
                        max_death_particles = 50  # Desired number
                        particle_count = min(max_death_particles, available_slots, current_particle_count * 2)

                        print(f"Player death: creating {particle_count} particles (available_slots={available_slots})")

                        # Scale player death particles based on player size
                        player_size_scale = 1.0  # Player is fixed size, so scale is 1.0

                        for _ in range(particle_count):
                            is_persistent = random.random() < 0.05
                            particle = Particle(player.rect.centerx, player.rect.centery, is_persistent)

                            # Scale the particle size (player is medium size)
                            # Updated min/max sizes: 8 * SCALE_X to 24 * SCALE_X
                            min_particle_size = 8 * SCALE_X
                            max_particle_size = 24 * SCALE_X
                            particle.size = min_particle_size + (
                                        max_particle_size - min_particle_size) * player_size_scale
                            particle.initial_size = particle.size  # Store initial size for shrinking

                            # Give particles initial velocity away from center
                            angle = random.uniform(0, 2 * math.pi)
                            speed = random.uniform(5, 15) * SCALE_X
                            particle.dx = math.cos(angle) * speed
                            particle.dy = math.sin(angle) * speed
                            particles.append(particle)

                        # Create a larger explosion at player's position
                        explosions.append(Explosion(player.rect.centerx, player.rect.centery,
                                                    200 * SCALE_X, 10.0, 0.5))  # Increased size and strength

                        # Apply immediate strong shake to the player
                        player.apply_shake(10.0)  # Increased from 5.0 to 10.0

                        for _ in range(particle_count):
                            is_persistent = random.random() < 0.05
                            particle = Particle(player.rect.centerx, player.rect.centery, is_persistent)

                            # Scale the particle size (player is medium size)
                            particle.size = random.randint(3, 8) * SCALE_X * player_size_scale

                            # Give particles initial velocity away from center
                            angle = random.uniform(0, 2 * math.pi)
                            speed = random.uniform(5, 15) * SCALE_X
                            particle.dx = math.cos(angle) * speed
                            particle.dy = math.sin(angle) * speed
                            particles.append(particle)

                        # Create a larger explosion at player's position
                        explosions.append(Explosion(player.rect.centerx, player.rect.centery,
                                                    200 * SCALE_X, 10.0, 0.5))  # Increased size and strength

                        # Apply immediate strong shake to the player
                        player.apply_shake(10.0)  # Increased from 5.0 to 10.0

                # Update player death animation
                if player.is_dying:
                    if player.update_death_animation(LOGIC_TIMESTEP):
                        game_over = True  # Death animation complete, set game over

                # Update projectiles
                for projectile in projectiles[:]:
                    projectile.update(circles, LOGIC_TIMESTEP)
                    if projectile.is_off_screen():
                        projectiles.remove(projectile)
                        continue
                    for circle in circles[:]:
                        if projectile.collides_with(circle):
                            if projectile in projectiles: projectiles.remove(projectile)
                            circle_hits += 1
                            destroy_circle(circle, circles, particles, max_objects)
                            screen_shake_timer = SCREEN_SHAKE_DURATION
                            break

                # Update particles within the fixed timestep
                particles_to_remove = []
                for particle in particles:
                    particle.update(LOGIC_TIMESTEP)
                    if particle.is_expired() or particle.is_off_screen():
                        particles_to_remove.append(particle)

                # Remove all marked particles at once
                for particle in particles_to_remove:
                    if particle in particles:
                        particles.remove(particle)

                # Update mouse hold time and firing rate
                if mouse_held:
                    mouse_hold_time += LOGIC_TIMESTEP
                    # Calculate the current firing delay based on hold time
                    hold_ratio = min(1.0, mouse_hold_time / AUTO_FIRE_RAMP_UP_TIME)
                    current_fire_delay = AUTO_FIRE_BASE_DELAY - (
                            AUTO_FIRE_BASE_DELAY - AUTO_FIRE_MIN_DELAY) * hold_ratio

                # Calculate projectile size based on firing rate
                size_multiplier = 1.0 + (PROJECTILE_MAX_SIZE_MULTIPLIER - 1.0) * (
                        1.0 - current_fire_delay / AUTO_FIRE_BASE_DELAY)

                # Determine if this should be treated as a single shot or auto-fire
                is_single_shot = (click_count == 1 and not single_fire_shot and
                                  (current_time - last_click_time) < RAPID_CLICK_THRESHOLD)

                # Single-fire logic (fires immediately on mouse press)
                if mouse_held and not single_fire_shot and is_single_shot and not player.is_dying:
                    projectile_count = 1
                    if circle_hits >= 125:
                        projectile_count = 5
                    elif circle_hits >= 25:
                        projectile_count = 3

                    total_objects = len(circles) + len(projectiles) + len(particles)
                    if total_objects + projectile_count < max_objects:
                        mouse_x, mouse_y = pygame.mouse.get_pos()
                        for i in range(projectile_count):
                            angle = (i - (projectile_count - 1) / 2) * 0.2 if projectile_count > 1 else 0
                            dx, dy = mouse_x - player.rect.centerx, mouse_y - player.rect.centery
                            distance = math.sqrt(dx ** 2 + dy ** 2)
                            if distance > 0:
                                cos_a, sin_a = math.cos(angle), math.sin(angle)
                                new_dx, new_dy = dx * cos_a - dy * sin_a, dx * sin_a + dy * cos_a
                                target_x, target_y = player.rect.centerx + new_dx, player.rect.centery + new_dy
                            else:
                                target_x, target_y = player.rect.centerx, player.rect.centery - 100
                            # Create projectile with stronger homing, cyan color, and larger size for single shots
                            projectiles.append(
                                Projectile(player.rect.centerx, player.rect.centery, target_x, target_y, player.vx,
                                           player.vy, SINGLE_FIRE_HOMING_STRENGTH, SINGLE_FIRE_COLOR,
                                           SINGLE_FIRE_SIZE_MULTIPLIER))
                    single_fire_shot = True  # Mark that we've fired a single shot

                # Auto-firing logic (fires continuously when mouse is held or clicking rapidly)
                if mouse_held and (mouse_hold_time > 0 or click_count > 1) and not player.is_dying:
                    auto_fire_timer += 1
                    if auto_fire_timer >= current_fire_delay:
                        projectile_count = 1
                        if circle_hits >= 125:
                            projectile_count = 5
                        elif circle_hits >= 25:
                            projectile_count = 3

                        total_objects = len(circles) + len(projectiles) + len(particles)
                        if total_objects + projectile_count < max_objects:
                            mouse_x, mouse_y = pygame.mouse.get_pos()
                            for i in range(projectile_count):
                                angle = (i - (projectile_count - 1) / 2) * 0.2 if projectile_count > 1 else 0
                                dx, dy = mouse_x - player.rect.centerx, mouse_y - player.rect.centery
                                distance = math.sqrt(dx ** 2 + dy ** 2)
                                if distance > 0:
                                    cos_a, sin_a = math.cos(angle), math.sin(angle)
                                    new_dx, new_dy = dx * cos_a - dy * sin_a, dx * sin_a + dy * cos_a
                                    target_x, target_y = player.rect.centerx + new_dx, player.rect.centery + new_dy
                                else:
                                    target_x, target_y = player.rect.centerx, player.rect.centery - 100
                                # Create projectile with normal homing, yellow color, and variable size for auto-fire
                                projectiles.append(
                                    Projectile(player.rect.centerx, player.rect.centery, target_x, target_y, player.vx,
                                               player.vy, HOMING_STRENGTH, AUTO_FIRE_COLOR, size_multiplier))
                        auto_fire_timer = 0

                # Spawning logic
                spawn_timer += 1
                if spawn_timer >= spawn_delay:
                    if len(circles) + len(projectiles) + len(particles) < max_objects:
                        circles.append(Circle())
                    spawn_timer = 0
                    spawn_delay = max(8, spawn_delay - 0.1)

                # Check circle-to-circle collisions
                circles_to_destroy = set()
                for i, circle1 in enumerate(circles):
                    for circle2 in circles[i + 1:]:
                        if circle1.collides_with_circle(circle2):
                            circles_to_destroy.add(circle1)
                            circles_to_destroy.add(circle2)
                if circles_to_destroy:
                    for circle in circles_to_destroy:
                        destroy_circle(circle, circles, particles, max_objects)
                    screen_shake_timer = SCREEN_SHAKE_DURATION

                if screen_shake_timer > 0:
                    screen_shake_timer -= 1

                accumulator -= LOGIC_TIMESTEP

            # Rendering
            alpha = accumulator / LOGIC_TIMESTEP
            player_alpha = player_accumulator / PLAYER_LOGIC_TIMESTEP

            # Update particle clouds and remove expired ones
            for cloud in particle_clouds[:]:
                cloud.update(frame_time)
                if cloud.is_expired():
                    particle_clouds.remove(cloud)
                    print(f"Removed expired ParticleCloud at ({cloud.x:.1f}, {cloud.y:.1f})")

            # Print current particle cloud count periodically
            if global_frame_counter % 60 == 0:  # Every second at 60 FPS
                print(f"Current particle clouds: {len(particle_clouds)}, Total particles: {len(particles)}")

            # Update stars
            for star in stars[:]:
                star.update(frame_time)
                if star.is_off_screen():
                    stars.remove(star)
                    stars.append(Star())

            # Draw everything
            screen.fill(BACKGROUND_BLUE)

            for star in stars:
                star.draw(screen)

            for particle in particles:
                if not particle.draw_in_front:
                    particle.draw(screen)

            # Only draw player if not in game over state (even if dying)
            if not game_over:
                player.draw(screen, player_alpha)

            for circle in circles:
                circle.draw(screen, alpha)
            for projectile in projectiles:
                projectile.draw(screen, alpha)

            for particle in particles:
                if particle.draw_in_front:
                    particle.draw(screen)

            # Draw UI
            upgrade_level = 1
            if circle_hits >= 125:
                upgrade_level = 3
            elif circle_hits >= 25:
                upgrade_level = 2
            elif circle_hits >= 0:
                upgrade_level = 1

            # Display score at the top of the screen
            score_text = font_small.render(f"Time: {score:.2f}s", True, WHITE)
            screen.blit(score_text, (10 * SCALE_X, 10 * SCALE_Y))

            upgrade_text = font_small.render(f"Level: {upgrade_level} | Hits: {circle_hits}", True, WHITE)
            screen.blit(upgrade_text, (10 * SCALE_X, 40 * SCALE_Y))

            next_upgrade_map = {1: 25, 2: 125, 3: None}
            next_upgrade = next_upgrade_map.get(upgrade_level)
            if next_upgrade:
                next_text = font_small.render(f"Next upgrade at {next_upgrade} hits", True, WHITE)
                screen.blit(next_text, (10 * SCALE_X, 70 * SCALE_Y))
            else:
                next_text = font_small.render("Max level reached!", True, WHITE)
                screen.blit(next_text, (10 * SCALE_X, 70 * SCALE_Y))

            # Display performance info (only if show_performance is True) - moved after UI elements
            if show_performance:
                # Get current FPS
                current_fps = clock.get_fps()
                fps_text = font_small.render(f"FPS: {current_fps:.1f}", True, WHITE)
                screen.blit(fps_text, (10 * SCALE_X, 100 * SCALE_Y))

                perf_text = font_small.render(f"Max Objects: {max_objects} | Particles: {current_particle_count}", True,
                                              WHITE)
                screen.blit(perf_text, (10 * SCALE_X, 130 * SCALE_Y))

            # Apply screen shake
            if screen_shake_timer > 0:
                shake_offset_x = random.uniform(-2, 2) * SCALE_X
                shake_offset_y = random.uniform(-2, 2) * SCALE_Y
                temp_surface = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
                temp_surface.blit(screen, (0, 0))
                screen.fill(BACKGROUND_BLUE)
                screen.blit(temp_surface, (shake_offset_x, shake_offset_y))

            pygame.display.flip()
            clock.tick()
        else:
            # Game over state - continue updating and drawing game objects
            # Use the same accumulator pattern as the main game loop
            game_over_accumulator += frame_time

            while game_over_accumulator >= LOGIC_TIMESTEP:
                # Update explosions and apply forces to particles
                for explosion in explosions[:]:
                    explosion.update(LOGIC_TIMESTEP)
                    if explosion.is_expired():
                        explosions.remove(explosion)
                    else:
                        # Apply explosion force to all particles
                        for particle in particles:
                            explosion.apply_force(particle)

                        # Apply explosion force to the player and get shake strength
                        # Only apply if player is not in death animation
                        if not player.is_dying:
                            shake_force = explosion.apply_force_to_player(player)
                            if shake_force > 0:
                                player.apply_shake(shake_force)

                # Update circles
                for circle in circles[:]:
                    circle.prev_x, circle.prev_y = circle.x, circle.y
                    circle.update(LOGIC_TIMESTEP)
                    if circle.is_off_screen():
                        circles.remove(circle)

                # Update projectiles
                for projectile in projectiles[:]:
                    projectile.prev_x, projectile.prev_y = projectile.x, projectile.y
                    projectile.update(circles, LOGIC_TIMESTEP)
                    if projectile.is_off_screen():
                        projectiles.remove(projectile)

                # Update stars
                for star in stars[:]:
                    star.update(LOGIC_TIMESTEP)
                    if star.is_off_screen():
                        stars.remove(star)
                        stars.append(Star())

                # Continue spawning circles even in game over state
                spawn_timer += 1  # This is now frame-based, like in the main game
                if spawn_timer >= spawn_delay:
                    if len(circles) + len(projectiles) + len(particles) < max_objects:
                        circles.append(Circle())
                    spawn_timer = 0
                    spawn_delay = max(8, spawn_delay - 0.1)  # Continue increasing spawn rate

                # Check for circle-circle collisions even in game over state
                circles_to_destroy = set()
                for i, circle1 in enumerate(circles):
                    for circle2 in circles[i + 1:]:
                        if circle1.collides_with_circle(circle2):
                            circles_to_destroy.add(circle1)
                            circles_to_destroy.add(circle2)
                if circles_to_destroy:
                    for circle in circles_to_destroy:
                        destroy_circle(circle, circles, particles, max_objects)

                # Check for projectile-circle collisions even in game over state
                for projectile in projectiles[:]:
                    for circle in circles[:]:
                        if projectile.collides_with(circle):
                            if projectile in projectiles:
                                projectiles.remove(projectile)
                            destroy_circle(circle, circles, particles, max_objects)
                            break

                # Update particles
                for particle in particles[:]:
                    particle.update(LOGIC_TIMESTEP)
                    should_remove = False
                    if not particle.is_persistent and particle.lifetime <= 0:
                        should_remove = True
                    elif particle.is_persistent and (particle.is_off_screen() or particle.is_expired()):
                        should_remove = True
                    if should_remove:
                        particles.remove(particle)
                        continue

                # Update particle clouds
                for cloud in particle_clouds[:]:
                    cloud.update(LOGIC_TIMESTEP)
                    if cloud.is_expired():
                        particle_clouds.remove(cloud)

                game_over_accumulator -= LOGIC_TIMESTEP

            # Draw everything
            screen.fill(BACKGROUND_BLUE)

            # Draw stars
            for star in stars:
                star.draw(screen)

            # Draw particles
            for particle in particles:
                if not particle.draw_in_front:
                    particle.draw(screen)

            # Don't draw the player (they're dead)

            # Draw circles
            for circle in circles:
                circle.draw(screen, 1.0)  # Use alpha of 1.0 for game over state

            # Draw projectiles
            for projectile in projectiles:
                projectile.draw(screen, 1.0)  # Use alpha of 1.0 for game over state

            # Draw particles in front
            for particle in particles:
                if particle.draw_in_front:
                    particle.draw(screen)

            # Draw game over screen
            font_large = pygame.font.SysFont(None, int(72 * SCALE_X))
            font_medium = pygame.font.SysFont(None, int(36 * SCALE_X))

            game_over_text = font_large.render("GAME OVER", True, RED)
            score_text = font_medium.render(f"Time survived: {score:.2f} seconds", True, WHITE)
            restart_text = font_medium.render("Press SPACE to play again or ESC to quit", True, WHITE)

            screen.blit(game_over_text,
                        game_over_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - 50 * SCALE_Y)))
            screen.blit(score_text, score_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 20 * SCALE_Y)))
            screen.blit(restart_text,
                        restart_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 80 * SCALE_Y)))

            # Display performance info (only if show_performance is True)
            if show_performance:
                # Get current FPS
                current_fps = clock.get_fps()
                fps_text = font_small.render(f"FPS: {current_fps:.1f}", True, WHITE)
                screen.blit(fps_text, (10 * SCALE_X, 10 * SCALE_Y))

                perf_text = font_small.render(f"Max Objects: {max_objects} | Particles: {current_particle_count}", True,
                                              WHITE)
                screen.blit(perf_text, (10 * SCALE_X, 40 * SCALE_Y))

            pygame.display.flip()
            clock.tick()

            # Handle input for game over screen
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_F2:
                        show_performance = not show_performance  # Toggle performance display
                    elif event.key == pygame.K_SPACE:
                        # Reset game state but keep performance settings
                        game_over = False
                        start_time = time.time()
                        score = 0.0
                        player = Player(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2)
                        circles, projectiles, particles = [], [], []
                        circle_hits = 0
                        auto_fire_timer = 0
                        spawn_timer = 0
                        spawn_delay = 15
                        mouse_held = False
                        single_fire_shot = False
                        mouse_hold_time = 0.0
                        current_fire_delay = AUTO_FIRE_BASE_DELAY
                        last_click_time = 0.0
                        click_count = 0
                        screen_shake_timer = 0
                        accumulator = 0.0
                        player_accumulator = 0.0
                        game_over_accumulator = 0.0
                        explosions = []  # Reset explosions list
                        # Note: We're NOT resetting max_objects or current_particle_count here
                        # This ensures performance settings persist across game sessions
                    elif event.key == pygame.K_ESCAPE:
                        running = False

    pygame.quit()
    sys.exit()


if __name__ == "__main__":
    main()