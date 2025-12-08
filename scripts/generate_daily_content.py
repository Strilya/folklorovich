#!/usr/bin/env python3
"""
Folklorovich - Daily Content Generator (FIXED)
ENGLISH narration, proper durations, multi-source images
"""

import os
import sys
import json
import logging
import random
from datetime import datetime
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from dotenv import load_dotenv
load_dotenv(PROJECT_ROOT / '.env')

from scripts.fetch_images import fetch_images_russian
from scripts.generate_voice import generate_voice_google
from scripts.generate_subtitles import generate_dual_subtitles
from scripts.render_video import create_slideshow_video
from scripts.music_manager import get_random_music

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('DailyGenerator')


def main():
    logger.info("="*60)
    logger.info("FOLKLOROVICH DAILY GENERATOR - FIXED VERSION")
    logger.info("="*60)
    
    metadata_path = PROJECT_ROOT / "content/metadata.json"
    metadata = json.loads(metadata_path.read_text())
    
    # Determine reel type
    last_type = metadata.get("reel_alternation", {}).get("last_reel_type")
    next_type = "superstition" if last_type == "visual" else "visual"
    
    logger.info(f"Next reel: {next_type.upper()}")
    
    try:
        if next_type == "visual":
            video_path = generate_visual_reel(metadata)
        else:
            video_path = generate_superstition_reel(metadata)
        
        # Update metadata
        if "reel_alternation" not in metadata:
            metadata["reel_alternation"] = {
                "last_reel_type": None,
                "visual_reel_count": 0,
                "superstition_reel_count": 0,
                "used_superstition_ids": [],
                "used_visual_theme_ids": []
            }
        
        metadata["reel_alternation"]["last_reel_type"] = next_type
        
        if next_type == "visual":
            metadata["reel_alternation"]["visual_reel_count"] = metadata["reel_alternation"].get("visual_reel_count", 0) + 1
        else:
            metadata["reel_alternation"]["superstition_reel_count"] = metadata["reel_alternation"].get("superstition_reel_count", 0) + 1
        
        metadata_path.write_text(json.dumps(metadata, indent=2))
        
        logger.info(f"✅ {next_type.upper()} REEL COMPLETE: {video_path}")
        
    except Exception as e:
        logger.error(f"❌ FAILED: {e}", exc_info=True)
        sys.exit(1)


def generate_visual_reel(metadata: dict) -> Path:
    """TYPE A: 15s visual reel"""
    
    logger.info("GENERATING VISUAL REEL")
    
    themes_path = PROJECT_ROOT / "content/visual_themes.json"
    themes_data = json.loads(themes_path.read_text())
    themes = themes_data["themes"]
    
    used_theme_ids = metadata.get("reel_alternation", {}).get("used_visual_theme_ids", [])
    available_themes = [t for t in themes if t["id"] not in used_theme_ids]
    
    if not available_themes:
        available_themes = themes
        used_theme_ids = []
    
    theme = random.choice(available_themes)
    logger.info(f"Theme: {theme['name']}")
    
    # Fetch images
    images = []
    for keyword_set in theme["keywords"]:
        try:
            img_paths = fetch_images_russian(keyword_set, num_images=2)
            images.extend(img_paths)
        except Exception as e:
            logger.warning(f"Image fetch failed: {e}")
    
    logger.info(f"Got {len(images)} images")
    
    # Music
    music_path = get_random_music("visual")
    
    # Render
    output_dir = PROJECT_ROOT / "output/videos"
    output_dir.mkdir(parents=True, exist_ok=True)
    
    video_filename = f"{datetime.now().date()}_{theme['id']}_visual.mp4"
    output_path = output_dir / video_filename
    
    create_slideshow_video(
        image_paths=images,
        output_path=str(output_path),
        reel_type="visual",
        music_path=music_path
    )
    
    used_theme_ids.append(theme["id"])
    metadata["reel_alternation"]["used_visual_theme_ids"] = used_theme_ids
    
    return output_path


def generate_superstition_reel(metadata: dict) -> Path:
    """TYPE B: Superstition with RUSSIAN narration + DUAL subtitles"""
    
    logger.info("GENERATING SUPERSTITION REEL")
    
    folklore_path = PROJECT_ROOT / "content/folklore_database.json"
    folklore_db = json.loads(folklore_path.read_text())
    
    used_ids = metadata.get("reel_alternation", {}).get("used_superstition_ids", [])
    available = [f for f in folklore_db["folklore"] if f["id"] not in used_ids]
    
    if not available:
        available = folklore_db["folklore"]
        used_ids = []
    
    folklore = random.choice(available)
    logger.info(f"Superstition: {folklore['name']}")
    
    # Generate ENGLISH TTS (not Russian)
    audio_dir = PROJECT_ROOT / "output/audio"
    audio_dir.mkdir(parents=True, exist_ok=True)
    
    audio_filename = f"{datetime.now().date()}_{folklore['id']}.mp3"
    audio_path = audio_dir / audio_filename
    
    # Use ENGLISH text for narration
    english_text = folklore.get("story_full", folklore.get("story_english", ""))
    russian_text = folklore.get("story_russian", "")
    
    # Use ENGLISH TTS
    voice_data = generate_voice_google(
        text=english_text,
        output_path=str(audio_path),
        voice_tone=folklore["voice_tone"]
    )
    
    logger.info(f"Audio duration: {voice_data['duration']:.1f}s")
    
    # Fetch images
    images = []
    num_needed = int(voice_data["duration"] / 2.5) + 1
    
    for keyword in folklore["visual_tags"][:6]:
        try:
            img_paths = fetch_images_russian(keyword, num_images=2)
            images.extend(img_paths)
        except Exception as e:
            logger.warning(f"Image fetch failed: {e}")
    
    logger.info(f"Got {len(images)} images (need {num_needed})")
    
    # Generate DUAL subtitles (Russian + English)
    subtitle_dir = PROJECT_ROOT / "output/subtitles"
    subtitle_dir.mkdir(parents=True, exist_ok=True)
    
    srt_russian, srt_english = generate_dual_subtitles(
        russian_text=russian_text if russian_text else "Русский текст",
        english_text=english_text,
        audio_duration=voice_data["duration"],
        output_dir=str(subtitle_dir),
        video_id=folklore["id"]
    )
    
    logger.info(f"Subtitles: RU={srt_russian}, EN={srt_english}")
    
    # Music
    music_path = get_random_music("superstition")
    
    # Render
    output_dir = PROJECT_ROOT / "output/videos"
    video_filename = f"{datetime.now().date()}_{folklore['id']}_superstition.mp4"
    output_path = output_dir / video_filename
    
    create_slideshow_video(
        image_paths=images,
        output_path=str(output_path),
        reel_type="superstition",
        audio_path=str(audio_path),
        music_path=music_path,
        subtitles_russian=srt_russian,
        subtitles_english=srt_english
    )
    
    used_ids.append(folklore["id"])
    metadata["reel_alternation"]["used_superstition_ids"] = used_ids
    
    return output_path


if __name__ == "__main__":
    main()
