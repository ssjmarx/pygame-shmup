# made by SSJMarx with the help of GLM 4.6

import pygame
import math
from constants import *


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
