# made by SSJMarx with the help of GLM 4.6

import pygame
import random
import math
from constants import *


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
