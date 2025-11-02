# made by SSJMarx with help of GLM 4.6

import pygame
from constants import *


def update_debug_display(screen, font_small, clock, max_objects, current_particle_count):
    """Displays performance debug information on screen - DISABLED."""
    # DISABLED: Performance display commented out
    # Get current FPS
    # current_fps = clock.get_fps()
    # fps_text = font_small.render(f"FPS: {current_fps:.1f}", True, WHITE)
    # screen.blit(fps_text, (10 * SCALE_X, 100 * SCALE_Y))

    # perf_text = font_small.render(f"Max Objects: {max_objects} | Particles: {current_particle_count}", True, WHITE)
    # screen.blit(perf_text, (10 * SCALE_X, 130 * SCALE_Y))


def apply_screen_shake(screen, screen_shake_timer):
    """Applies screen shake effect to the display."""
    if screen_shake_timer > 0:
        shake_offset_x = random.uniform(-2, 2) * SCALE_X
        shake_offset_y = random.uniform(-2, 2) * SCALE_Y
        temp_surface = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
        temp_surface.blit(screen, (0, 0))
        screen.blit(temp_surface, (shake_offset_x, shake_offset_y))
