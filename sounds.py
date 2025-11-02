# made by SSJMarx with the help of GLM 4.6

import pygame
import numpy as np
from constants import *

# Initialize pygame mixer
pygame.mixer.init(frequency=22050, size=-16, channels=2, buffer=512)

class SoundManager:
    """Manages all game sounds using procedural generation."""
    
    def __init__(self):
        self.sounds = {}
        self.enabled = True
        self.volume = 0.5
        self.generate_all_sounds()
    
    def generate_tone(self, frequency, duration, sample_rate=22050, volume=0.5):
        """Generate a simple sine wave tone."""
        frames = int(duration * sample_rate)
        arr = np.zeros(frames)
        for i in range(frames):
            arr[i] = volume * np.sin(2 * np.pi * frequency * i / sample_rate)
        arr = (arr * 32767).astype(np.int16)
        arr = np.repeat(arr.reshape(frames, 1), 2, axis=1)
        return pygame.sndarray.make_sound(arr)
    
    def generate_blip(self, frequency, duration, sample_rate=22050, volume=0.5):
        """Generate a blip sound with envelope."""
        frames = int(duration * sample_rate)
        arr = np.zeros(frames)
        
        for i in range(frames):
            # Apply envelope (quick attack, quick decay)
            envelope = 1.0
            if i < frames * 0.1:  # Attack
                envelope = i / (frames * 0.1)
            else:  # Decay
                envelope = np.exp(-5 * (i - frames * 0.1) / frames)
            
            arr[i] = volume * envelope * np.sin(2 * np.pi * frequency * i / sample_rate)
        
        arr = (arr * 32767).astype(np.int16)
        arr = np.repeat(arr.reshape(frames, 1), 2, axis=1)
        return pygame.sndarray.make_sound(arr)
    
    def generate_explosion(self, duration, sample_rate=22050, volume=0.5):
        """Generate a very bassy explosion sound like a bass drum with long reverb."""
        frames = int(duration * sample_rate)
        arr = np.zeros(frames)
        
        # Main bass drum hit - very low frequency thump
        for i in range(frames):
            # Primary bass frequency (around 60-80 Hz for deep bass drum)
            bass_freq = 60 + (80 - 60) * (1 - i / frames)  # Slight pitch drop
            arr[i] += volume * 0.8 * np.sin(2 * np.pi * bass_freq * i / sample_rate)
        
        # Add sub-bass rumble (30-40 Hz range)
        for i in range(frames):
            arr[i] += volume * 0.4 * np.sin(2 * np.pi * 35 * i / sample_rate)
        
        # Long reverb tail - multiple delayed low frequencies
        reverb_delays = [0.05, 0.08, 0.12, 0.18]  # Delays in seconds
        reverb_gains = [0.3, 0.2, 0.15, 0.1]
        
        for delay, gain in zip(reverb_delays, reverb_gains):
            delay_frames = int(delay * sample_rate)
            if delay_frames < frames:
                for i in range(delay_frames, frames):
                    # Reverb with lower frequencies
                    reverb_freq = 50 + np.random.uniform(-10, 10)  # Slight frequency variation
                    arr[i] += gain * volume * 0.3 * np.sin(2 * np.pi * reverb_freq * (i - delay_frames) / sample_rate)
                    arr[i] *= np.exp(-0.5 * (i - delay_frames) / (frames - delay_frames))  # Reverb decay
        
        # Apply envelope - slow attack, long decay for drum feel
        for i in range(frames):
            # Quick attack like a drum hit
            if i < frames * 0.02:  # First 2% - attack
                envelope = i / (frames * 0.02)
            else:
                # Long decay with reverb tail
                decay_progress = (i - frames * 0.02) / (frames * 0.98)
                envelope = np.exp(-1.5 * decay_progress)  # Slower decay for longer sustain
            arr[i] *= envelope
        
        # Add subtle noise for texture
        noise = np.random.normal(0, volume * 0.1, frames)
        for i in range(frames):
            noise_envelope = np.exp(-3 * i / frames)  # Quick noise decay
            arr[i] += noise[i] * noise_envelope
        
        arr = np.clip(arr, -1, 1)
        arr = (arr * 32767).astype(np.int16)
        arr = np.repeat(arr.reshape(frames, 1), 2, axis=1)
        return pygame.sndarray.make_sound(arr)
    
    def generate_missile_hiss(self, duration, sample_rate=22050, volume=0.5):
        """Generate a hissy missile launch sound that fades out."""
        frames = int(duration * sample_rate)
        arr = np.zeros(frames)
        
        # Generate white noise for the hiss
        noise = np.random.normal(0, volume * 0.6, frames)
        
        # Apply envelope that fades out
        for i in range(frames):
            # Start loud, fade to silence
            envelope = 1.0 - (i / frames) ** 0.5  # Square root fade for smoother decay
            arr[i] = noise[i] * envelope
        
        # Add some high-frequency components for "whoosh" effect
        for i in range(frames):
            if i < frames * 0.5:  # High frequencies only in first half
                arr[i] += 0.3 * volume * np.sin(2 * np.pi * 3000 * i / sample_rate) * (1 - i / (frames * 0.5))
                arr[i] += 0.2 * volume * np.sin(2 * np.pi * 5000 * i / sample_rate) * (1 - i / (frames * 0.5))
        
        # Add subtle low-frequency rumble for missile launch
        for i in range(frames):
            arr[i] += 0.2 * volume * np.sin(2 * np.pi * 80 * i / sample_rate) * np.exp(-4 * i / frames)
        
        arr = np.clip(arr, -1, 1)
        arr = (arr * 32767).astype(np.int16)
        arr = np.repeat(arr.reshape(frames, 1), 2, axis=1)
        return pygame.sndarray.make_sound(arr)
    
    def generate_sweep(self, start_freq, end_freq, duration, sample_rate=22050, volume=0.5):
        """Generate a frequency sweep sound."""
        frames = int(duration * sample_rate)
        arr = np.zeros(frames)
        
        for i in range(frames):
            # Logarithmic sweep
            t = i / frames
            freq = start_freq * (end_freq / start_freq) ** t
            arr[i] = volume * np.sin(2 * np.pi * freq * i / sample_rate)
        
        arr = (arr * 32767).astype(np.int16)
        arr = np.repeat(arr.reshape(frames, 1), 2, axis=1)
        return pygame.sndarray.make_sound(arr)
    
    def generate_double_beep(self, frequency1, frequency2, duration, sample_rate=22050, volume=0.5):
        """Generate a double beep effect."""
        # First beep
        frames1 = int(duration * 0.4 * sample_rate)
        arr1 = np.zeros(frames1)
        for i in range(frames1):
            envelope = 1.0 if i < frames1 * 0.8 else (frames1 - i) / (frames1 * 0.2)
            arr1[i] = volume * envelope * np.sin(2 * np.pi * frequency1 * i / sample_rate)
        
        # Silence gap
        gap_frames = int(duration * 0.1 * sample_rate)
        gap = np.zeros(gap_frames)
        
        # Second beep
        frames2 = int(duration * 0.4 * sample_rate)
        arr2 = np.zeros(frames2)
        for i in range(frames2):
            envelope = 1.0 if i < frames2 * 0.8 else (frames2 - i) / (frames2 * 0.2)
            arr2[i] = volume * envelope * np.sin(2 * np.pi * frequency2 * i / sample_rate)
        
        # Combine
        arr = np.concatenate([arr1, gap, arr2])
        arr = (arr * 32767).astype(np.int16)
        arr = np.repeat(arr.reshape(len(arr), 1), 2, axis=1)
        return pygame.sndarray.make_sound(arr)
    
    def generate_all_sounds(self):
        """Generate all game sounds."""
        # Player shoot - short high-pitched beep
        self.sounds['shoot'] = self.generate_blip(660, 0.05, volume=0.3)
        
        # Homing missile - hissy missile launch sound
        self.sounds['missile'] = self.generate_missile_hiss(0.3, volume=0.4)
        
        # Projectile hit - medium pitch blip
        self.sounds['hit'] = self.generate_blip(330, 0.1, volume=0.4)
        
        # Circle explosions - different sizes for performance
        self.sounds['explosion_small'] = self.generate_explosion(0.2, volume=0.5)
        self.sounds['explosion_medium'] = self.generate_explosion(0.3, volume=0.7)
        self.sounds['explosion_large'] = self.generate_explosion(0.4, volume=0.9)
        
        # Player death - descending tone
        self.sounds['death'] = self.generate_sweep(880, 110, 0.5, volume=0.6)
        
        # Circle collision - double beep
        self.sounds['collision'] = self.generate_double_beep(440, 220, 0.15, volume=0.4)
        
        # Set volume for all sounds
        for sound in self.sounds.values():
            sound.set_volume(self.volume)
    
    def play_sized_explosion(self, size_factor):
        """Play explosion sound with size-based parameters using pre-generated sounds."""
        if not self.enabled:
            return
        
        # Use pre-generated explosion sounds with size-based selection
        if size_factor < 0.33:
            # Small explosion
            self.sounds['explosion_small'].play()
        elif size_factor < 0.67:
            # Medium explosion
            self.sounds['explosion_medium'].play()
        else:
            # Large explosion
            self.sounds['explosion_large'].play()
    
    def play(self, sound_name):
        """Play a sound by name."""
        if self.enabled and sound_name in self.sounds:
            self.sounds[sound_name].play()
    
    def set_volume(self, volume):
        """Set volume for all sounds (0.0 to 1.0)."""
        self.volume = max(0.0, min(1.0, volume))
        for sound in self.sounds.values():
            sound.set_volume(self.volume)
    
    def toggle(self):
        """Toggle sound on/off."""
        self.enabled = not self.enabled
        return self.enabled

# Global sound manager instance
sound_manager = SoundManager()
