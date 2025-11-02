# Sound System for Dodge the Circles

## Overview
The game now features a procedural sound system that generates classic arcade-style blips and beeps using numpy and pygame. No external sound files are required - all sounds are generated programmatically at runtime.

## Sound Effects

### Currently Implemented:
- **Shoot**: Short high-pitched beep (660Hz, 50ms) - Auto-fire shooting
- **Missile**: Hissy missile launch sound with fade-out (300ms) - Single-click homing shots
- **Explosion**: Deep bassy drum hit with long reverb - Size-based (small/medium/large)
- **Death**: Descending tone sweep (880Hz → 110Hz, 500ms) - Player death
- **Collision**: Double beep effect (440Hz → 220Hz, 150ms) - **DISABLED** (destruction sounds provide enough feedback)

## Sound Controls

### Keyboard Controls:
- **M**: Toggle sound on/off
- **+/=**: Increase volume (10% increments)
- **-**: Decrease volume (10% increments)
- **F2**: Toggle performance display (existing)
- **ESC**: Quit game (existing)

### Volume Levels:
- Volume ranges from 0% to 100%
- Default volume is 50%
- Volume changes are displayed in the console

## Technical Details

### Sound Generation:
- Uses numpy arrays to generate waveforms
- Sample rate: 22050 Hz
- 16-bit audio resolution
- Stereo output

### Sound Types:
1. **Simple Tones**: Pure sine waves
2. **Blips**: Sine waves with envelope (attack/decay)
3. **Explosions**: White noise with low-frequency rumble
4. **Sweeps**: Logarithmic frequency transitions
5. **Double Beeps**: Two-toned effects with gaps

### Performance:
- All sounds are generated once at startup and cached
- Shooting sounds moved to 20 FPS logic loop (from 120 FPS) for better performance
- Collision sound disabled to reduce audio frequency
- Size-based explosion sounds use pre-generated variants instead of dynamic generation
- Minimal CPU overhead during gameplay

## Future Enhancements

### Potential Additions:
- Power-up sounds (rising tones)
- Menu navigation sounds
- Background music (procedural generation)
- Different sound variants based on game events
- Sound visualization effects

### Customization:
- Easy to modify frequencies and durations in `sounds.py`
- Sound constants defined in `constants.py`
- Modular system for adding new sound types

## Troubleshooting

### Common Issues:
1. **No Sound**: Check system volume and mute settings
2. **Crackling**: Try reducing sample rate or buffer size
3. **Performance**: Disable sound if experiencing slowdown (press M)

### Dependencies:
- `pygame` (already required)
- `numpy` (for procedural generation)

## Code Structure

### Files Modified:
- `sounds.py`: New sound management module
- `constants.py`: Added sound constants
- `main.py`: Integrated sound calls and controls
- `gamelogic.py`: Added explosion sound

### Key Classes:
- `SoundManager`: Handles all sound operations
- Procedural generation methods for different sound types

The sound system is designed to be easily extensible and maintainable, following the same modular structure as the rest of the game.
