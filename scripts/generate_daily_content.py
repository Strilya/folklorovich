#!/usr/bin/env python3
"""
Folklorovich - Daily Content Generator (Phase 8: Dual Reel Types)
Master orchestrator script with strict alternation between visual and superstition reels.

Usage:
    python scripts/generate_daily_content.py

This script generates TWO distinct reel types:
- TYPE A: Visual-Only Reels (15s, no narration, loud music, Russian beauty)
- TYPE B: Superstition Reels (25-32s, Russian narration, dual subtitles, quiet music)

Pattern: A → B → A → B (strict alternation)

Author: Folklorovich Project
Date: 2025-12-06
"""

import os
import sys
import json
import logging
import random
from datetime import datetime
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

# Environment variables
from dotenv import load_dotenv
load_dotenv(PROJECT_ROOT / '.env')

# Import pipeline modules
from scripts.fetch_images import fetch_images_russian
from scripts.generate_voice import generate_voice_google
from scripts.generate_subtitles import generate_dual_subtitles
from scripts.render_video import create_slideshow_video
from scripts.music_manager import get_random_music

# Configure logging
logging.basicConfig(
    level=os.getenv('LOG_LEVEL', 'INFO'),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(PROJECT_ROOT / 'generation.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('DailyGenerator')


def main():
    """Generate daily Folklorovich reel with strict alternation"""

    logger.info("=" * 60)
    logger.info("FOLKLOROVICH DAILY CONTENT GENERATOR - PHASE 8")
    logger.info("=" * 60)

    # Load metadata
    metadata_path = Path(PROJECT_ROOT / "content/metadata.json")
    metadata = json.loads(metadata_path.read_text())

    # Determine next reel type (STRICT ALTERNATION)
    last_type = metadata.get("reel_alternation", {}).get("last_reel_type")

    if last_type == "visual":
        next_type = "superstition"
    elif last_type == "superstition":
        next_type = "visual"
    else:
        # First run - start with visual
        next_type = "visual"

    logger.info(f"Last reel type: {last_type or 'None (first run)'}")
    logger.info(f"Next reel type: {next_type.upper()}")
    logger.info("")

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
            metadata["reel_alternation"]["visual_reel_count"] = \
                metadata["reel_alternation"].get("visual_reel_count", 0) + 1
        else:
            metadata["reel_alternation"]["superstition_reel_count"] = \
                metadata["reel_alternation"].get("superstition_reel_count", 0) + 1

        # Update generation history
        if "generation_history" not in metadata:
            metadata["generation_history"] = {}

        metadata["generation_history"]["last_success_date"] = datetime.now().isoformat()
        metadata["last_update"] = datetime.now().isoformat()

        # Add to generation log
        if "generation_log" not in metadata["generation_history"]:
            metadata["generation_history"]["generation_log"] = []

        metadata["generation_history"]["generation_log"].append({
            "date": datetime.now().isoformat(),
            "type": next_type,
            "video_path": str(video_path),
            "status": "success"
        })

        # Keep only last 20 entries in log
        metadata["generation_history"]["generation_log"] = \
            metadata["generation_history"]["generation_log"][-20:]

        metadata_path.write_text(json.dumps(metadata, indent=2, ensure_ascii=False))

        logger.info("")
        logger.info("=" * 60)
        logger.info(f"✅ {next_type.upper()} REEL GENERATED SUCCESSFULLY!")
        logger.info(f"📹 Video: {video_path}")
        logger.info(f"📊 Stats: {metadata['reel_alternation']['visual_reel_count']} visual, "
                   f"{metadata['reel_alternation']['superstition_reel_count']} superstition")
        logger.info("=" * 60)

    except Exception as e:
        logger.error(f"❌ Generation failed: {e}", exc_info=True)

        # Update failure metadata
        if "generation_history" not in metadata:
            metadata["generation_history"] = {}

        metadata["generation_history"]["last_failure_date"] = datetime.now().isoformat()
        metadata["generation_history"]["last_error_message"] = str(e)
        metadata_path.write_text(json.dumps(metadata, indent=2, ensure_ascii=False))

        sys.exit(1)


def generate_visual_reel(metadata: dict) -> Path:
    """
    TYPE A: Visual-Only Reel (15s, no narration)

    Features:
    - 15 seconds total
    - 10 images with fast crossfades
    - Loud atmospheric music
    - Only watermark overlay
    - Russian cultural/nature beauty
    """

    logger.info("┌─────────────────────────────────────────┐")
    logger.info("│   GENERATING VISUAL REEL (TYPE A)      │")
    logger.info("└─────────────────────────────────────────┘")
    logger.info("")

    # Load visual themes
    themes_path = Path(PROJECT_ROOT / "content/visual_themes.json")
    themes_data = json.loads(themes_path.read_text())
    themes = themes_data["themes"]

    # Get used theme IDs
    used_theme_ids = metadata.get("reel_alternation", {}).get("used_visual_theme_ids", [])

    # Select unused theme (or reset if all used)
    available_themes = [t for t in themes if t["id"] not in used_theme_ids]
    if not available_themes:
        logger.info("All themes used, resetting cycle")
        available_themes = themes
        used_theme_ids = []

    theme = random.choice(available_themes)
    logger.info(f"🎨 Theme: {theme['name']} ({theme['id']})")
    logger.info(f"   Mood: {theme['mood']}")
    logger.info("")

    # Fetch 10 images (2 per keyword)
    logger.info("📥 Fetching images from Pixabay...")
    images = []
    for i, keyword_set in enumerate(theme["keywords"]):
        logger.info(f"   Keyword {i+1}/5: {keyword_set}")
        try:
            img_paths = fetch_images_russian(keyword_set, num_images=2)
            images.extend(img_paths)
        except Exception as e:
            logger.warning(f"   Failed to fetch images for '{keyword_set}': {e}")

    if len(images) < 10:
        logger.warning(f"Only got {len(images)} images, will repeat some")

    images = images[:10] if len(images) >= 10 else images
    logger.info(f"   Total images: {len(images)}")
    logger.info("")

    # Fetch cinematic music (random selection)
    logger.info("🎵 Selecting cinematic music...")
    music_path = get_random_music("visual")
    logger.info(f"   Music: {Path(music_path).name}")
    logger.info("")

    # Render video
    output_dir = Path(PROJECT_ROOT / "output/videos")
    output_dir.mkdir(parents=True, exist_ok=True)

    video_filename = f"{datetime.now().date()}_{theme['id']}_visual.mp4"
    output_path = output_dir / video_filename

    logger.info("🎬 Rendering slideshow video...")
    logger.info(f"   Output: {output_path}")
    logger.info("")

    create_slideshow_video(
        image_paths=images,
        output_path=str(output_path),
        reel_type="visual",
        music_path=music_path
    )

    # Mark theme as used
    used_theme_ids.append(theme["id"])
    metadata["reel_alternation"]["used_visual_theme_ids"] = used_theme_ids

    logger.info("✅ Visual reel complete!")
    logger.info("")

    return output_path


def generate_superstition_reel(metadata: dict) -> Path:
    """
    TYPE B: Superstition Reel (25-32s, narration + dual subs)

    Features:
    - 25-32 seconds (matches audio)
    - 10-13 images with smooth crossfades
    - Russian narration (Google Cloud TTS)
    - Dual subtitles (Russian + English)
    - Quiet background music (15% volume)
    - Watermark overlay
    """

    logger.info("┌─────────────────────────────────────────┐")
    logger.info("│  GENERATING SUPERSTITION REEL (TYPE B) │")
    logger.info("└─────────────────────────────────────────┘")
    logger.info("")

    # Load folklore database
    folklore_path = Path(PROJECT_ROOT / "content/folklore_database.json")
    folklore_db = json.loads(folklore_path.read_text())

    # Get used superstition IDs
    used_ids = metadata.get("reel_alternation", {}).get("used_superstition_ids", [])

    # Select unused superstition
    available = [f for f in folklore_db["folklore"] if f["id"] not in used_ids]

    if not available:
        logger.info("All superstitions used, resetting cycle")
        available = folklore_db["folklore"]
        used_ids = []

    folklore = random.choice(available)
    logger.info(f"📖 Superstition: {folklore['name']} (ID: {folklore['id']})")
    logger.info(f"   Voice tone: {folklore['voice_tone']}")
    logger.info("")

    # Generate Russian TTS
    logger.info("🎙️  Generating Russian narration (Google Cloud TTS)...")
    audio_dir = Path(PROJECT_ROOT / "output/audio")
    audio_dir.mkdir(parents=True, exist_ok=True)

    audio_filename = f"{datetime.now().date()}_{folklore['id']}.mp3"
    audio_path = audio_dir / audio_filename

    russian_text = folklore.get("story_russian", folklore["story_full"])

    try:
        voice_data = generate_voice_google(
            text=russian_text,
            output_path=str(audio_path),
            voice_tone=folklore["voice_tone"]
        )
        logger.info(f"   Duration: {voice_data['duration']:.1f}s")
        logger.info(f"   Voice: {voice_data['voice']}")
    except Exception as e:
        logger.error(f"Google Cloud TTS failed, falling back to Edge TTS: {e}")
        # Fallback to Edge TTS if Google fails
        from scripts.generate_voice import generate_tts_audio
        generate_tts_audio(
            text=russian_text,
            output_path=audio_path,
            voice_tone=folklore["voice_tone"]
        )
        from scripts.generate_voice import get_audio_duration_ffprobe
        voice_data = {
            "path": str(audio_path),
            "duration": get_audio_duration_ffprobe(str(audio_path)),
            "voice": "Edge TTS fallback"
        }

    logger.info("")

    # Fetch images (Russian cultural)
    logger.info("📥 Fetching images from Pixabay...")
    images = []
    num_needed = int(voice_data["duration"] / 2.5) + 1

    for i, keyword in enumerate(folklore["visual_tags"][:6]):  # Use first 6 keywords
        logger.info(f"   Keyword {i+1}: {keyword}")
        try:
            img_paths = fetch_images_russian(keyword, num_images=2)
            images.extend(img_paths)
        except Exception as e:
            logger.warning(f"   Failed: {e}")

    images = images[:num_needed] if len(images) >= num_needed else images
    logger.info(f"   Total images: {len(images)} (need {num_needed})")
    logger.info("")

    # Generate dual subtitles
    logger.info("📝 Generating dual subtitles...")
    subtitle_dir = Path(PROJECT_ROOT / "output/subtitles")
    subtitle_dir.mkdir(parents=True, exist_ok=True)

    srt_russian, srt_english = generate_dual_subtitles(
        russian_text=russian_text,
        english_text=folklore["story_full"],
        audio_duration=voice_data["duration"],
        output_dir=str(subtitle_dir),
        video_id=folklore["id"]
    )
    logger.info(f"   Russian: {srt_russian}")
    logger.info(f"   English: {srt_english}")
    logger.info("")

    # Fetch Russian folk music (random selection, quiet background)
    logger.info("🎵 Selecting Russian folk music...")
    music_path = get_random_music("superstition")
    logger.info(f"   Music: {Path(music_path).name}")
    logger.info("")

    # Render video
    output_dir = Path(PROJECT_ROOT / "output/videos")
    output_dir.mkdir(parents=True, exist_ok=True)

    video_filename = f"{datetime.now().date()}_{folklore['id']}_superstition.mp4"
    output_path = output_dir / video_filename

    logger.info("🎬 Rendering slideshow video with dual subtitles...")
    logger.info(f"   Output: {output_path}")
    logger.info("")

    create_slideshow_video(
        image_paths=images,
        output_path=str(output_path),
        reel_type="superstition",
        audio_path=str(audio_path),
        music_path=music_path,
        title=folklore["name"],
        subtitles_russian=srt_russian,
        subtitles_english=srt_english
    )

    # Mark as used
    used_ids.append(folklore["id"])
    metadata["reel_alternation"]["used_superstition_ids"] = used_ids

    logger.info("✅ Superstition reel complete!")
    logger.info("")

    return output_path


if __name__ == "__main__":
    main()
