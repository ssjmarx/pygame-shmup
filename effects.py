# made by SSJMarx with the help of GLM 4.6

import pygame
import random
import time
import math
from constants import *


class Star:
    """Represents a background star."""
    
    def __init__(self, x=None, y=None, direction=None):
        # Random size
        self.size = random.uniform(STAR_MIN_SIZE, STAR_MAX_SIZE) * SCALE_X
        
        # Random color
        self.color = random.choice(STAR_COLORS)
        
        # Twinkle effect
        self.twinkle_speed = random.uniform(0.01, 0.05)
        self.twinkle_phase = random.uniform(0, math.pi * 2)
        self.brightness = random.uniform(0.5, 1.0)
        
        # Position
        if x is None or y is None:
            self._spawn_from_edge(direction)
        else:
            self.x = x
            self.y = y
    
    def _spawn_from_edge(self, direction):
        """Spawns the star at the edge of the screen based on the movement direction."""
        angle = direction
        
        # Normalize angle to 0-2π
        angle = angle % (2 * math.pi)
        
        # Determine which edge to spawn at based on movement direction
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
    
    def update(self, dt, direction):
        """Updates the star's position."""
        # Move the star in the given direction
        self.x += math.cos(direction) * STAR_SPEED * dt
        self.y += math.sin(direction) * STAR_SPEED * dt
        
        # Update twinkle
        self.twinkle_phase += self.twinkle_speed
    
    def draw(self, screen):
        """Draws the star."""
        # Calculate current brightness based on twinkle phase
        current_brightness = self.brightness * (0.7 + 0.3 * math.sin(self.twinkle_phase))
        color = tuple(int(c * current_brightness) for c in self.color)
        pygame.draw.circle(screen, color, (int(self.x), int(self.y)), int(self.size))
    
    def is_off_screen(self):
        """Checks if the star is off-screen."""
        margin = 10
        return (self.x < -margin or self.x > SCREEN_WIDTH + margin or
                self.y < -margin or self.y > SCREEN_HEIGHT + margin)




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

    def update(self, dt):
        """Update the cloud's lifetime."""
        self.lifetime -= dt

    def is_expired(self):
        """Check if the cloud has expired."""
        return self.lifetime <= 0

    def is_too_close(self, x, y, min_distance):
        """Check if a position is too close to this cloud."""
        distance = math.sqrt((self.x - x) ** 2 + (self.y - y) ** 2)
        return distance < min_distance


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


# Global lists for particle effects
particle_clouds = []
explosions = []
