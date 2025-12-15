#!/usr/bin/env python3
"""
Folklorovich - Three Exhibition Reels Generator
Generates professional reels for three separate exhibitions.
"""

import os
import sys
import json
import random
import logging
from pathlib import Path
from datetime import datetime

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from scripts.render_video import get_audio_duration
from scripts.generate_voice import generate_voice_google, get_audio_duration_ffprobe
from scripts.generate_subtitles import generate_dual_subtitles

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('ExhibitionReels')


def delay_subtitles(input_srt: str, output_srt: str, delay_seconds: float):
    """Delay all subtitle timecodes by specified seconds."""
    with open(input_srt, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    with open(output_srt, 'w', encoding='utf-8') as f:
        for line in lines:
            if '-->' in line:
                parts = line.split('-->')
                start = parts[0].strip()
                end = parts[1].strip()
                
                start_ms = timecode_to_ms(start) + (delay_seconds * 1000)
                end_ms = timecode_to_ms(end) + (delay_seconds * 1000)
                
                f.write(f"{ms_to_timecode(start_ms)} --> {ms_to_timecode(end_ms)}\n")
            else:
                f.write(line)


def timecode_to_ms(tc: str) -> float:
    """Convert SRT timecode to milliseconds."""
    parts = tc.replace(',', ':').split(':')
    h, m, s, ms = map(int, parts)
    return (h * 3600 + m * 60 + s) * 1000 + ms


def ms_to_timecode(ms: float) -> str:
    """Convert milliseconds to SRT timecode."""
    total_seconds = int(ms // 1000)
    milliseconds = int(ms % 1000)
    hours = total_seconds // 3600
    minutes = (total_seconds % 3600) // 60
    seconds = total_seconds % 60
    return f"{hours:02d}:{minutes:02d}:{seconds:02d},{milliseconds:03d}"


def create_title_card(output_path: Path, title: str, subtitle: str, date: str):
    """Create exhibition title card."""
    from PIL import Image, ImageDraw, ImageFont
    
    img = Image.new('RGB', (1080, 1920), color='black')
    draw = ImageDraw.Draw(img)
    
    try:
        font_title = ImageFont.truetype("/System/Library/Fonts/Supplemental/Didot.ttc", 50)
        font_subtitle = ImageFont.truetype("/System/Library/Fonts/Supplemental/Didot.ttc", 36)
    except:
        font_title = ImageFont.load_default()
        font_subtitle = ImageFont.load_default()
    
    # Center text
    bbox1 = draw.textbbox((0, 0), title, font=font_title)
    w1 = bbox1[2] - bbox1[0]
    draw.text((540 - w1/2, 800), title, fill='white', font=font_title)
    
    bbox2 = draw.textbbox((0, 0), subtitle, font=font_subtitle)
    w2 = bbox2[2] - bbox2[0]
    draw.text((540 - w2/2, 900), subtitle, fill='gold', font=font_subtitle)
    
    bbox3 = draw.textbbox((0, 0), date, font=font_subtitle)
    w3 = bbox3[2] - bbox3[0]
    draw.text((540 - w3/2, 970), date, fill='gray', font=font_subtitle)
    
    img.save(output_path)


def render_exhibition_reel(image_paths: list, output_path: str, audio_path: str, 
                          music_path: str, srt_russian: str, srt_english: str,
                          title_card_config: dict, show_end_card: bool = True):
    """Render single exhibition reel with title card and subtitles."""
    import subprocess
    
    audio_duration = get_audio_duration(audio_path)
    num_images = len(image_paths)
    
    # Calculate image duration to fit ALL images into audio time
    # Leave 1 second buffer at end
    available_time = audio_duration - 1.0
    image_duration = available_time / num_images
    
    # Minimum 1 second per image
    if image_duration < 1.0:
        image_duration = 1.0
        logger.warning(f"  ⚠️  Too many images for audio length, using 1s per image")
    
    logger.info(f"  Rendering: 2s title + {num_images} images @ {image_duration:.1f}s each")
    
    inputs = []
    filters = []
    
    # TITLE CARD
    title_card_path = PROJECT_ROOT / "output/temp_title_card.png"
    create_title_card(title_card_path, **title_card_config)
    inputs.extend(["-loop", "1", "-t", "2.0", "-i", str(title_card_path)])
    
    # IMAGES with watermarks
    for img in image_paths:
        inputs.extend(["-loop", "1", "-t", str(image_duration), "-i", str(img)])
    
    # AUDIO
    inputs.extend(["-i", audio_path, "-i", music_path])
    
    # SCALE & WATERMARK
    filters.append("[0:v]scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,setsar=1,fps=25[title]")
    
    for i in range(1, num_images + 1):
        filters.append(
            f"[{i}:v]scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,setsar=1,fps=25,"
            f"drawtext=fontfile=/System/Library/Fonts/Helvetica.ttc:text='@Folklorovich':"
            f"fontcolor=white@0.3:fontsize=24:x=w-tw-30:y=h-th-30[v{i}]"
        )
    
    # SMOOTH TRANSITIONS using overlay with fade
    # First, prepare all images with fade effects
    for i in range(1, num_images + 1):
        # Each image fades in at start (0.5s) and fades out at end (0.5s)
        filters.append(
            f"[v{i}]fade=t=in:st=0:d=0.5,fade=t=out:st={image_duration - 0.5}:d=0.5[vf{i}]"
        )
    
    # Concat with faded images (smooth because of fade in/out)
    concat_inputs = "[title]" + "".join([f"[vf{i}]" for i in range(1, num_images + 1)])
    filters.append(f"{concat_inputs}concat=n={num_images + 1}:v=1:a=0[vbase]")
    
    logger.info(f"     Created fade transitions for {num_images} images")
    
    # DELAYED SUBTITLES (start after 2s title card)
    srt_russian_delayed = str(srt_russian).replace('.srt', '_delayed.srt')
    srt_english_delayed = str(srt_english).replace('.srt', '_delayed.srt')
    delay_subtitles(str(srt_russian), srt_russian_delayed, 2.0)
    delay_subtitles(str(srt_english), srt_english_delayed, 2.0)
    
    srt_russian_escaped = srt_russian_delayed.replace('\\', '/').replace(':', '\\:')
    filters.append(
        f"[vbase]subtitles={srt_russian_escaped}:force_style='"
        f"FontName=Didot,FontSize=12,Italic=1,Bold=0,PrimaryColour=&H00FFFF,"
        f"OutlineColour=&H000000,Outline=1,Shadow=0,"
        f"MarginV=650,Alignment=8'[vsub_ru]"
    )
    
    srt_english_escaped = srt_english_delayed.replace('\\', '/').replace(':', '\\:')
    filters.append(
        f"[vsub_ru]subtitles={srt_english_escaped}:force_style='"
        f"FontName=Didot,FontSize=13,Italic=1,Bold=0,PrimaryColour=&HFFFFFF,"
        f"OutlineColour=&H000000,Outline=1,Shadow=0,"
        f"MarginV=80,Alignment=2'[vsub]"
    )
    
    # END FADE & CARD (based on audio, not video content)
    # Fade starts 2s before audio ends
    fade_start_time = 2 + audio_duration  # After title + audio
    
    if show_end_card:
        filters.append(f"[vsub]fade=t=out:st={fade_start_time}:d=2[vfade]")
        
        # End card shows during fade (last 3s)
        end_card_start = fade_start_time - 1
        filters.append(
            f"[vfade]drawtext=fontfile=/System/Library/Fonts/HelveticaNeue.ttc:"
            f"text='@Folklorovich':fontcolor=white:fontsize=48:x=(w-text_w)/2:y=h/2-70:alpha='if(lt(t,{end_card_start}),0,1)',"
            f"drawtext=fontfile=/System/Library/Fonts/HelveticaNeue.ttc:"
            f"text='Discover Russian Mysteries':fontcolor=0xFFD700:fontsize=22:x=(w-text_w)/2:y=h/2+30:alpha='if(lt(t,{end_card_start}),0,1)'[vout]"
        )
        final_output = "[vout]"
    else:
        filters.append(f"[vsub]fade=t=out:st={fade_start_time}:d=1.5[vfade]")
        final_output = "[vfade]"
    
    # AUDIO MIX (delay narration by 2s to start after title card)
    narration_idx = num_images + 1
    music_idx = num_images + 2
    filters.append(
        f"[{narration_idx}:a]adelay=2000|2000[voice_delayed];"
        f"[voice_delayed]volume=1.0[voice];"
        f"[{music_idx}:a]volume=0.15,aloop=loop=-1:size=2e+09[music];"
        f"[voice][music]amix=inputs=2:duration=first[aout]"
    )
    
    # Calculate actual total duration based on AUDIO (not video content)
    # 2s title + audio duration + 2s delayed audio + 3s end card
    total_duration = 2 + audio_duration + 2 + 3
    
    logger.info(f"     Total duration: {total_duration:.1f}s (2s title + {audio_duration:.1f}s audio + 3s end)")
    
    # RENDER
    cmd = [
        "ffmpeg", "-y", *inputs,
        "-filter_complex", ";".join(filters),
        "-map", final_output, "-map", "[aout]",
        "-t", str(total_duration),
        "-c:v", "libx264", "-preset", "medium", "-crf", "23",
        "-pix_fmt", "yuv420p",
        "-c:a", "aac", "-b:a", "192k",
        output_path
    ]
    
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        logger.error(f"FFmpeg error: {result.stderr}")
        raise RuntimeError("FFmpeg failed")
    
    if title_card_path.exists():
        title_card_path.unlink()


def generate_three_exhibitions():
    """Generate reels for all three exhibitions."""
    
    logger.info("=" * 70)
    logger.info("GENERATING THREE EXHIBITION REELS")
    logger.info("=" * 70)
    logger.info("")
    
    # Exhibition configurations
    exhibitions = [
        {
            "name": "alenas_dream",
            "folder": "alenas_dream",
            "show_end_card": True,
            "title_card": {
                "title": "Alena's Dreams",
                "subtitle": "Fashion Art Installation",
                "date": "December 2025"
            },
            "narration_english": "Alena's Dreams is a total art installation that presents legendary Russian couturier Alena Akhmadullina not only as a fashion designer, but as an artist whose creative vision transcends the boundaries of fashion. Each elegant dress tells a story, blending haute couture with fine art in a dreamlike exhibition that captures the soul of Russian creativity.",
            "narration_russian": "Сны Алёны это тотальная художественная инсталляция которая представляет легендарного российского кутюрье Алёну Ахмадуллину не только как модельера но и как художника чьё творческое видение выходит за рамки моды. Каждое элегантное платье рассказывает историю сочетая высокую моду с изобразительным искусством в выставке похожей на сон которая передаёт душу русского творчества."
        },
        {
            "name": "winter_moscow",
            "folder": "winter_moscow",
            "show_end_card": True,  # YES end card
            "title_card": {
                "title": "Winter Moscow",
                "subtitle": "New Year's Celebration",
                "date": "December 2025"
            },
            "narration_english": "Moscow transforms into a winter wonderland for the New Year celebrations. Glittering decorations illuminate Red Square, festive lights dance across historic boulevards, and the city sparkles with holiday magic. From grand Christmas markets to elegant ice sculptures, Moscow celebrates the season with spectacular beauty that captures the warmth and joy of Russian winter traditions.",
            "narration_russian": "Москва превращается в зимнюю сказку к новогодним празднованиям. Сверкающие украшения освещают Красную площадь, праздничные огни танцуют на исторических бульварах, и город искрится праздничным волшебством. От грандиозных рождественских ярмарок до элегантных ледовых скульптур, Москва празднует сезон с впечатляющей красотой передающей тепло и радость русских зимних традиций."
        },
        {
            "name": "tzar_exhibition",
            "folder": "tzar_exhibition",
            "show_end_card": True,
            "title_card": {
                "title": "Treasures of the Imperial Residences",
                "subtitle": "Tzar's Village Exhibition",
                "date": "December 2025"
            },
            "narration_english": "At the Tzar's Village exhibition, the imperial treasures reveal centuries of Russian power and artistry. From ceremonial weapons wielded by legendary tzars to golden regalia that witnessed coronations, each artifact tells the story of the Romanov dynasty. Jeweled crowns, sacred icons, and palace masterpieces reflect the wealth, faith, and cultural sophistication that defined Imperial Russia.",
            "narration_russian": "На выставке Царского Села императорские сокровища раскрывают века русской власти и мастерства. От церемониального оружия которым владели легендарные цари до золотых регалий свидетелей коронаций, каждый артефакт рассказывает историю династии Романовых. Украшенные драгоценностями короны, священные иконы и дворцовые шедевры отражают богатство веру и культурную изысканность определявшую Императорскую Россию."
        }
    ]
    
    # Music
    music_dir = PROJECT_ROOT / "assets/music/cinematic"
    music_files = list(music_dir.glob("*.mp3"))
    if not music_files:
        logger.error("No music files found")
        return
    
    # Output dirs
    output_video_dir = PROJECT_ROOT / "output/videos/exhibitions"
    output_audio_dir = PROJECT_ROOT / "output/audio/exhibitions"
    output_subtitle_dir = PROJECT_ROOT / "output/subtitles/exhibitions"
    
    for d in [output_video_dir, output_audio_dir, output_subtitle_dir]:
        d.mkdir(parents=True, exist_ok=True)
    
    # Generate each exhibition
    for i, exhibition in enumerate(exhibitions, 1):
        logger.info(f"┌{'─' * 68}┐")
        logger.info(f"│ EXHIBITION {i}/3: {exhibition['name']:<53} │")
        logger.info(f"└{'─' * 68}┘")
        logger.info("")
        
        # Load images
        images_dir = PROJECT_ROOT / "assets" / exhibition["folder"]
        if not images_dir.exists():
            logger.error(f"  ❌ Folder not found: {images_dir}")
            continue
        
        image_files = sorted([
            f for f in images_dir.glob("*")
            if f.suffix.lower() in ['.jpg', '.jpeg', '.png', '.heic']
        ])
        
        if len(image_files) < 5:
            logger.error(f"  ❌ Not enough images: {len(image_files)}")
            continue
        
        logger.info(f"  📸 Found {len(image_files)} images")
        
        # Generate TTS
        audio_filename = f"{exhibition['name']}_{datetime.now().strftime('%Y%m%d')}.mp3"
        audio_path = output_audio_dir / audio_filename
        
        logger.info(f"  🎙️  Generating narration...")
        try:
            voice_data = generate_voice_google(
                text=exhibition['narration_english'],
                output_path=str(audio_path),
                voice_tone='neutral'
            )
        except Exception as e:
            logger.warning(f"  Google TTS failed, using Edge TTS")
            from scripts.generate_voice import generate_tts_audio
            generate_tts_audio(
                text=exhibition['narration_english'],
                output_path=audio_path,
                voice_tone='neutral'
            )
            voice_data = {
                "path": str(audio_path),
                "duration": get_audio_duration_ffprobe(str(audio_path))
            }
        
        logger.info(f"     Duration: {voice_data['duration']:.1f}s")
        
        # Generate subtitles
        logger.info(f"  📝 Generating subtitles...")
        srt_russian, srt_english = generate_dual_subtitles(
            russian_text=exhibition['narration_russian'],
            english_text=exhibition['narration_english'],
            audio_duration=voice_data['duration'],
            output_dir=str(output_subtitle_dir),
            video_id=exhibition['name']
        )
        
        # Select music
        music_path = random.choice(music_files)
        logger.info(f"  🎵 Music: {music_path.name}")
        
        # Render video
        video_filename = f"{exhibition['name']}_{datetime.now().strftime('%Y%m%d')}.mp4"
        video_path = output_video_dir / video_filename
        
        logger.info(f"  🎬 Rendering video...")
        render_exhibition_reel(
            image_paths=[str(img) for img in image_files],
            output_path=str(video_path),
            audio_path=str(audio_path),
            music_path=str(music_path),
            srt_russian=str(srt_russian),
            srt_english=str(srt_english),
            title_card_config=exhibition['title_card'],
            show_end_card=exhibition.get('show_end_card', True)
        )
        
        logger.info(f"  ✅ Complete: {video_path.name}")
        logger.info("")
    
    logger.info("=" * 70)
    logger.info("✨ ALL 3 EXHIBITION REELS GENERATED!")
    logger.info("=" * 70)
    logger.info(f"Videos: {output_video_dir}")
    logger.info("")


if __name__ == "__main__":
    try:
        generate_three_exhibitions()
    except Exception as e:
        logger.error(f"Failed: {e}", exc_info=True)
        sys.exit(1)
