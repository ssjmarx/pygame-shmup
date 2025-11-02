# made by SSJMarx with help of GLM 4.6

import random
import math
from constants import *
from effects import Explosion, ParticleCloud
from sounds import sound_manager


def destroy_circle(circle, circles_list, particles_list, max_obj_limit, explosions_list):
    """Handles the destruction of a circle, creating splits, particles, and explosions."""
    from cache import calculation_cache  # Import cache system
    
    if circle in circles_list:
        circles_list.remove(circle)
        circles_list.extend(circle.split())
        total_objects = len(circles_list) + len(particles_list)
        new_particles = circle.create_particles(total_objects, max_obj_limit)
        particles_list.extend(new_particles)

        # Try to get cached explosion pattern
        cached_explosion = calculation_cache.get_cached_explosion_pattern()
        cached_multiplier = calculation_cache.get_cached_explosion_multiplier()

        # Create an explosion at the circle's position - size based on circle size
        # Use cached values if available, otherwise fall back to original calculation
        if cached_explosion:
            explosion_radius, _ = cached_explosion  # Use cached radius
        else:
            explosion_radius = circle.radius * 5  # Base radius multiplier
        
        if cached_multiplier:
            explosion_radius = circle.radius * cached_multiplier  # Use cached multiplier
        
        explosion_strength = circle.radius / 10  # Make's explosion strength proportional to circle size

        explosions_list.append(Explosion(circle.x, circle.y, explosion_radius, explosion_strength, 0.5))
        # Play explosion sound with size-based volume and duration
        size_factor = circle.radius / MAX_RADIUS  # Normalize to 0-1 range
        sound_manager.play_sized_explosion(size_factor)


def cleanup_and_update_max(objects_dict, current_max):
    """Cleans up particles and updates max object count on slowdown - DISABLED."""
    # DISABLED: Dynamic optimization code commented out
    # global max_objects, current_particle_count  # Add this to access the global variables

    # particles = objects_dict['particles']
    # total_objects = len(objects_dict['circles']) + len(objects_dict['projectiles']) + len(particles)
    # new_max = int(total_objects * 0.8)
    # new_max = max(new_max, INITIAL_MAX_OBJECTS // 10)

    # # Only print debug message if we're actually reducing the max_objects value
    # if new_max < current_max and new_max < max_objects:
    #     print(f"Slowdown detected! Reducing max_objects from {max_objects} to {new_max}")

    #     # Calculate the percentage of max_objects remaining
    #     percentage_remaining = new_max / max_objects

    #     # Reduce particle count proportionally
    #     new_particle_count = max(1, int(INITIAL_PARTICLE_COUNT * percentage_remaining * 0.5))

    #     # Only print particle message if we're actually reducing it
    #     if new_particle_count < current_particle_count:
    #         print(f"Particle count reduced to {new_particle_count} (was {current_particle_count})")
    #         current_particle_count = new_particle_count

    #     # Update the global max_objects
    #     max_objects = new_max

    # # Calculate how many particles to remove (30% of total)
    # particles_to_remove = int(len(particles) * 0.3)

    # if particles_to_remove > 0:
    #     # Separate particles into categories
    #     non_persistent = [p for p in particles if not p.is_persistent]
    #     persistent = [p for p in particles if p.is_persistent]

    #     # Sort non-persistent by lifetime (oldest first)
    #     non_persistent.sort(key=lambda p: p.lifetime)

    #     # Sort persistent by persistent_timer (oldest first)
    #     persistent.sort(key=lambda p: p.persistent_timer)

    #     # Create a list of particles to remove in the specified order
    #     particles_to_remove_list = []

    #     # 1. Oldest non-persistent particles
    #     remove_count = min(particles_to_remove, len(non_persistent) // 2)
    #     particles_to_remove_list.extend(non_persistent[:remove_count])

    #     # 2. Youngest non-persistent particles
    #     if len(particles_to_remove_list) < particles_to_remove:
    #         remove_count = min(particles_to_remove - len(particles_to_remove_list),
    #                            len(non_persistent) - len(particles_to_remove_list))
    #         particles_to_remove_list.extend(non_persistent[-remove_count:])

    #     # 3. Oldest persistent particles
    #     if len(particles_to_remove_list) < particles_to_remove:
    #         remove_count = min(particles_to_remove - len(particles_to_remove_list),
    #                            len(persistent) // 2)
    #         particles_to_remove_list.extend(persistent[:remove_count])

    #     # 4. Youngest persistent particles
    #     if len(particles_to_remove_list) < particles_to_remove:
    #         remove_count = min(particles_to_remove - len(particles_to_remove_list),
    #                            len(persistent) - len(persistent) // 2)
    #         particles_to_remove_list.extend(persistent[-remove_count:])

    #     # Remove all marked particles at once
    #     for particle in particles_to_remove_list:
    #         if particle in particles:
    #             particles.remove(particle)

    return current_max  # Return unchanged max_objects value
