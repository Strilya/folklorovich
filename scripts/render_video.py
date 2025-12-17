#!/usr/bin/env python3
import subprocess
from pathlib import Path
import logging

logger = logging.getLogger('Renderer')


def get_duration(path: str) -> float:
    cmd = ["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "default=noprint_wrappers=1:nokey=1", str(path)]
    result = subprocess.run(cmd, capture_output=True, text=True)
    return float(result.stdout.strip()) if result.returncode == 0 else 0.0


def render_video(video_paths: list, output_path: str, audio_path: str, music_path: str, srt_english: str, srt_russian: str) -> str:
    audio_dur = get_duration(audio_path)
    clip_dur = audio_dur / len(video_paths)
    
    logger.info(f"Rendering: {audio_dur:.1f}s, {len(video_paths)} clips")
    
    inputs = []
    filters = []
    
    for i, vid in enumerate(video_paths):
        inputs.extend(["-i", str(vid)])
    
    inputs.extend(["-i", str(audio_path), "-i", str(music_path)])
    
    for i in range(len(video_paths)):
        filters.append(
            f"[{i}:v]fps=25,scale=1080:1920:force_original_aspect_ratio=increase,"
            f"crop=1080:1920,setsar=1,format=yuv420p,"
            f"trim=duration={clip_dur:.2f},setpts=PTS-STARTPTS[v{i}]"
        )
    
    concat = "".join([f"[v{i}]" for i in range(len(video_paths))])
    filters.append(f"{concat}concat=n={len(video_paths)}:v=1:a=0[vbase]")
    
    # ENGLISH - YELLOW, 16PX, NO OUTLINE
    srt_en = str(srt_english).replace('\\', '/').replace(':', '\\:')
    filters.append(
        f"[vbase]subtitles={srt_en}:force_style='"
        f"FontName=Arial,FontSize=16,PrimaryColour=&H00FFFF,"
        f"OutlineColour=&H000000,BorderStyle=0,Outline=0,Shadow=0,"
        f"Alignment=2,MarginV=650'[ven]"
    )
    
    # RUSSIAN - WHITE, 16PX, NO OUTLINE
    srt_ru = str(srt_russian).replace('\\', '/').replace(':', '\\:')
    filters.append(
        f"[ven]subtitles={srt_ru}:force_style='"
        f"FontName=Arial,FontSize=16,PrimaryColour=&HFFFFFF,"
        f"OutlineColour=&H000000,BorderStyle=0,Outline=0,Shadow=0,"
        f"Alignment=2,MarginV=250'[vsub]"
    )
    
    # Watermark
    filters.append(
        f"[vsub]drawtext=fontfile=/System/Library/Fonts/Arial.ttf:"
        f"text='@Folklorovich':fontcolor=white@0.8:fontsize=18:"
        f"x=(w-text_w)/2:y=h-th-40[vwm]"
    )
    
    # Fade
    filters.append(f"[vwm]fade=t=out:st={audio_dur-2}:d=1.5[vfade]")
    
    # End card
    filters.append(
        f"[vfade]drawtext=fontfile=/System/Library/Fonts/Arial.ttf:"
        f"text='@Folklorovich':fontcolor=white:fontsize=48:x=(w-text_w)/2:y=h/2-70:"
        f"alpha='if(lt(t,{audio_dur-2}),0,min((t-{audio_dur-2})/0.5,1))',"
        f"drawtext=fontfile=/System/Library/Fonts/Arial.ttf:"
        f"text='Discover Russian Mysteries':fontcolor=0xFFD700:fontsize=24:x=(w-text_w)/2:y=h/2+30:"
        f"alpha='if(lt(t,{audio_dur-2}),0,min((t-{audio_dur-2})/0.5,1))'[vout]"
    )
    
    narr_idx = len(video_paths)
    music_idx = len(video_paths) + 1
    filters.append(
        f"[{narr_idx}:a]volume=1.0[v];"
        f"[{music_idx}:a]volume=0.10,aloop=loop=-1:size=2e+09[m];"
        f"[v][m]amix=inputs=2:duration=first[aout]"
    )
    
    cmd = [
        "ffmpeg", "-y", *inputs,
        "-filter_complex", ";".join(filters),
        "-map", "[vout]", "-map", "[aout]",
        "-t", str(audio_dur),
        "-c:v", "libx264", "-preset", "fast", "-crf", "23",
        "-c:a", "aac", "-b:a", "192k",
        "-movflags", "+faststart",
        str(output_path)
    ]
    
    result = subprocess.run(cmd, capture_output=True, text=True)
    
    if result.returncode != 0:
        logger.error(f"FFmpeg failed:\n{result.stderr[-500:]}")
        raise RuntimeError("FFmpeg failed")
    
    logger.info(f"✅ Done: {output_path}")
    return str(output_path)


def create_slideshow_video(image_paths, output_path, reel_type, audio_path=None, music_path=None, title="", subtitles_russian=None, subtitles_english=None, **kwargs):
    return render_video(image_paths, output_path, audio_path, music_path, subtitles_english, subtitles_russian)
