# made by SSJMarx with the help of GLM 4.6

import pygame
import sys
from constants import *


def start_game_screen(screen, clock):
    """Displays the start game screen."""
    from main import stars, star_direction  # Import here to avoid circular import
    from effects import Star
    
    font_large = pygame.font.SysFont(None, int(72 * SCALE_X))
    font_medium = pygame.font.SysFont(None, int(36 * SCALE_X))

    waiting = True
    while waiting:
        # Update stars
        for star in stars[:]:
            star.update(1 / 120, star_direction)  # Use a fixed timestep for consistent star movement
            if star.is_off_screen():
                stars.remove(star)
                stars.append(Star(direction=star_direction))

        # Draw everything
        # Draw background first
        screen.fill(BACKGROUND_BLUE)

        # Draw stars
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


def game_over_screen(screen, clock, score):
    """Displays the game over screen."""
    from main import stars, star_direction  # Import here to avoid circular import
    from effects import Star
    
    font_large = pygame.font.SysFont(None, int(72 * SCALE_X))
    font_medium = pygame.font.SysFont(None, int(36 * SCALE_X))

    waiting = True
    while waiting:
        # Update stars
        for star in stars[:]:
            star.update(1 / 120, star_direction)  # Use a fixed timestep for consistent star movement
            if star.is_off_screen():
                stars.remove(star)
                stars.append(Star(direction=star_direction))

        # Draw everything
        # Draw background first
        screen.fill(BACKGROUND_BLUE)

        # Draw stars
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
