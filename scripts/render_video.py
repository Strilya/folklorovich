#!/usr/bin/env python3
"""
Folklorovich - Video Renderer
FINAL VERSION: Loop, clean subtitles, QuickTime compatible
"""

import subprocess
from pathlib import Path
import logging

logger = logging.getLogger('VideoRenderer')


def create_slideshow_video(
    image_paths: list,
    output_path: str,
    reel_type: str,
    audio_path: str = None,
    music_path: str = None,
    title: str = "",
    subtitles_russian: str = None,
    subtitles_english: str = None,
    image_duration: float = 2.5,
    font_name: str = "Baskerville"
) -> str:
    """Main entry point
    
    Args:
        image_duration: Seconds per image (default 2.5, use 1.2 for custom reels)
        font_name: Font for subtitles (default Baskerville, use Snell Roundhand for imperial)
    """
    if reel_type == "visual":
        return create_visual_reel(image_paths, output_path, music_path)
    else:
        return create_superstition_reel(
            image_paths, output_path, audio_path, music_path,
            subtitles_russian, subtitles_english, image_duration, font_name
        )


def create_visual_reel(image_paths: list, output_path: str, music_path: str) -> str:
    """TYPE A: 15s visual, 12 images, faster switching"""
    
    total_duration = 15.0
    num_images = 12
    
    while len(image_paths) < num_images:
        image_paths.extend(image_paths)
    image_paths = image_paths[:num_images]
    
    logger.info(f"Visual reel: {num_images} images")
    
    inputs = []
    filters = []
    
    # 1.25s per image
    for i, img in enumerate(image_paths):
        inputs.extend(["-loop", "1", "-t", "1.25", "-i", str(img)])
    
    inputs.extend(["-i", music_path])
    
    # Scale
    for i in range(num_images):
        filters.append(f"[{i}:v]scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,setsar=1,fps=25[v{i}]")
    
    # CONCAT
    concat_inputs = "".join([f"[v{i}]" for i in range(num_images)])
    filters.append(f"{concat_inputs}concat=n={num_images}:v=1:a=0[vconcat]")
    
    # FADE TO BLACK at end (last 1.5 seconds)
    filters.append(f"[vconcat]fade=t=out:st=13.5:d=1.5[vfade]")
    
    # END CARD (shows during fade out)
    # @Folklorovich - white, large, bold, centered
    # "Discover Russian Mysteries" - gold/yellow, elegant, below
    filters.append(
        f"[vfade]drawtext=fontfile=/System/Library/Fonts/HelveticaNeue.ttc:"
        f"text='@Folklorovich':fontcolor=white:fontsize=48:x=(w-text_w)/2:y=h/2-70:alpha='if(lt(t,13.5),0,min((t-13.5)/0.3,1))',"
        f"drawtext=fontfile=/System/Library/Fonts/HelveticaNeue.ttc:"
        f"text='Discover Russian Mysteries':fontcolor=0xFFD700:fontsize=22:x=(w-text_w)/2:y=h/2+30:alpha='if(lt(t,13.5),0,min((t-13.5)/0.3,1))'[vout]"
    )
    
    cmd = [
        "ffmpeg", "-y", *inputs,
        "-filter_complex", ";".join(filters),
        "-map", "[vout]", "-map", f"{num_images}:a",
        "-t", str(total_duration),
        "-c:v", "libx264", "-preset", "medium", "-crf", "23",
        "-pix_fmt", "yuv420p",
        "-c:a", "aac", "-b:a", "192k",
        output_path
    ]
    
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(f"FFmpeg failed: {result.stderr}")
    
    logger.info(f"✓ Visual reel: {output_path}")
    return output_path


def create_superstition_reel(image_paths: list, output_path: str, audio_path: str, music_path: str, srt_russian: str, srt_english: str, image_duration: float = 2.5, font_name: str = "Baskerville") -> str:
    """TYPE B: Superstition with clean professional subtitles
    
    Args:
        image_duration: Seconds per image (default 2.5 for superstitions, 1.2 for custom reels)
        font_name: Font for subtitles (default Baskerville for folklore, Snell Roundhand for imperial)
    """
    
    duration = get_audio_duration(audio_path)
    num_images_needed = int(duration / image_duration) + 1
    
    logger.info(f"Superstition reel: {duration:.1f}s, {num_images_needed} images @ {image_duration}s each")
    
    while len(image_paths) < num_images_needed:
        image_paths.extend(image_paths)
    image_paths = image_paths[:num_images_needed]
    
    inputs = []
    filters = []
    
    # Use custom image duration
    for i, img in enumerate(image_paths):
        inputs.extend(["-loop", "1", "-t", str(image_duration), "-i", str(img)])
    
    inputs.extend(["-i", audio_path, "-i", music_path])
    
    # Scale all
    for i in range(len(image_paths)):
        filters.append(f"[{i}:v]scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,setsar=1,fps=25[v{i}]")
    
    # CONCAT (crossfade is broken - stays on 2nd image)
    concat_inputs = "".join([f"[v{i}]" for i in range(len(image_paths))])
    filters.append(f"{concat_inputs}concat=n={len(image_paths)}:v=1:a=0[vconcat]")
    
    final_video = "[vconcat]"
    
    # Russian subtitles TOP - YELLOW, configurable font
    srt_russian_escaped = str(srt_russian).replace('\\', '/').replace(':', '\\:')
    filters.append(
        f"{final_video}subtitles={srt_russian_escaped}:force_style='"
        f"FontName={font_name},FontSize=13,Bold=0,PrimaryColour=&H00FFFF,"
        f"OutlineColour=&H000000,Outline=1,Shadow=2,"
        f"MarginV=650,Alignment=8'[vsub_ru]"
    )
    
    # English subtitles BOTTOM - WHITE, configurable font
    srt_english_escaped = str(srt_english).replace('\\', '/').replace(':', '\\:')
    filters.append(
        f"[vsub_ru]subtitles={srt_english_escaped}:force_style='"
        f"FontName={font_name},FontSize=14,Bold=0,PrimaryColour=&HFFFFFF,"
        f"OutlineColour=&H000000,Outline=1,Shadow=2,"
        f"MarginV=80,Alignment=2'[vsub]"
    )
    
    # Watermark
    filters.append(f"[vsub]drawtext=fontfile=/System/Library/Fonts/Helvetica.ttc:text='@Folklorovich':fontcolor=white@0.2:fontsize=16:x=w-tw-20:y=h-th-20[vwm]")
    
    # FADE TO BLACK at end (last 1.5 seconds)
    filters.append(f"[vwm]fade=t=out:st={duration - 1.5}:d=1.5[vfade]")
    
    # END CARD (same as Type A)
    filters.append(
        f"[vfade]drawtext=fontfile=/System/Library/Fonts/HelveticaNeue.ttc:"
        f"text='@Folklorovich':fontcolor=white:fontsize=48:x=(w-text_w)/2:y=h/2-70:alpha='if(lt(t,{duration - 1.5}),0,min((t-{duration - 1.5})/0.3,1))',"
        f"drawtext=fontfile=/System/Library/Fonts/HelveticaNeue.ttc:"
        f"text='Discover Russian Mysteries':fontcolor=0xFFD700:fontsize=22:x=(w-text_w)/2:y=h/2+30:alpha='if(lt(t,{duration - 1.5}),0,min((t-{duration - 1.5})/0.3,1))'[vout]"
    )
    
    # Audio mix
    narration_idx = len(image_paths)
    music_idx = len(image_paths) + 1
    filters.append(f"[{narration_idx}:a]volume=1.0[voice];[{music_idx}:a]volume=0.15,aloop=loop=-1:size=2e+09[music];[voice][music]amix=inputs=2:duration=first[aout]")
    
    cmd = [
        "ffmpeg", "-y", *inputs,
        "-filter_complex", ";".join(filters),
        "-map", "[vout]", "-map", "[aout]",
        "-t", str(duration),
        "-c:v", "libx264", "-preset", "medium", "-crf", "23",
        "-pix_fmt", "yuv420p",  # QuickTime compatibility
        "-c:a", "aac", "-b:a", "192k",
        output_path
    ]
    
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError("FFmpeg failed")
    
    logger.info(f"✓ Superstition reel: {output_path}")
    return output_path


def get_audio_duration(audio_path: str) -> float:
    cmd = ["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "default=noprint_wrappers=1:nokey=1", audio_path]
    result = subprocess.run(cmd, capture_output=True, text=True, check=True)
    return float(result.stdout.strip())
