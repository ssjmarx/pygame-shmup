# made by SSJMarx with the help of GLM 4.6

import pygame
from constants import *


def draw_game_ui(screen, font_small, score, circle_hits):
    """Draws the in-game UI elements."""
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
