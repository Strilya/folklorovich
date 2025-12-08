"""
Beat Detector for Folklorovich
Detects beats in music for synchronized visual transitions

SIMPLE VERSION: Uses evenly-spaced beats (every 1.5s)
Advanced beat detection can be added later with librosa

Author: Folklorovich Project
Date: 2025-12-07
"""

import logging

logger = logging.getLogger('BeatDetector')


def detect_beats(music_path: str, duration: float = 15.0, num_beats: int = 10) -> list:
    """
    Detect beat timestamps in music file.
    
    CURRENT: Simple evenly-spaced beats (reliable, works every time)
    FUTURE: Can upgrade to FFmpeg or librosa for actual beat detection
    
    Args:
        music_path: Path to music file
        duration: Duration to analyze (seconds)
        num_beats: Number of beats to generate
        
    Returns:
        List of beat timestamps in seconds
    """
    
    logger.info(f"Generating {num_beats} evenly-spaced beats over {duration}s")
    
    # Simple approach: evenly space beats
    # For 15s with 10 images = beat every 1.5s
    beat_interval = duration / num_beats
    
    timestamps = [i * beat_interval for i in range(num_beats)]
    
    logger.info(f"Beat timestamps: {[f'{t:.2f}s' for t in timestamps]}")
    
    return timestamps


# Future enhancement: Real beat detection with librosa
def detect_beats_advanced(music_path: str, duration: float = 15.0, num_beats: int = 10) -> list:
    """
    Advanced beat detection using librosa (requires installation)
    
    To use this:
    1. pip install librosa
    2. Uncomment this function
    3. Replace detect_beats() above
    """
    try:
        import librosa
        import numpy as np
        
        # Load audio
        y, sr = librosa.load(music_path, duration=duration)
        
        # Detect beats
        tempo, beat_frames = librosa.beat.beat_track(y=y, sr=sr)
        beat_times = librosa.frames_to_time(beat_frames, sr=sr)
        
        # Limit to num_beats
        if len(beat_times) > num_beats:
            # Sample evenly from detected beats
            indices = np.linspace(0, len(beat_times)-1, num_beats, dtype=int)
            beat_times = beat_times[indices]
        elif len(beat_times) < num_beats:
            # Fallback to evenly spaced if not enough beats detected
            logger.warning(f"Only detected {len(beat_times)} beats, using evenly-spaced")
            return detect_beats(music_path, duration, num_beats)
        
        return beat_times.tolist()
        
    except ImportError:
        logger.warning("librosa not installed, using simple beat detection")
        return detect_beats(music_path, duration, num_beats)
    except Exception as e:
        logger.error(f"Advanced beat detection failed: {e}, using simple")
        return detect_beats(music_path, duration, num_beats)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    # Test beat detection
    beats = detect_beats("test.mp3", duration=15.0, num_beats=10)
    print(f"Detected {len(beats)} beats:")
    for i, beat in enumerate(beats):
        print(f"  Beat {i+1}: {beat:.2f}s")
