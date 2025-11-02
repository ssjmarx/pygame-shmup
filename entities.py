# made by SSJMarx with the help of GLM 4.6

import pygame
import random
import math
from constants import *


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
        from cache import calculation_cache  # Import cache system
        
        min_split_radius = MIN_SPLIT_RADIUS * SCALE_X

        # Check if the circle is large enough to split
        if self.radius < min_split_radius * 2:
            return []

        # Determine number of splits (2-6)
        num_splits = random.randint(2, 6)

        new_circles = []
        
        # Try to get cached split configuration and angles
        cached_config = calculation_cache.get_cached_split_configuration(num_splits)
        cached_angles = calculation_cache.get_cached_split_angles(num_splits)

        # Calculate the total area we want to distribute (80% of original)
        total_target_area = math.pi * (self.radius ** 2) * 0.8

        # Use cached configuration if available, otherwise generate
        if cached_config:
            size_ratios = cached_config
        else:
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

            # Try to get new cached configuration for the adjusted number
            cached_config = calculation_cache.get_cached_split_configuration(num_splits)
            cached_angles = calculation_cache.get_cached_split_angles(num_splits)

            if cached_config:
                size_ratios = cached_config
            else:
                # Recalculate size ratios with the new number
                size_ratios = []
                remaining_ratio = 1.0

                for i in range(num_splits - 1):
                    ratio = random.uniform(0.1, remaining_ratio * 0.8)
                    size_ratios.append(ratio)
                    remaining_ratio -= ratio

                size_ratios.append(remaining_ratio)
                random.shuffle(size_ratios)

        # Use cached angles if available, otherwise generate
        if cached_angles:
            angles = cached_angles
        else:
            split_angle = random.uniform(0, 2 * math.pi)
            angles = [split_angle + (2 * math.pi * i / num_splits) for i in range(num_splits)]

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

            # Use cached angle if available
            current_angle = angles[i]

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
        from effects import particle_clouds  # Import here to avoid circular import
        from effects import Particle  # Import here to avoid circular import
        from cache import calculation_cache  # Import cache system
        
        particles = []
        available_slots = max_objects - current_objects - OBJECT_BUFFER

        if available_slots > 0:
            # Check if this location is too close to existing particle clouds
            min_distance = 100 * SCALE_X  # Minimum distance between particle clouds
            too_close = False

            for cloud in particle_clouds:
                if cloud.is_too_close(self.x, self.y, min_distance):
                    too_close = True
                    break

            # If too close to another cloud, reduce particle count significantly
            if too_close:
                particle_count = min(2, available_slots)  # Only generate a few particles
            else:
                # Use the current_particle_count (starts at 20, can be reduced by performance system)
                from main import current_particle_count  # Import here to avoid circular import
                particle_count = min(current_particle_count, available_slots)

                # Add a new cloud to track this area
                # Use PARTICLE_LIFETIME as the cloud's lifetime
                from effects import ParticleCloud  # Import here to avoid circular import
                particle_clouds.append(ParticleCloud(self.x, self.y, PARTICLE_LIFETIME))

            # Try to get cached particle pattern
            cached_pattern = calculation_cache.get_cached_particle_pattern(particle_count)
            cached_sizes = calculation_cache.get_cached_particle_sizes(self.radius)
            cached_colors = calculation_cache.get_cached_particle_colors(particle_count)

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

            for i in range(particle_count):
                # Reduced chance of creating persistent particles from 5% to 2%
                is_persistent = random.random() < 0.02

                # Use cached values if available, otherwise fall back to random generation
                if cached_pattern and i < len(cached_pattern):
                    dx, dy = cached_pattern[i]
                    # Scale the cached velocity to match our base speed
                    cached_speed = math.sqrt(dx**2 + dy**2)
                    if cached_speed > 0:
                        dx = (dx / cached_speed) * base_speed
                        dy = (dy / cached_speed) * base_speed
                else:
                    # Fallback to random generation
                    angle = random.uniform(0, 2 * math.pi)
                    velocity_factor = random.uniform(0.7, 1.3)
                    initial_speed = base_speed * velocity_factor
                    dx = math.cos(angle) * initial_speed
                    dy = math.sin(angle) * initial_speed

                # Create particle with initial velocity
                particle = Particle(self.x, self.y, is_persistent, (dx, dy))

                # Use cached size if available, otherwise calculate
                if cached_sizes:
                    particle.size = cached_sizes
                else:
                    # Scale the particle size based on the size ratio
                    # Updated min/max sizes: 8 * SCALE_X to 24 * SCALE_X
                    min_particle_size = 8 * SCALE_X
                    max_particle_size = 24 * SCALE_X
                    particle.size = min_particle_size + (max_particle_size - min_particle_size) * size_ratio

                # Use cached color if available
                if cached_colors and i < len(cached_colors):
                    particle.color = cached_colors[i]

                # Store the initial size for shrinking effect
                particle.initial_size = particle.size

                particles.append(particle)
        return particles
