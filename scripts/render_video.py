#!/usr/bin/env python3
"""
Folklorovich - Slideshow Video Renderer
Creates slideshow videos with crossfades for both visual and superstition reels.

Features:
- TYPE A: Visual reels (15s, fast crossfades, loud music)
- TYPE B: Superstition reels (25-32s, smooth crossfades, dual subtitles, quiet music)
- 1080x1920 vertical format (Instagram Reels)
- Ken Burns effect and crossfade transitions
- Watermark overlay
- High-quality H.264 encoding

Author: Folklorovich Project
Date: 2025-12-06
"""

import subprocess
from pathlib import Path
import logging
from scripts.beat_detector import detect_beats

logger = logging.getLogger('VideoRenderer')


def create_slideshow_video(
    image_paths: list,
    output_path: str,
    reel_type: str,
    audio_path: str = None,
    music_path: str = None,
    title: str = "",
    subtitles_russian: str = None,
    subtitles_english: str = None
) -> str:
    """
    Create slideshow video with crossfades and watermark

    Args:
        image_paths: List of image file paths
        output_path: Path to save output video
        reel_type: "visual" or "superstition"
        audio_path: Path to narration audio (superstition reels only)
        music_path: Path to background music
        title: Title text (superstition reels only)
        subtitles_russian: Path to Russian SRT file (superstition reels only)
        subtitles_english: Path to English SRT file (superstition reels only)

    Returns:
        Path to created video file
    """
    if reel_type == "visual":
        return create_visual_reel(image_paths, output_path, music_path)
    else:
        return create_superstition_reel(
            image_paths, output_path, audio_path, music_path,
            title, subtitles_russian, subtitles_english
        )


def create_visual_reel(image_paths: list, output_path: str, music_path: str) -> str:
    """
    TYPE A: Visual-Only Reel with BEAT-SYNCED transitions
    - 15 seconds total
    - 10 images with beat-synced durations
    - Fast crossfades (0.3s)
    - LOUD music (100% volume)
    - Only watermark, no other text
    """

    total_duration = 15
    crossfade_duration = 0.3

    # Detect beats in music for synchronized transitions
    logger.info(f"Detecting beats in music: {Path(music_path).name}")
    beat_timestamps = detect_beats(music_path, duration=total_duration, num_beats=10)
    logger.info(f"Beat timestamps: {[f'{b:.2f}s' for b in beat_timestamps]}")

    # Ensure we have exactly 10 images
    if len(image_paths) < 10:
        # Repeat images if needed
        while len(image_paths) < 10:
            image_paths.extend(image_paths[:10 - len(image_paths)])
    image_paths = image_paths[:10]

    logger.info(f"Creating beat-synced visual reel with {len(image_paths)} images...")

    # Calculate duration for each image based on beats
    image_durations = []
    for i in range(len(image_paths)):
        if i < len(beat_timestamps) - 1:
            duration = beat_timestamps[i+1] - beat_timestamps[i]
        else:
            # Last image: fill remaining time
            duration = total_duration - beat_timestamps[i] if i < len(beat_timestamps) else 1.5

        # Ensure minimum duration
        duration = max(0.5, duration)
        image_durations.append(duration)

    logger.info(f"Image durations: {[f'{d:.2f}s' for d in image_durations]}")

    # Build FFmpeg inputs
    inputs = []
    filter_parts = []

    # Add image inputs with beat-synced durations
    for i, (img, duration) in enumerate(zip(image_paths, image_durations)):
        inputs.extend(["-loop", "1", "-t", str(duration), "-i", str(img)])

    # Add music input
    inputs.extend(["-i", music_path])

    # Scale and crop each image to 1080x1920
    for i in range(len(image_paths)):
        filter_parts.append(
            f"[{i}:v]scale=1080:1920:force_original_aspect_ratio=increase,"
            f"crop=1080:1920,setsar=1,format=yuv420p[v{i}]"
        )

    # Create crossfade chain with beat-synced timing
    current = "[v0]"
    for i in range(1, len(image_paths)):
        # Offset is cumulative duration up to this point minus crossfade
        offset = sum(image_durations[:i]) - crossfade_duration
        filter_parts.append(
            f"{current}[v{i}]xfade=transition=fade:duration={crossfade_duration}:"
            f"offset={offset}[vf{i}]"
        )
        current = f"[vf{i}]"

    # Add watermark
    watermark_filter = (
        f"{current}drawtext=fontfile=/System/Library/Fonts/Helvetica.ttc:"
        f"text='@Folklorovich':fontcolor=white@0.2:fontsize=20:"
        f"x=w-tw-25:y=h-th-25[vout]"
    )
    filter_parts.append(watermark_filter)

    # Build command
    cmd = [
        "ffmpeg", "-y",
        *inputs,
        "-filter_complex", ";".join(filter_parts),
        "-map", "[vout]",
        "-map", f"{len(image_paths)}:a",  # Music from last input
        "-t", str(total_duration),
        "-c:v", "libx264",
        "-preset", "medium",
        "-crf", "23",
        "-c:a", "aac",
        "-b:a", "192k",
        "-shortest",
        output_path
    ]

    logger.info("Running FFmpeg for beat-synced visual reel...")
    result = subprocess.run(cmd, capture_output=True, text=True)

    if result.returncode != 0:
        logger.error(f"FFmpeg failed: {result.stderr}")
        raise RuntimeError(f"FFmpeg failed: {result.stderr}")

    logger.info(f"✓ Beat-synced visual reel created: {output_path}")
    return output_path


def create_superstition_reel(
    image_paths: list,
    output_path: str,
    audio_path: str,
    music_path: str,
    title: str,
    srt_russian: str,
    srt_english: str
) -> str:
    """
    TYPE B: Superstition Reel
    - 25-32 seconds (matches audio)
    - 10-13 images (2.5s each)
    - Smooth crossfades (0.5s)
    - QUIET background music (15% volume)
    - Russian narration
    - Dual subtitles (Russian top, English bottom)
    - Watermark
    """

    # Get audio duration
    duration = get_audio_duration(audio_path)
    duration_per_image = 2.5
    crossfade_duration = 0.5
    num_images_needed = int(duration / duration_per_image) + 1

    logger.info(f"Creating superstition reel ({duration:.1f}s, {num_images_needed} images)...")

    # Adjust images
    while len(image_paths) < num_images_needed:
        image_paths.extend(image_paths[:num_images_needed - len(image_paths)])
    image_paths = image_paths[:num_images_needed]

    # Build FFmpeg filter (similar to visual, but with dual audio mix)
    inputs = []
    filter_parts = []

    # Image inputs
    for i, img in enumerate(image_paths):
        inputs.extend(["-loop", "1", "-t", str(duration_per_image), "-i", str(img)])

    # Audio inputs (narration + background music)
    inputs.extend(["-i", audio_path, "-i", music_path])

    # Scale images
    for i in range(len(image_paths)):
        filter_parts.append(
            f"[{i}:v]scale=1080:1920:force_original_aspect_ratio=increase,"
            f"crop=1080:1920,setsar=1,format=yuv420p[v{i}]"
        )

    # Crossfade chain
    current = "[v0]"
    for i in range(1, len(image_paths)):
        offset = duration_per_image * i - crossfade_duration
        filter_parts.append(
            f"{current}[v{i}]xfade=transition=fade:duration={crossfade_duration}:"
            f"offset={offset}[vf{i}]"
        )
        current = f"[vf{i}]"

    # Escape subtitle paths for FFmpeg
    srt_russian_escaped = str(srt_russian).replace('\\', '/').replace(':', '\\:')
    srt_english_escaped = str(srt_english).replace('\\', '/').replace(':', '\\:')

    # Add Russian subtitles (top 25%)
    subtitle_filter_ru = (
        f"{current}subtitles={srt_russian_escaped}:force_style='"
        f"FontName=Arial,FontSize=32,PrimaryColour=&HFFFFFF,"
        f"OutlineColour=&H000000,Outline=2,MarginV=150,Alignment=2"
        f"'[vsub_ru]"
    )
    filter_parts.append(subtitle_filter_ru)

    # Add English subtitles (bottom 25%)
    subtitle_filter_en = (
        f"[vsub_ru]subtitles={srt_english_escaped}:force_style='"
        f"FontName=Arial,FontSize=24,PrimaryColour=&HFFFFFF,"
        f"OutlineColour=&H000000,Outline=2,MarginV=200,Alignment=8"
        f"'[vsub_en]"
    )
    filter_parts.append(subtitle_filter_en)

    # Add watermark
    watermark_filter = (
        f"[vsub_en]drawtext=fontfile=/System/Library/Fonts/Helvetica.ttc:"
        f"text='@Folklorovich':fontcolor=white@0.2:fontsize=20:"
        f"x=w-tw-25:y=h-th-25[vout]"
    )
    filter_parts.append(watermark_filter)

    # Audio mix (voice 100% + music 15%)
    narration_idx = len(image_paths)
    music_idx = len(image_paths) + 1
    audio_filter = (
        f"[{narration_idx}:a]volume=1.0[voice];"
        f"[{music_idx}:a]volume=0.15,aloop=loop=-1:size=2e+09[music];"
        f"[voice][music]amix=inputs=2:duration=first[aout]"
    )
    filter_parts.append(audio_filter)

    # Build command
    cmd = [
        "ffmpeg", "-y",
        *inputs,
        "-filter_complex", ";".join(filter_parts),
        "-map", "[vout]",
        "-map", "[aout]",
        "-c:v", "libx264",
        "-preset", "medium",
        "-crf", "23",
        "-c:a", "aac",
        "-b:a", "192k",
        "-shortest",
        output_path
    ]

    logger.info("Running FFmpeg for superstition reel...")
    result = subprocess.run(cmd, capture_output=True, text=True)

    if result.returncode != 0:
        logger.error(f"FFmpeg failed: {result.stderr}")
        raise RuntimeError(f"FFmpeg failed: {result.stderr}")

    logger.info(f"✓ Superstition reel created: {output_path}")
    return output_path


def get_audio_duration(audio_path: str) -> float:
    """Get audio file duration using ffprobe"""
    cmd = [
        "ffprobe", "-v", "error",
        "-show_entries", "format=duration",
        "-of", "default=noprint_wrappers=1:nokey=1",
        audio_path
    ]
    result = subprocess.run(cmd, capture_output=True, text=True, check=True)
    return float(result.stdout.strip())


if __name__ == "__main__":
    import sys
    logging.basicConfig(level=logging.INFO)

    print("Folklorovich Slideshow Video Renderer")
    print("Usage: import this module and call create_slideshow_video()")
    print("\nTest mode not implemented. Use generate_daily_content.py to create reels.")
