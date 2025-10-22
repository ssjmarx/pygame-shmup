# made by SSJMarx with the help of GLM 4.6

import pygame
from constants import *


def draw_background(screen):
    """Draws the background of the play area."""
    screen.fill(BACKGROUND_BLUE)




def draw_game_objects(screen, player, circles, projectiles, particles, alpha, player_alpha, game_over):
    """Draws all game objects in the correct order."""
    # Draw particles (background layer)
    for particle in particles:
        if not particle.draw_in_front:
            particle.draw(screen)

    # Draw player (only if not in game over state, even if dying)
    if not game_over:
        player.draw(screen, player_alpha)

    # Draw circles
    for circle in circles:
        circle.draw(screen, alpha)

    # Draw projectiles
    for projectile in projectiles:
        projectile.draw(screen, alpha)

    # Draw particles (foreground layer)
    for particle in particles:
        if particle.draw_in_front:
            particle.draw(screen)


def update_particle_clouds(particle_clouds, frame_time, global_frame_counter, particles=None):
    """Updates particle clouds and removes expired ones."""
    
    # Update particle clouds and remove expired ones
    for cloud in particle_clouds[:]:
        cloud.update(frame_time)
        if cloud.is_expired():
            particle_clouds.remove(cloud)
