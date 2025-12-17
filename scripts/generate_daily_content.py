#!/usr/bin/env python3
import sys
import json
import random
import logging
from pathlib import Path
from datetime import datetime

PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from scripts.fetch_videos import fetch_russian_videos
from scripts.generate_voice import generate_voice_google
from scripts.generate_subtitles import generate_dual_subtitles
from scripts.render_video import create_slideshow_video

logging.basicConfig(level=logging.INFO, format='%(levelname)s - %(message)s')
logger = logging.getLogger('Main')


def generate_etiquette():
    logger.info("="*50)
    logger.info("GENERATING ETIQUETTE VIDEO")
    logger.info("="*50)
    
    # Load data
    etiq_file = PROJECT_ROOT / "content/cultural_etiquette.json"
    with open(etiq_file) as f:
        rules = json.load(f)['etiquette']
    
    rule = random.choice(rules)
    logger.info(f"Topic: {rule['name']}")
    
    # Fetch videos
    keywords = " ".join(rule['visual_tags'])
    logger.info(f"Keywords: {keywords}")
    videos = fetch_russian_videos(keywords, num_videos=8)
    
    if len(videos) < 5:
        logger.error("Not enough videos!")
        return None
    
    logger.info(f"Videos: {len(videos)}")
    
    # Generate audio
    audio_dir = PROJECT_ROOT / "output/audio"
    audio_dir.mkdir(parents=True, exist_ok=True)
    audio_path = audio_dir / f"{rule['id']}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.mp3"
    
    voice_data = generate_voice_google(rule['story_english'], str(audio_path), rule['voice_tone'])
    
    # Generate subtitles
    sub_dir = PROJECT_ROOT / "output/subtitles"
    ru_srt, en_srt = generate_dual_subtitles(
        rule['story_russian'],
        rule['story_english'],
        voice_data['duration'],
        str(sub_dir),
        rule['id']
    )
    
    # Music
    music_dir = PROJECT_ROOT / "assets/music/cinematic"
    music_path = str(random.choice(list(music_dir.glob("*.mp3"))))
    
    # Render
    out_dir = PROJECT_ROOT / "output/videos"
    out_dir.mkdir(parents=True, exist_ok=True)
    output = out_dir / f"{rule['id']}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.mp4"
    
    create_slideshow_video(
        image_paths=[str(v) for v in videos],
        output_path=str(output),
        reel_type="etiquette",
        audio_path=str(audio_path),
        music_path=music_path,
        subtitles_russian=str(ru_srt),
        subtitles_english=str(en_srt)
    )
    
    logger.info("="*50)
    logger.info(f"DONE: {output.name}")
    logger.info("="*50)
    return str(output)


if __name__ == "__main__":
    try:
        generate_etiquette()
    except Exception as e:
        logger.error(f"FAILED: {e}", exc_info=True)
        sys.exit(1)
