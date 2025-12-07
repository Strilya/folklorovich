"""
Music Manager for Folklorovich
Handles random music track selection for different reel types.

Author: Folklorovich Project
Date: 2025-12-06
"""

import random
import logging
from pathlib import Path
from typing import List

logger = logging.getLogger('MusicManager')


def get_random_music(reel_type: str) -> str:
    """
    Get random music track based on reel type.

    Args:
        reel_type: "visual" or "superstition"

    Returns:
        Path to music file

    Raises:
        FileNotFoundError: If no music files found in the directory
    """

    if reel_type == "visual":
        music_dir = Path("assets/music/cinematic")
    elif reel_type == "superstition":
        music_dir = Path("assets/music/russian_folk")
    else:
        raise ValueError(f"Invalid reel_type: {reel_type}. Must be 'visual' or 'superstition'")

    # Get all MP3 files
    tracks = list(music_dir.glob("*.mp3"))

    if not tracks:
        raise FileNotFoundError(
            f"No music found in {music_dir}\n"
            f"Please download music tracks and place them in this directory.\n"
            f"See assets/music/README.md for instructions."
        )

    # Return random track
    selected_track = random.choice(tracks)
    logger.info(f"Selected music track: {selected_track.name} from {music_dir.name}")

    return str(selected_track)


def list_available_tracks(reel_type: str = None) -> dict:
    """
    List all available music tracks.

    Args:
        reel_type: Optional filter for "visual" or "superstition"

    Returns:
        Dictionary with track counts and file paths
    """

    result = {}

    if reel_type is None or reel_type == "visual":
        cinematic_dir = Path("assets/music/cinematic")
        cinematic_tracks = list(cinematic_dir.glob("*.mp3"))
        result["cinematic"] = {
            "count": len(cinematic_tracks),
            "tracks": [str(t) for t in cinematic_tracks]
        }

    if reel_type is None or reel_type == "superstition":
        folk_dir = Path("assets/music/russian_folk")
        folk_tracks = list(folk_dir.glob("*.mp3"))
        result["russian_folk"] = {
            "count": len(folk_tracks),
            "tracks": [str(t) for t in folk_tracks]
        }

    return result


if __name__ == "__main__":
    # Test the music manager
    import sys

    logging.basicConfig(level=logging.INFO)

    print("=" * 60)
    print("MUSIC MANAGER TEST")
    print("=" * 60)
    print()

    # List available tracks
    tracks = list_available_tracks()

    print("Available Music Tracks:")
    print()

    for category, data in tracks.items():
        print(f"{category.upper()}:")
        print(f"  Count: {data['count']}")
        if data['tracks']:
            for track in data['tracks']:
                print(f"    - {Path(track).name}")
        else:
            print(f"    ⚠️  No tracks found!")
        print()

    # Test random selection
    if len(sys.argv) > 1:
        reel_type = sys.argv[1]
        try:
            track = get_random_music(reel_type)
            print(f"Random {reel_type} track: {track}")
        except Exception as e:
            print(f"Error: {e}")
