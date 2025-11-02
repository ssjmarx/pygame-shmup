# made by SSJMarx with the help of GLM 4.6

import pygame
import sys
import time
import math
import random

# Import all modules
from constants import *
from player import Player
from entities import Circle
from projectiles import Projectile
from effects import Particle, Explosion, ParticleCloud, Star
from gamelogic import destroy_circle, cleanup_and_update_max
from ui import draw_game_ui
from debug import update_debug_display, apply_screen_shake
from playarea import draw_game_objects, update_particle_clouds
from sounds import sound_manager
from cache import calculation_cache
from loading import show_loading_screen

# UI states
UI_NONE = "none"
UI_TITLE = "title"
UI_GAME_OVER = "game_over"

# Global variables that need to be shared across modules
particle_clouds = []
explosions = []
stars = []
star_direction = 0
max_objects = INITIAL_MAX_OBJECTS
current_particle_count = INITIAL_PARTICLE_COUNT

# Game state variables
ui_state = UI_TITLE
screen = None
clock = None
font_small = None
player = None
circles = []
projectiles = []
particles = []
score = 0.0
circle_hits = 0
show_performance = False
start_time = 0.0
game_over = False
accumulator = 0.0
player_accumulator = 0.0
game_over_accumulator = 0.0
global_frame_counter = 0
last_cleanup_frame = 0
screen_shake_timer = 0
mouse_held = False
auto_fire_timer = 0
spawn_timer = 0
spawn_delay = 15
single_fire_shot = False
mouse_hold_time = 0.0
current_fire_delay = AUTO_FIRE_BASE_DELAY
last_click_time = 0.0
click_count = 0
play_missile_sound = False
play_shoot_sound = False


def initialize_game():
    """Initialize game components."""
    global screen, clock, font_small, stars, star_direction, player
    
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption("Dodge the Circles")
    clock = pygame.time.Clock()
    font_small = pygame.font.SysFont(None, int(24 * SCALE_X))
    
    # Initialize game components during loading
    def initialize_all_game_components():
        # Preload calculations
        if not calculation_cache.is_preloaded:
            calculation_cache.preload_all()
        
        # Initialize stars
        if not stars:
            star_direction = random.uniform(0, 2 * math.pi)
            for _ in range(STAR_COUNT):
                stars.append(Star(random.uniform(0, SCREEN_WIDTH), random.uniform(0, SCREEN_HEIGHT)))
        
        # Initialize player
        player = Player(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2)
        
        return True
    
    # Show loading screen while initializing everything
    show_loading_screen(screen, clock, initialize_all_game_components)


def reset_game():
    """Reset game to initial state."""
    global ui_state, player, circles, projectiles, particles, score, circle_hits
    global game_over, start_time, accumulator, player_accumulator, game_over_accumulator
    global mouse_held, auto_fire_timer, spawn_timer, spawn_delay, single_fire_shot
    global mouse_hold_time, current_fire_delay, last_click_time, click_count
    global screen_shake_timer, explosions
    
    ui_state = UI_NONE
    player = Player(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2)
    circles = []
    projectiles = []
    particles = []
    score = 0.0
    circle_hits = 0
    game_over = False
    start_time = time.time()
    accumulator = 0.0
    player_accumulator = 0.0
    game_over_accumulator = 0.0
    mouse_held = False
    auto_fire_timer = 0
    spawn_timer = 0
    spawn_delay = 15
    single_fire_shot = False
    mouse_hold_time = 0.0
    current_fire_delay = AUTO_FIRE_BASE_DELAY
    last_click_time = 0.0
    click_count = 0
    screen_shake_timer = 0
    explosions = []


def player_logic(dt, events=None):
    """Handle player input and movement at 120 FPS."""
    global player, mouse_held, single_fire_shot, mouse_hold_time, current_fire_delay
    global last_click_time, click_count, current_time
    
    # Update player movement
    player.prev_rect = player.rect.copy()
    player.move(pygame.key.get_pressed(), dt)
    
    # Handle mouse events
    current_time = time.time()
    if events:
        for event in events:
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_F2:
                    global show_performance
                    show_performance = not show_performance
                elif event.key == pygame.K_m:
                    # Toggle sound on/off
                    sound_manager.toggle()
                    print(f"Sound {'enabled' if sound_manager.enabled else 'disabled'}")
                elif event.key == pygame.K_EQUALS or event.key == pygame.K_PLUS:
                    # Increase volume
                    new_volume = min(1.0, sound_manager.volume + 0.1)
                    sound_manager.set_volume(new_volume)
                    print(f"Volume: {int(new_volume * 100)}%")
                elif event.key == pygame.K_MINUS:
                    # Decrease volume
                    new_volume = max(0.0, sound_manager.volume - 0.1)
                    sound_manager.set_volume(new_volume)
                    print(f"Volume: {int(new_volume * 100)}%")
            if event.type == pygame.MOUSEBUTTONDOWN:
                mouse_held = True
                single_fire_shot = False
                mouse_hold_time = 0.0
                current_fire_delay = AUTO_FIRE_BASE_DELAY
                
                # Check for rapid clicking
                if current_time - last_click_time < RAPID_CLICK_THRESHOLD:
                    click_count += 1
                else:
                    click_count = 1
                last_click_time = current_time
                
            if event.type == pygame.MOUSEBUTTONUP:
                mouse_held = False
                single_fire_shot = False
                mouse_hold_time = 0.0
                current_fire_delay = AUTO_FIRE_BASE_DELAY
                
                # Check for rapid clicking
                if current_time - last_click_time < RAPID_CLICK_THRESHOLD:
                    click_count += 1
                else:
                    click_count = 1
                last_click_time = current_time
    
    return True


def get_projectile_count():
    """Determine projectile count based on current upgrade level."""
    global circle_hits
    if circle_hits >= 125:
        return 5
    elif circle_hits >= 25:
        return 3
    else:
        return 1


def game_logic(dt):
    """Update game logic at 20 FPS."""
    global circles, projectiles, particles, explosions, particle_clouds
    global spawn_timer, spawn_delay, auto_fire_timer, current_fire_delay
    global mouse_held, mouse_hold_time, single_fire_shot, circle_hits
    global last_click_time, current_time, screen_shake_timer, game_over
    global player, score, start_time
    global play_missile_sound, play_shoot_sound  # Sound trigger flags
    
    # Reset sound triggers
    play_missile_sound = False
    play_shoot_sound = False
    
    # Update score (only if not game over)
    if not game_over:
        score = time.time() - start_time
    
    # Update circles
    for circle in circles[:]:
        circle.prev_x, circle.prev_y = circle.x, circle.y
        circle.update(dt)
        if circle.is_off_screen():
            circles.remove(circle)
            continue
        if player is not None and circle.collides_with(player) and not player.is_dying:
            # Start death animation
            player.start_death_animation()
            
            # Create particles for player death
            total_objects = len(circles) + len(projectiles) + len(particles)
            available_slots = max_objects - total_objects - OBJECT_BUFFER
            max_death_particles = 50
            particle_count = min(max_death_particles, available_slots, current_particle_count * 2)
            
            player_size_scale = 1.0
            for _ in range(particle_count):
                is_persistent = random.random() < 0.05
                particle = Particle(player.rect.centerx, player.rect.centery, is_persistent)
                
                min_particle_size = 8 * SCALE_X
                max_particle_size = 24 * SCALE_X
                particle.size = min_particle_size + (
                    max_particle_size - min_particle_size) * player_size_scale
                particle.initial_size = particle.size
                
                angle = random.uniform(0, 2 * math.pi)
                speed = random.uniform(5, 15) * SCALE_X
                particle.dx = math.cos(angle) * speed
                particle.dy = math.sin(angle) * speed
                particles.append(particle)
            
            explosions.append(Explosion(player.rect.centerx, player.rect.centery,
                                        200 * SCALE_X, 10.0, 0.5))
            player.apply_shake(10.0)
            sound_manager.play('death')
    
    # Update player death animation
    if player is not None and player.is_dying:
        if player.update_death_animation(dt):
            game_over = True
            global ui_state
            ui_state = UI_GAME_OVER
    
    # Update projectiles
    for projectile in projectiles[:]:
        projectile.update(circles, dt)
        if projectile.is_off_screen():
            projectiles.remove(projectile)
            continue
        for circle in circles[:]:
            if projectile.collides_with(circle):
                if projectile in projectiles:
                    projectiles.remove(projectile)
                circle_hits += 1
                destroy_circle(circle, circles, particles, max_objects, explosions)
                screen_shake_timer = SCREEN_SHAKE_DURATION
                break
    
    # Update particles
    particles_to_remove = []
    for particle in particles:
        particle.update(dt)
        if particle.is_expired() or particle.is_off_screen():
            particles_to_remove.append(particle)
    
    for particle in particles_to_remove:
        if particle in particles:
            particles.remove(particle)
    
    # Update explosions
    for explosion in explosions[:]:
        explosion.update(dt)
        if explosion.is_expired():
            explosions.remove(explosion)
        else:
            # Apply explosion force to all particles
            for particle in particles:
                explosion.apply_force(particle)

            # Apply explosion force to the player and get shake strength
            if player is not None:
                shake_force = explosion.apply_force_to_player(player)
                if shake_force > 0:
                    player.apply_shake(shake_force)

                # Apply additional direct explosion force to player (from original)
                dx = player.rect.centerx - explosion.x
                dy = player.rect.centery - explosion.y
                distance = math.sqrt(dx ** 2 + dy ** 2)
                if 0 <= distance < explosion.radius:
                    distance_ratio = distance / explosion.radius
                    force = explosion.strength * (1 - distance_ratio ** 2) * 3.0  # Triple the effect on player
                    if distance > 0:
                        player.vx += (dx / distance) * force
                        player.vy += (dy / distance) * force
                        player.apply_push_visual()  # Trigger visual effect
    
    # Update mouse hold time and firing rate
    if mouse_held:
        mouse_hold_time += dt
        hold_ratio = min(1.0, mouse_hold_time / AUTO_FIRE_RAMP_UP_TIME)
        current_fire_delay = AUTO_FIRE_BASE_DELAY - (
            AUTO_FIRE_BASE_DELAY - AUTO_FIRE_MIN_DELAY) * hold_ratio
    
    size_multiplier = 1.0 + (PROJECTILE_MAX_SIZE_MULTIPLIER - 1.0) * (
        1.0 - current_fire_delay / AUTO_FIRE_BASE_DELAY)
    
    is_single_shot = (click_count == 1 and not single_fire_shot and
                      (current_time - last_click_time) < RAPID_CLICK_THRESHOLD)
    
    # Handle firing - completely rewritten logic
    if player is not None and mouse_held and not player.is_dying:
        # Check if this should be a single shot (homing) or auto-fire
        if is_single_shot and not single_fire_shot:
            # Single click - fire homing shots
            projectile_count = get_projectile_count()
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
                    projectiles.append(
                        Projectile(player.rect.centerx, player.rect.centery, target_x, target_y, player.vx,
                                   player.vy, SINGLE_FIRE_HOMING_STRENGTH, SINGLE_FIRE_COLOR,
                                   SINGLE_FIRE_SIZE_MULTIPLIER))
                    play_missile_sound = True
            single_fire_shot = True
        
        else:
            # Auto-fire logic (either holding mouse or single shot was already used)
            auto_fire_timer += 1  # Increment by frame count since we're in 20 FPS loop
            
            # Calculate current fire delay based on hold time (ramp-up effect)
            if mouse_held:
                mouse_hold_time += dt
                hold_ratio = min(1.0, mouse_hold_time / AUTO_FIRE_RAMP_UP_TIME)
                current_fire_delay = AUTO_FIRE_BASE_DELAY - (
                    AUTO_FIRE_BASE_DELAY - AUTO_FIRE_MIN_DELAY) * hold_ratio
            else:
                current_fire_delay = AUTO_FIRE_BASE_DELAY
            
            # Check if it's time to fire
            if auto_fire_timer >= current_fire_delay:
                projectile_count = get_projectile_count()
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
                        projectiles.append(
                            Projectile(player.rect.centerx, player.rect.centery, target_x, target_y, player.vx,
                                       player.vy, HOMING_STRENGTH, AUTO_FIRE_COLOR, size_multiplier))
                        play_shoot_sound = True
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
        # sound_manager.play('collision')  # Commented out - destruction sounds provide enough feedback
        for circle in circles_to_destroy:
            destroy_circle(circle, circles, particles, max_objects, explosions)
        screen_shake_timer = SCREEN_SHAKE_DURATION
    
    if screen_shake_timer > 0:
        screen_shake_timer -= 1
    
    # Update particle clouds (moved from render loop to 20 FPS)
    update_particle_clouds(particle_clouds, LOGIC_TIMESTEP, global_frame_counter, particles)
    
    # Update stars (moved from render loop to 20 FPS)
    for star in stars[:]:
        star.update(LOGIC_TIMESTEP, star_direction)
        if star.is_off_screen():
            stars.remove(star)
            stars.append(Star(direction=star_direction))
    
    # Update cache system
    calculation_cache.update_cache(LOGIC_TIMESTEP)
    
    # Play sounds based on trigger flags (moved to 20 FPS loop for performance)
    if play_missile_sound:
        sound_manager.play('missile')
    if play_shoot_sound:
        sound_manager.play('shoot')


def render():
    """Render everything at variable FPS (capped at 120)."""
    global screen, font_small, player, circles, projectiles, particles
    global stars, ui_state, score, circle_hits, show_performance
    global accumulator, player_accumulator, game_over_accumulator
    
    # Calculate interpolation values
    alpha = accumulator / LOGIC_TIMESTEP
    player_alpha = player_accumulator / PLAYER_LOGIC_TIMESTEP
    
    # Draw background
    screen.fill(BACKGROUND_BLUE)
    
    # Draw stars
    for star in stars:
        star.draw(screen)
    
    # Always draw game objects (player is drawn only when not game over)
    should_draw_player = not game_over
    draw_game_objects(screen, player if should_draw_player else None, circles, projectiles, particles, alpha, player_alpha, game_over)
    
    # Draw UI
    draw_game_ui(screen, font_small, score, circle_hits)
    
    # Draw performance info
    if show_performance:
        update_debug_display(screen, font_small, clock, max_objects, current_particle_count)
    
    # Draw UI overlays
    if ui_state == UI_TITLE:
        # Draw title overlay
        font_large = pygame.font.SysFont(None, int(72 * SCALE_X))
        font_medium = pygame.font.SysFont(None, int(36 * SCALE_X))
        
        title_text = font_large.render("DODGE THE CIRCLES", True, WHITE)
        start_text = font_medium.render("Press SPACE to start or ESC to quit", True, WHITE)
        
        screen.blit(title_text, title_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - 50 * SCALE_Y)))
        screen.blit(start_text, start_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 20 * SCALE_Y)))
        
    elif ui_state == UI_GAME_OVER:
        # Draw game over overlay
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
    
    # Apply screen shake (only when playing)
    if ui_state == UI_NONE:
        apply_screen_shake(screen, screen_shake_timer)
    
    pygame.display.flip()


def main():
    """Main game function - continuous game logic with UI overlays."""
    global ui_state, accumulator, player_accumulator, game_over_accumulator
    global global_frame_counter, last_cleanup_frame, spawn_timer, spawn_delay
    global circles, projectiles, particles, explosions, particle_clouds, max_objects
    
    initialize_game()
    
    running = True
    while running:
        frame_time = clock.get_time() / 1000.0
        accumulator += frame_time
        player_accumulator += frame_time
        game_over_accumulator += frame_time
        global_frame_counter += 1
        
        # Collect all events for this frame
        events = pygame.event.get()
        
        # Handle input for UI overlays
        for event in events:
            if event.type == pygame.QUIT:
                running = False
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE:
                    if ui_state == UI_TITLE:
                        reset_game()
                    elif ui_state == UI_GAME_OVER:
                        reset_game()
                elif event.key == pygame.K_ESCAPE:
                    running = False
        
        # Handle player input only when no UI overlay is active
        if ui_state == UI_NONE:
            if not player_logic(PLAYER_LOGIC_TIMESTEP, events):
                running = False
        
        # Update game logic at 20 FPS (always runs)
        while accumulator >= LOGIC_TIMESTEP:
            game_logic(LOGIC_TIMESTEP)
            accumulator -= LOGIC_TIMESTEP
        
        # Update player accumulator (only when no UI overlay)
        while player_accumulator >= PLAYER_LOGIC_TIMESTEP:
            if ui_state == UI_NONE:
                player_logic(PLAYER_LOGIC_TIMESTEP)
                # Update player shake effect
                player.update_shake()
            player_accumulator -= PLAYER_LOGIC_TIMESTEP
        
        # Update game over accumulator
        while game_over_accumulator >= LOGIC_TIMESTEP:
            game_over_accumulator -= LOGIC_TIMESTEP
        
        # Performance monitoring - DISABLED
        # if global_frame_counter % FPS_CHECK_INTERVAL == 0:
        #     current_fps = clock.get_fps()
        #     if current_fps < 60 and (global_frame_counter - last_cleanup_frame) > FPS_CHECK_INTERVAL * 2:
        #         objects_dict = {'circles': circles, 'projectiles': projectiles, 'particles': particles}
        #         max_objects = cleanup_and_update_max(objects_dict, max_objects)
        #         particles = objects_dict['particles']
        #         last_cleanup_frame = global_frame_counter
        
        # Render everything with UI overlays
        render()
        clock.tick(120)

if __name__ == "__main__":
    main()
