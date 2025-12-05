#!/usr/bin/env python3
"""
Folklorovich - Daily Content Generator
Main orchestrator script that runs the entire content generation pipeline.

Usage:
    python scripts/generate_daily_content.py

This script:
1. Loads environment variables and configuration
2. Selects the next folklore entry from the database
3. Fetches images from Unsplash
4. Creates a 4K image collage
5. Generates Russian TTS narration
6. Renders final video with FFmpeg
7. Updates metadata tracking

Author: Folklorovich Project
Date: 2025-12-05
"""

import os
import sys
import json
import logging
import random
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Tuple

# Add project root to path for imports
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

# Environment variables
from dotenv import load_dotenv
load_dotenv(PROJECT_ROOT / '.env')

# Import other pipeline scripts
from scripts.fetch_images import fetch_images_for_folklore
from scripts.create_collage import create_collage
from scripts.generate_voice import generate_tts_audio
from scripts.render_video import render_video

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


class ContentGenerator:
    """Main content generation orchestrator."""

    def __init__(self):
        """Initialize the content generator."""
        self.project_root = PROJECT_ROOT
        self.content_dir = self.project_root / 'content'
        self.output_dir = self.project_root / 'output'

        # Load configuration
        self.folklore_db = self._load_json(self.content_dir / 'folklore_database.json')
        self.metadata = self._load_json(self.content_dir / 'metadata.json')

        # Ensure output directories exist
        (self.output_dir / 'images').mkdir(parents=True, exist_ok=True)
        (self.output_dir / 'audio').mkdir(parents=True, exist_ok=True)
        (self.output_dir / 'videos').mkdir(parents=True, exist_ok=True)

        logger.info("Content generator initialized")

    def _load_json(self, filepath: Path) -> Dict:
        """Load JSON file with error handling."""
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            logger.error(f"File not found: {filepath}")
            raise
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON in {filepath}: {e}")
            raise

    def _save_json(self, filepath: Path, data: Dict):
        """Save JSON file with pretty formatting."""
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        logger.info(f"Saved JSON to {filepath}")

    def select_next_folklore(self) -> Optional[Dict]:
        """
        Select the next folklore entry using intelligent rotation.

        Algorithm:
        1. Check if all entries have been used in current cycle
        2. If yes, start new cycle with shuffled order
        3. Select next unused entry
        4. Mark as used in metadata

        Returns:
            Folklore entry dict or None if database is empty
        """
        folklore_list = self.folklore_db.get('folklore', [])
        if not folklore_list:
            logger.error("Folklore database is empty!")
            return None

        # Get current cycle state
        used_ids = set(self.metadata['content_rotation']['used_ids_this_cycle'])
        all_ids = {entry['id'] for entry in folklore_list}

        # Check if cycle is complete
        if used_ids >= all_ids:
            logger.info("Cycle complete! Starting new cycle with shuffled order")
            self._start_new_cycle(all_ids)
            used_ids = set()

        # Get cycle order (or create if doesn't exist)
        cycle_order = self.metadata['content_rotation'].get('cycle_order', [])
        if not cycle_order:
            cycle_order = list(all_ids)
            random.shuffle(cycle_order)
            self.metadata['content_rotation']['cycle_order'] = cycle_order

        # Find next unused entry
        for folklore_id in cycle_order:
            if folklore_id not in used_ids:
                # Find the full entry
                entry = next((e for e in folklore_list if e['id'] == folklore_id), None)
                if entry:
                    logger.info(f"Selected folklore: {entry['name']} (ID: {folklore_id})")
                    return entry

        logger.error("Could not select next folklore entry")
        return None

    def _start_new_cycle(self, all_ids: set):
        """Start a new content rotation cycle."""
        # Increment cycle number
        self.metadata['content_rotation']['current_cycle'] += 1

        # Create new shuffled order
        new_order = list(all_ids)
        random.shuffle(new_order)

        # Reset tracking
        self.metadata['content_rotation']['cycle_order'] = new_order
        self.metadata['content_rotation']['used_ids_this_cycle'] = []

        logger.info(f"Started cycle #{self.metadata['content_rotation']['current_cycle']}")

    def mark_folklore_used(self, folklore_id: str):
        """Mark a folklore entry as used in the current cycle."""
        used_ids = self.metadata['content_rotation']['used_ids_this_cycle']
        if folklore_id not in used_ids:
            used_ids.append(folklore_id)

        self.metadata['content_rotation']['last_used_id'] = folklore_id
        self.metadata['content_rotation']['last_generated_date'] = datetime.now().isoformat()

        logger.info(f"Marked folklore {folklore_id} as used")

    def generate_content(self, folklore_entry: Dict) -> Optional[Path]:
        """
        Generate complete video content for a folklore entry.

        Pipeline:
        1. Fetch images from Unsplash
        2. Create collage
        3. Generate TTS audio
        4. Render video with FFmpeg

        Args:
            folklore_entry: Folklore database entry

        Returns:
            Path to generated video or None if failed
        """
        start_time = datetime.now()
        folklore_id = folklore_entry['id']
        folklore_name = folklore_entry['name']

        try:
            # Create dated output directory
            date_str = datetime.now().strftime('%Y-%m-%d')
            output_subdir = self.output_dir / 'images' / f"{date_str}_{folklore_id}"
            output_subdir.mkdir(parents=True, exist_ok=True)

            logger.info(f"Starting generation for {folklore_name} (ID: {folklore_id})")

            # Step 1: Fetch images
            logger.info("Step 1/4: Fetching images from Unsplash...")
            image_paths = fetch_images_for_folklore(
                visual_tags=folklore_entry['visual_tags'],
                output_dir=output_subdir,
                count=6  # Fetch 6 images for variety
            )

            if not image_paths:
                logger.error("Failed to fetch images")
                return None

            logger.info(f"Fetched {len(image_paths)} images")

            # Step 2: Create collage
            logger.info("Step 2/4: Creating image collage...")
            collage_path = self.output_dir / 'images' / f"{date_str}_{folklore_id}_collage.png"

            success = create_collage(
                image_paths=image_paths,
                output_path=collage_path,
                title=folklore_entry['name_russian'],
                subtitle=folklore_entry.get('moral', ''),
                layout_name=None  # Will select random layout
            )

            if not success:
                logger.error("Failed to create collage")
                return None

            logger.info(f"Created collage: {collage_path}")

            # Step 3: Generate TTS audio
            logger.info("Step 3/4: Generating TTS audio...")
            audio_path = self.output_dir / 'audio' / f"{date_str}_{folklore_id}.mp3"

            audio_success = generate_tts_audio(
                text=folklore_entry['story_full'],
                output_path=audio_path,
                voice_tone=folklore_entry['voice_tone'],
                target_duration=folklore_entry.get('duration_target', 30)
            )

            if not audio_success:
                logger.error("Failed to generate audio")
                return None

            logger.info(f"Generated audio: {audio_path}")

            # Step 4: Render video
            logger.info("Step 4/4: Rendering final video...")
            video_filename = f"{date_str}_{folklore_name.replace(' ', '_')}.mp4"
            video_path = self.output_dir / 'videos' / video_filename

            render_success = render_video(
                image_path=collage_path,
                audio_path=audio_path,
                output_path=video_path
            )

            if not render_success:
                logger.error("Failed to render video")
                return None

            # Success! Update statistics
            generation_time = (datetime.now() - start_time).total_seconds()
            self._update_statistics(folklore_entry, generation_time, success=True)

            logger.info(f"✓ Video generated successfully: {video_path}")
            logger.info(f"Total generation time: {generation_time:.2f} seconds")

            return video_path

        except Exception as e:
            logger.error(f"Generation failed with exception: {e}", exc_info=True)
            self._update_statistics(folklore_entry, 0, success=False, error=str(e))
            return None

    def _update_statistics(self, folklore_entry: Dict, generation_time: float,
                          success: bool, error: Optional[str] = None):
        """Update metadata statistics after generation attempt."""
        stats = self.metadata['generation_history']

        stats['total_videos_generated'] += 1

        if success:
            stats['successful_generations'] += 1
            stats['last_success_date'] = datetime.now().isoformat()

            # Update category statistics
            category = folklore_entry.get('category', 'unknown')
            cat_stats = self.metadata['statistics']['by_category']
            cat_stats[category] = cat_stats.get(category, 0) + 1

            # Update voice tone statistics
            voice = folklore_entry.get('voice_tone', 'unknown')
            voice_stats = self.metadata['statistics']['by_voice_tone']
            voice_stats[voice] = voice_stats.get(voice, 0) + 1

            # Update average generation time
            avg_time = self.metadata['statistics'].get('average_generation_time_seconds')
            if avg_time is None:
                self.metadata['statistics']['average_generation_time_seconds'] = generation_time
            else:
                # Running average
                total = stats['successful_generations']
                self.metadata['statistics']['average_generation_time_seconds'] = \
                    ((avg_time * (total - 1)) + generation_time) / total
        else:
            stats['failed_generations'] += 1
            stats['last_failure_date'] = datetime.now().isoformat()
            stats['last_error_message'] = error

        self.metadata['last_update'] = datetime.now().isoformat()

    def run(self) -> bool:
        """
        Run the daily content generation pipeline.

        Returns:
            True if successful, False otherwise
        """
        logger.info("=" * 60)
        logger.info("Folklorovich Daily Content Generation Started")
        logger.info("=" * 60)

        try:
            # Select next folklore entry
            folklore_entry = self.select_next_folklore()
            if not folklore_entry:
                logger.error("Could not select folklore entry")
                return False

            # Generate content
            video_path = self.generate_content(folklore_entry)

            if video_path and video_path.exists():
                # Mark as used
                self.mark_folklore_used(folklore_entry['id'])

                # Save updated metadata
                self._save_json(self.content_dir / 'metadata.json', self.metadata)

                logger.info("=" * 60)
                logger.info("Generation Complete!")
                logger.info(f"Video: {video_path}")
                logger.info(f"Folklore: {folklore_entry['name']} ({folklore_entry['id']})")
                logger.info("=" * 60)

                return True
            else:
                logger.error("Generation failed")
                # Still save metadata to track failures
                self._save_json(self.content_dir / 'metadata.json', self.metadata)
                return False

        except Exception as e:
            logger.error(f"Critical error in generation pipeline: {e}", exc_info=True)
            return False


def main():
    """Main entry point."""
    try:
        generator = ContentGenerator()
        success = generator.run()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        logger.info("Generation cancelled by user")
        sys.exit(130)
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
        sys.exit(1)


if __name__ == '__main__':
    main()
