# made by SSJMarx with the help of GLM 4.6

import pygame
import math
import time
from constants import *


def draw_circular_progress(screen, progress, center_x, center_y, radius=50):
    """Draw a circular progress indicator with a rotating inner circle."""
    # Draw outer circle outline
    pygame.draw.circle(screen, WHITE, (int(center_x), int(center_y)), radius, 3)
    
    # Calculate inner circle position (rotating around outer circle)
    angle = progress * 2 * math.pi  # Full rotation = 1.0 progress
    inner_radius = radius * 0.3  # Inner circle is 30% of outer radius
    
    # Position inner circle so its edge touches the outer circle edge
    distance = radius - inner_radius
    inner_x = center_x + math.cos(angle) * distance
    inner_y = center_y + math.sin(angle) * distance
    
    # Draw inner filled circle
    pygame.draw.circle(screen, (0, 255, 100), (int(inner_x), int(inner_y)), int(inner_radius))


def show_loading_screen(screen, clock, preload_function):
    """Show loading screen with circular progress indicator while preloading."""
    screen.fill(BACKGROUND_BLUE)
    
    # Start preload in background
    import threading
    preload_complete = False
    preload_result = None
    preload_error = None
    
    def preload_worker():
        nonlocal preload_complete, preload_result, preload_error
        try:
            preload_result = preload_function()
            preload_complete = True
        except Exception as e:
            preload_error = e
            preload_complete = True
    
    # Start preload thread
    preload_thread = threading.Thread(target=preload_worker)
    preload_thread.start()
    
    # Track rotation animation
    start_time = time.time()
    estimated_duration = 2.0  # Estimate 2 seconds for preload
    minimum_display_time = 0.5  # Minimum 0.5 second display time
    
    loading_complete = False
    fade_out = False
    fade_alpha = 0
    fade_duration = 0.5  # 0.5 second fade out
    
    font_large = pygame.font.SysFont(None, int(48 * SCALE_X))
    font_small = pygame.font.SysFont(None, int(24 * SCALE_X))
    
    # Create fade surface
    fade_surface = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
    fade_surface.set_alpha(0)  # Start transparent
    fade_surface.fill(BACKGROUND_BLUE)
    
    while not loading_complete:
        frame_time = clock.tick(60) / 1000.0
        
        # Calculate continuous rotation for the small circle (continues during fade)
        elapsed = time.time() - start_time
        rotation_speed = 1.0  # Rotations per second
        continuous_rotation = (elapsed * rotation_speed) % 1.0  # Always 0-1, loops continuously
        
        # Calculate simulated progress for the percentage display
        simulated_progress = min(elapsed / estimated_duration, 0.95)  # Cap at 95% until actually complete
        
        # Check if preload is actually complete AND minimum time has passed
        if preload_complete and elapsed >= minimum_display_time and not fade_out:
            fade_out = True
            fade_start_time = time.time()
        
        # Handle fade out - fade from transparent to opaque
        if fade_out:
            fade_elapsed = time.time() - fade_start_time
            fade_alpha = int(255 * min(fade_elapsed / fade_duration, 1.0))  # Go from 0 to 255
            fade_surface.set_alpha(fade_alpha)
            
            if fade_elapsed >= fade_duration:
                loading_complete = True
                if preload_error:
                    print(f"Preload error: {preload_error}")
        
        # Draw loading screen
        screen.fill(BACKGROUND_BLUE)
        
        # Draw title
        title_text = font_large.render("LOADING", True, WHITE)
        title_rect = title_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - 100 * SCALE_Y))
        screen.blit(title_text, title_rect)
        
        # Draw circular progress indicator with continuous rotation
        center_x = SCREEN_WIDTH // 2
        center_y = SCREEN_HEIGHT // 2
        draw_circular_progress(screen, continuous_rotation, center_x, center_y, 60 * SCALE_X)
        
        # Draw progress percentage
        font_progress = pygame.font.SysFont(None, int(36 * SCALE_X))
        progress_text = font_progress.render(f"{int(simulated_progress * 100)}%", True, WHITE)
        progress_rect = progress_text.get_rect(center=(center_x, center_y + 80 * SCALE_Y))
        screen.blit(progress_text, progress_rect)
        
        # Draw loading text
        if not fade_out:
            if simulated_progress < 1.0:
                loading_text = font_small.render("Preloading game assets...", True, WHITE)
            else:
                loading_text = font_small.render("Ready!", True, (0, 255, 100))
            
            loading_rect = loading_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 120 * SCALE_Y))
            screen.blit(loading_text, loading_rect)
        
        # Apply fade overlay (covers loading screen to reveal game underneath)
        if fade_out:
            screen.blit(fade_surface, (0, 0))
        
        pygame.display.flip()
    
    return preload_result
