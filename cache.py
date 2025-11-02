# made by SSJMarx with the help of GLM 4.6

import random
import math
import time
from constants import *


class CalculationCache:
    """Caches expensive calculations to improve performance."""
    
    def __init__(self):
        self.is_preloaded = False
        self.cache_timer = 0.0
        self.cache_update_interval = 1.0  # Update every second
        
        # Particle creation caches
        self.particle_velocity_patterns = []      # Pre-calculated velocity patterns
        self.particle_size_distributions = []     # Size distributions by circle size
        self.particle_color_sets = []             # Color variations
        
        # Circle splitting caches
        self.circle_split_configurations = {}     # Key: split_count, Value: list of configurations
        self.split_angle_patterns = {}           # Angle distributions for splits
        
        # Explosion caches
        self.explosion_force_patterns = []       # Force application patterns
        self.explosion_size_multipliers = []     # Size multipliers for different circle sizes
        
        # Performance tracking
        self.cache_hits = 0
        self.cache_misses = 0
    
    def generate_particle_patterns(self):
        """Generate cached particle creation patterns."""
        # Generate velocity patterns (100 patterns)
        for _ in range(100):
            pattern = []
            base_speed = random.uniform(100, 500) * SCALE_X
            for _ in range(20):  # 20 particles per pattern
                angle = random.uniform(0, 2 * math.pi)
                speed_factor = random.uniform(0.7, 1.3)
                velocity = (
                    math.cos(angle) * base_speed * speed_factor,
                    math.sin(angle) * base_speed * speed_factor
                )
                pattern.append(velocity)
            self.particle_velocity_patterns.append(pattern)
        
        # Generate size distributions for different circle size ranges
        size_ranges = [
            (MIN_RADIUS * SCALE_X, MAX_RADIUS * 0.5 * SCALE_X),      # Small circles
            (MAX_RADIUS * 0.5 * SCALE_X, MAX_RADIUS * SCALE_X),        # Medium circles
            (MAX_RADIUS * SCALE_X, MAX_RADIUS * 1.5 * SCALE_X)         # Large circles
        ]
        
        for min_size, max_size in size_ranges:
            distribution = []
            for _ in range(50):
                # Calculate size ratio relative to the range
                size_ratio = random.uniform(0.25, 1.0)
                min_particle_size = 8 * SCALE_X
                max_particle_size = 24 * SCALE_X
                particle_size = min_particle_size + (max_particle_size - min_particle_size) * size_ratio
                distribution.append(particle_size)
            self.particle_size_distributions.append((min_size, max_size, distribution))
        
        # Generate color sets
        for _ in range(30):
            color_set = []
            for _ in range(20):
                color = (
                    random.randint(0, 50),      # Red: 0-50 (very low)
                    random.randint(100, 200),   # Green: 100-200 (moderate)
                    random.randint(200, 255)    # Blue: 200-255 (high)
                )
                color_set.append(color)
            self.particle_color_sets.append(color_set)
    
    def generate_circle_split_patterns(self):
        """Generate cached circle splitting configurations."""
        # Generate patterns for 2-6 splits
        for split_count in range(2, 7):
            configurations = []
            angle_patterns = []
            
            for _ in range(50):  # 50 configurations per split count
                # Size ratios that sum to ~0.8 (80% of original area)
                size_ratios = []
                remaining_ratio = 1.0
                
                for i in range(split_count - 1):
                    ratio = random.uniform(0.1, remaining_ratio * 0.8)
                    size_ratios.append(ratio)
                    remaining_ratio -= ratio
                
                size_ratios.append(remaining_ratio)
                random.shuffle(size_ratios)
                
                # Normalize to ensure sum is 0.8
                total = sum(size_ratios)
                size_ratios = [r * 0.8 / total for r in size_ratios]
                
                configurations.append(size_ratios)
                
                # Generate angle pattern
                base_angle = random.uniform(0, 2 * math.pi)
                angle_pattern = [base_angle + (2 * math.pi * i / split_count) for i in range(split_count)]
                angle_patterns.append(angle_pattern)
            
            self.circle_split_configurations[split_count] = configurations
            self.split_angle_patterns[split_count] = angle_patterns
    
    def generate_explosion_patterns(self):
        """Generate cached explosion patterns."""
        # Generate force patterns for different explosion sizes
        for _ in range(30):
            pattern = []
            base_strength = random.uniform(5, 20)
            radius = random.uniform(100, 300) * SCALE_X
            
            # Generate force application points
            for _ in range(10):
                distance_ratio = random.uniform(0, 1)
                force = base_strength * (1 - distance_ratio ** 2)
                pattern.append((distance_ratio, force))
            
            self.explosion_force_patterns.append((radius, pattern))
        
        # Generate size multipliers for different circle sizes
        for _ in range(20):
            multiplier = random.uniform(3, 7)  # Explosion radius multiplier
            self.explosion_size_multipliers.append(multiplier)
    
    def get_cached_particle_pattern(self, particle_count):
        """Get a cached particle creation pattern."""
        if not self.particle_velocity_patterns:
            return None
        
        self.cache_hits += 1
        pattern = random.choice(self.particle_velocity_patterns)
        return pattern[:particle_count] if len(pattern) >= particle_count else pattern
    
    def get_cached_particle_sizes(self, circle_radius):
        """Get cached particle sizes for a given circle radius."""
        for min_size, max_size, distribution in self.particle_size_distributions:
            if min_size <= circle_radius <= max_size:
                self.cache_hits += 1
                return random.choice(distribution[:20])  # Return up to 20 sizes
        return None
    
    def get_cached_particle_colors(self, particle_count):
        """Get cached particle colors."""
        if not self.particle_color_sets:
            return None
        
        self.cache_hits += 1
        color_set = random.choice(self.particle_color_sets)
        return color_set[:particle_count] if len(color_set) >= particle_count else color_set
    
    def get_cached_split_configuration(self, split_count):
        """Get cached circle split configuration."""
        if split_count not in self.circle_split_configurations:
            return None
        
        self.cache_hits += 1
        return random.choice(self.circle_split_configurations[split_count])
    
    def get_cached_split_angles(self, split_count):
        """Get cached split angle pattern."""
        if split_count not in self.split_angle_patterns:
            return None
        
        self.cache_hits += 1
        return random.choice(self.split_angle_patterns[split_count])
    
    def get_cached_explosion_pattern(self):
        """Get cached explosion pattern."""
        if not self.explosion_force_patterns:
            return None
        
        self.cache_hits += 1
        return random.choice(self.explosion_force_patterns)
    
    def get_cached_explosion_multiplier(self):
        """Get cached explosion size multiplier."""
        if not self.explosion_size_multipliers:
            return 5.0  # Default multiplier
        
        self.cache_hits += 1
        return random.choice(self.explosion_size_multipliers)
    
    def update_cache(self, dt):
        """Update cache periodically (called every second)."""
        self.cache_timer += dt
        
        if self.cache_timer >= self.cache_update_interval:
            self.cache_timer = 0.0
            
            # Add a few new patterns to keep things fresh
            if len(self.particle_velocity_patterns) < 200:
                # Add 5 new particle patterns
                for _ in range(5):
                    pattern = []
                    base_speed = random.uniform(100, 500) * SCALE_X
                    for _ in range(20):
                        angle = random.uniform(0, 2 * math.pi)
                        speed_factor = random.uniform(0.7, 1.3)
                        velocity = (
                            math.cos(angle) * base_speed * speed_factor,
                            math.sin(angle) * base_speed * speed_factor
                        )
                        pattern.append(velocity)
                    self.particle_velocity_patterns.append(pattern)
            
            # Remove oldest patterns if cache gets too large
            if len(self.particle_velocity_patterns) > 200:
                self.particle_velocity_patterns = self.particle_velocity_patterns[-150:]
    
    def preload_all(self):
        """Preload all cache data."""
        print("Preloading calculations...")
        start_time = time.time()
        
        self.generate_particle_patterns()
        self.generate_circle_split_patterns()
        self.generate_explosion_patterns()
        
        self.is_preloaded = True
        elapsed = time.time() - start_time
        print(f"Cache preload completed in {elapsed:.2f} seconds")
        
        return elapsed


# Global cache instance
calculation_cache = CalculationCache()
