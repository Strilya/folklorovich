#!/usr/bin/env python3
"""
Folklorovich - Custom Reel Generator
For special exhibitions, events, personal photos - completely separate from daily automation.

Usage: python3 scripts/generate_custom_reel.py
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

from scripts.render_video import create_slideshow_video
from scripts.generate_voice import generate_voice_google, get_audio_duration_ffprobe
from scripts.generate_subtitles import generate_dual_subtitles

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('CustomReelGenerator')


def delay_subtitles(input_srt: str, output_srt: str, delay_seconds: float):
    """Delay all subtitle timecodes by specified seconds."""
    from datetime import timedelta
    
    with open(input_srt, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    with open(output_srt, 'w', encoding='utf-8') as f:
        for line in lines:
            if '-->' in line:
                # Parse timecodes
                parts = line.split('-->')
                start = parts[0].strip()
                end = parts[1].strip()
                
                # Add delay
                start_ms = timecode_to_ms(start) + (delay_seconds * 1000)
                end_ms = timecode_to_ms(end) + (delay_seconds * 1000)
                
                # Write delayed
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


def render_tzar_reel(image_paths: list, output_path: str, audio_path: str, music_path: str,
                     srt_russian: str, srt_english: str, title: str, transition_type: str):
    """
    Render Tzar exhibition reel - SIMPLIFIED to actually work.
    """
    import subprocess
    from scripts.render_video import get_audio_duration
    
    audio_duration = get_audio_duration(audio_path)
    
    # Simple equal timing for ALL images
    num_images = len(image_paths)
    image_duration = 1.8  # Fixed duration per image for consistency
    
    logger.info(f"Video: 2s title + {num_images} images @ {image_duration}s each")
    
    inputs = []
    filters = []
    
    # TITLE CARD (2 seconds)
    title_card_path = PROJECT_ROOT / "output/temp_title_card.png"
    create_title_card(title_card_path)
    inputs.extend(["-loop", "1", "-t", "2.0", "-i", str(title_card_path)])
    
    # IMAGES with EQUAL duration (crucial for xfade)
    for i, img in enumerate(image_paths):
        inputs.extend(["-loop", "1", "-t", str(image_duration), "-i", str(img)])
    
    # AUDIO
    inputs.extend(["-i", audio_path, "-i", music_path])
    
    # SCALE everything to 1080x1920
    filters.append("[0:v]scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,setsar=1,fps=25[title]")
    
    for i in range(1, num_images + 1):
        filters.append(
            f"[{i}:v]scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,setsar=1,fps=25,"
            f"drawtext=fontfile=/System/Library/Fonts/Helvetica.ttc:text='@Folklorovich':"
            f"fontcolor=white@0.3:fontsize=24:x=w-tw-30:y=h-th-30[v{i}]"
        )
    
    # SIMPLE CONCAT (xfade is broken - all images equal time)
    all_inputs = "[title]" + "".join([f"[v{i}]" for i in range(1, num_images + 1)])
    filters.append(f"{all_inputs}concat=n={num_images + 1}:v=1:a=0[vbase]")
    
    # DELAYED SUBTITLES
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
    
    # END FADE
    filters.append(f"[vsub]fade=t=out:st={audio_duration + 1.5}:d=1.5[vfade]")
    
    # END CARD
    filters.append(
        f"[vfade]drawtext=fontfile=/System/Library/Fonts/HelveticaNeue.ttc:"
        f"text='@Folklorovich':fontcolor=white:fontsize=48:x=(w-text_w)/2:y=h/2-70:alpha='if(lt(t,{audio_duration + 1}),0,min((t-{audio_duration + 1})/0.3,1))',"
        f"drawtext=fontfile=/System/Library/Fonts/HelveticaNeue.ttc:"
        f"text='Discover Russian Mysteries':fontcolor=0xFFD700:fontsize=22:x=(w-text_w)/2:y=h/2+30:alpha='if(lt(t,{audio_duration + 1}),0,min((t-{audio_duration + 1})/0.3,1))'[vout]"
    )
    
    # AUDIO MIX
    narration_idx = num_images + 1
    music_idx = num_images + 2
    filters.append(
        f"[{narration_idx}:a]volume=1.0[voice];"
        f"[{music_idx}:a]volume=0.15,aloop=loop=-1:size=2e+09[music];"
        f"[voice][music]amix=inputs=2:duration=first[aout]"
    )
    
    # TOTAL DURATION
    total_duration = audio_duration + 3.5  # 2s title + audio + 1.5s end
    
    # BUILD COMMAND
    cmd = [
        "ffmpeg", "-y", *inputs,
        "-filter_complex", ";".join(filters),
        "-map", "[vout]", "-map", "[aout]",
        "-t", str(total_duration),
        "-c:v", "libx264", "-preset", "medium", "-crf", "23",
        "-pix_fmt", "yuv420p",
        "-c:a", "aac", "-b:a", "192k",
        output_path
    ]
    
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        logger.error(f"FFmpeg error: {result.stderr}")
        raise RuntimeError(f"FFmpeg failed")
    
    # Cleanup
    if title_card_path.exists():
        title_card_path.unlink()


def create_title_card(output_path: Path):
    """Create exhibition title card image - SIMPLE and CLEAN."""
    from PIL import Image, ImageDraw, ImageFont
    
    # Create 1080x1920 black image
    img = Image.new('RGB', (1080, 1920), color='black')
    draw = ImageDraw.Draw(img)
    
    # Load Didot Italic
    try:
        font_title = ImageFont.truetype("/System/Library/Fonts/Supplemental/Didot.ttc", 50)
        font_subtitle = ImageFont.truetype("/System/Library/Fonts/Supplemental/Didot.ttc", 36)
    except:
        font_title = ImageFont.load_default()
        font_subtitle = ImageFont.load_default()
    
    # Simple centered text - NO RUSSIAN
    title1 = "Treasures of the"
    title2 = "Imperial Residences"
    subtitle = "Tzar's Village Exhibition"
    date = "December 2025"
    
    # Draw (use textbbox for proper centering)
    bbox1 = draw.textbbox((0, 0), title1, font=font_title)
    w1 = bbox1[2] - bbox1[0]
    draw.text((540 - w1/2, 800), title1, fill='white', font=font_title)
    
    bbox2 = draw.textbbox((0, 0), title2, font=font_title)
    w2 = bbox2[2] - bbox2[0]
    draw.text((540 - w2/2, 870), title2, fill='white', font=font_title)
    
    bbox3 = draw.textbbox((0, 0), subtitle, font=font_subtitle)
    w3 = bbox3[2] - bbox3[0]
    draw.text((540 - w3/2, 980), subtitle, fill='gold', font=font_subtitle)
    
    bbox4 = draw.textbbox((0, 0), date, font=font_subtitle)
    w4 = bbox4[2] - bbox4[0]
    draw.text((540 - w4/2, 1050), date, fill='gray', font=font_subtitle)
    
    img.save(output_path)


def generate_tzar_exhibition_reels():
    """
    Generate 4 reels from Tzar Exhibition images.
    
    Specifications:
    - 62 images total → 4 reels (15-16 images each)
    - 1.2 seconds per image
    - Epic Russian orchestral music
    - English voiceover with Russian + English subtitles
    - Snell Roundhand font
    - @Folklorovich branding
    """
    
    logger.info("=" * 60)
    logger.info("TZAR EXHIBITION REEL GENERATOR")
    logger.info("=" * 60)
    logger.info("")
    
    # Load images
    images_dir = PROJECT_ROOT / "assets/tzar_exhibition"
    if not images_dir.exists():
        logger.error(f"Image directory not found: {images_dir}")
        return
    
    image_files = sorted([
        f for f in images_dir.glob("*")
        if f.suffix.lower() in ['.jpg', '.jpeg', '.png', '.heic']
    ])
    
    if len(image_files) < 60:
        logger.error(f"Expected 60+ images, found {len(image_files)}")
        return
    
    logger.info(f"Found {len(image_files)} images")
    
    # Shuffle for random distribution
    random.shuffle(image_files)
    
    # Divide into 4 reels
    images_per_reel = len(image_files) // 4
    reel_groups = [
        image_files[i*images_per_reel:(i+1)*images_per_reel]
        for i in range(4)
    ]
    
    # Add remaining images to last reel
    if len(image_files) % 4 != 0:
        reel_groups[3].extend(image_files[4*images_per_reel:])
    
    logger.info(f"Divided into 4 reels: {[len(g) for g in reel_groups]} images each")
    logger.info("")
    
    # Reel themes (SWAPPED: Weapons first, Jewels second)
    reel_configs = [
        {
            "title": "Royal Weapons & Armor",
            "transition": "concat",
            "narration_english": "This exhibition showcases ceremonial swords wielded by Peter the Great and battle armor worn in legendary military campaigns. From jewel-encrusted sabers to steel breastplates that deflected enemy blades, each artifact combines deadly function with imperial beauty. Master craftsmen spent years creating these masterpieces that reflected the military might of the Russian Empire.",
            "narration_russian": "Эта выставка демонстрирует церемониальные мечи которыми владел Пётр Великий и боевые доспехи носимые в легендарных военных кампаниях. От инкрустированных драгоценностями сабель до стальных нагрудников отражавших вражеские клинки, каждый артефакт сочетает смертоносную функцию с имперской красотой. Мастера годами создавали эти шедевры отражающие военную мощь Российской империи."
        },
        {
            "title": "Imperial Jewels & Regalia",
            "transition": "concat",
            "narration_english": "At the Tzar's Village exhibition, the imperial jewels reveal centuries of Russian power. Crowns worn by tzars during coronation ceremonies, diamonds that once adorned empresses, and golden regalia that witnessed the grandeur of the Romanov dynasty. Each piece tells a story of wealth, artistry, and the absolute authority of Russia's ruling families.",
            "narration_russian": "На выставке Царского Села императорские драгоценности раскрывают века русской власти. Короны надеваемые царями во время коронации, бриллианты украшавшие императриц, и золотые регалии свидетели величия династии Романовых. Каждый предмет рассказывает историю богатства мастерства и абсолютной власти правящих семей России."
        },
        {
            "title": "Palace Artifacts & Art",
            "transition": "crossfade",
            "narration_english": "Every object within the imperial palaces was crafted by Europe's finest artisans. Golden furniture commissioned from French masters, delicate porcelain from imperial factories, and ornate decorative pieces that filled vast ballrooms. These treasures reflect not just wealth, but the refined taste and cultural sophistication of Russia's aristocracy during its golden age.",
            "narration_russian": "Каждый предмет в императорских дворцах был создан лучшими европейскими мастерами. Золотая мебель заказанная у французских мастеров, изящный фарфор с императорских фабрик, и богато украшенные декоративные предметы заполнявшие огромные бальные залы. Эти сокровища отражают не только богатство но и утончённый вкус культурную изысканность русской аристократии золотого века."
        },
        {
            "title": "Religious Icons & Sacred Objects",
            "transition": "crossfade",
            "narration_english": "The tzars' deep Orthodox faith is embodied in these sacred treasures. Icons blessed by patriarchs and venerated for centuries, jeweled crosses carried into battle, and holy relics that protected the imperial family through war and revolution. Each object represents the spiritual foundation that sustained the dynasty until its tragic end in nineteen eighteen.",
            "narration_russian": "Глубокая православная вера царей воплощена в этих священных сокровищах. Иконы благословлённые патриархами почитаемые веками, украшенные драгоценностями кресты носимые в битвы, и святые реликвии защищавшие императорскую семью через войны и революцию. Каждый предмет представляет духовную основу поддерживавшую династию до её трагического конца в тысяча девятьсот восемнадцатом."
        }
    ]
    
    # Music
    music_dir = PROJECT_ROOT / "assets/music/cinematic"
    music_files = list(music_dir.glob("*.mp3"))
    if not music_files:
        logger.error("No music files found in assets/music/cinematic/")
        return
    
    # Output directories
    output_video_dir = PROJECT_ROOT / "output/videos/custom"
    output_audio_dir = PROJECT_ROOT / "output/audio/custom"
    output_subtitle_dir = PROJECT_ROOT / "output/subtitles/custom"
    
    for d in [output_video_dir, output_audio_dir, output_subtitle_dir]:
        d.mkdir(parents=True, exist_ok=True)
    
    # Generate each reel
    generated_reels = []
    
    for i, (images, config) in enumerate(zip(reel_groups, reel_configs), 1):
        logger.info(f"┌─────────────────────────────────────────┐")
        logger.info(f"│  GENERATING REEL {i}/4: {config['title'][:20]:<20}│")
        logger.info(f"└─────────────────────────────────────────┘")
        logger.info("")
        
        # Generate TTS audio
        audio_filename = f"tzar_reel{i}_{datetime.now().strftime('%Y%m%d')}.mp3"
        audio_path = output_audio_dir / audio_filename
        
        logger.info("🎙️  Generating English narration...")
        try:
            voice_data = generate_voice_google(
                text=config['narration_english'],
                output_path=str(audio_path),
                voice_tone='neutral'
            )
        except Exception as e:
            logger.warning(f"Google TTS failed: {e}, using Edge TTS fallback")
            from scripts.generate_voice import generate_tts_audio
            generate_tts_audio(
                text=config['narration_english'],
                output_path=audio_path,
                voice_tone='neutral'
            )
            voice_data = {
                "path": str(audio_path),
                "duration": get_audio_duration_ffprobe(str(audio_path)),
                "voice": "Edge TTS"
            }
        
        logger.info(f"   Duration: {voice_data['duration']:.1f}s")
        logger.info("")
        
        # Generate dual subtitles
        logger.info("📝 Generating dual subtitles...")
        srt_russian, srt_english = generate_dual_subtitles(
            russian_text=config['narration_russian'],
            english_text=config['narration_english'],
            audio_duration=voice_data['duration'],
            output_dir=str(output_subtitle_dir),
            video_id=f"tzar_reel{i}"
        )
        logger.info("")
        
        # Select music
        music_path = random.choice(music_files)
        logger.info(f"🎵 Music: {music_path.name}")
        logger.info("")
        
        # Generate video with custom rendering
        logger.info(f"🎬 Rendering video ({config['transition']}) with {len(images)} images...")
        video_filename = f"tzar_reel{i}_{config['transition']}_{datetime.now().strftime('%Y%m%d')}.mp4"
        video_path = output_video_dir / video_filename
        
        render_tzar_reel(
            image_paths=[str(img) for img in images],
            output_path=str(video_path),
            audio_path=str(audio_path),
            music_path=str(music_path),
            srt_russian=str(srt_russian),
            srt_english=str(srt_english),
            title=config['title'],
            transition_type=config['transition']
        )
        
        generated_reels.append({
            "reel_number": i,
            "title": config['title'],
            "video_path": str(video_path),
            "image_count": len(images),
            "duration": voice_data['duration']
        })
        
        logger.info(f"✅ Reel {i} complete: {video_path}")
        logger.info("")
    
    # Summary
    logger.info("=" * 60)
    logger.info("✨ ALL 4 TZAR EXHIBITION REELS GENERATED!")
    logger.info("=" * 60)
    for reel in generated_reels:
        logger.info(f"Reel {reel['reel_number']}: {reel['title']}")
        logger.info(f"  📹 {reel['video_path']}")
        logger.info(f"  🖼️  {reel['image_count']} images, {reel['duration']:.1f}s")
        logger.info("")
    
    logger.info(f"Videos saved to: {output_video_dir}")
    logger.info("")


if __name__ == "__main__":
    try:
        generate_tzar_exhibition_reels()
    except Exception as e:
        logger.error(f"Failed to generate reels: {e}", exc_info=True)
        sys.exit(1)
