#!/usr/bin/env python3
"""
Folklorovich - Production-Ready Daily Content Generator
Enhanced version with comprehensive error handling, validation, and monitoring.

Author: Folklorovich Project
Date: 2025-12-05
"""

import os
import sys
import json
import random
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

# Load environment
from dotenv import load_dotenv
load_dotenv(PROJECT_ROOT / '.env')

# Import utilities
from scripts.utils import (
    setup_logging,
    retry_with_backoff,
    validate_image,
    validate_audio,
    validate_video,
    track_api_usage,
    alert_if_limits_approaching,
    generate_summary_report,
    safe_file_operation
)

# Import pipeline scripts
from scripts.fetch_images import fetch_images_for_folklore
from scripts.create_collage import create_collage
from scripts.generate_voice import generate_tts_audio
from scripts.render_video import render_video

# Initialize logging
logger = setup_logging('daily_generator', level=os.getenv('LOG_LEVEL', 'INFO'))


class ProductionContentGenerator:
    """Production-ready content generator with enhanced error handling."""

    def __init__(self):
        """Initialize generator with validation."""
        self.project_root = PROJECT_ROOT
        self.content_dir = self.project_root / 'content'
        self.output_dir = self.project_root / 'output'
        self.errors = []
        self.start_time = datetime.now()

        try:
            # Load configuration
            self.folklore_db = self._load_json_safe(
                self.content_dir / 'folklore_database.json'
            )
            self.metadata = self._load_json_safe(
                self.content_dir / 'metadata.json'
            )

            # Validate configuration
            self._validate_configuration()

            # Ensure output directories
            self._ensure_directories()

            logger.info("✓ Content generator initialized successfully")

        except Exception as e:
            logger.error(f"❌ Failed to initialize generator: {e}")
            raise

    def _load_json_safe(self, filepath: Path) -> Dict:
        """Load JSON with comprehensive error handling."""
        try:
            if not filepath.exists():
                raise FileNotFoundError(f"Configuration file missing: {filepath}")

            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)

            logger.debug(f"Loaded {filepath.name}")
            return data

        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON in {filepath}: {e}")
            raise
        except Exception as e:
            logger.error(f"Error loading {filepath}: {e}")
            raise

    def _save_json_safe(self, filepath: Path, data: Dict) -> bool:
        """Save JSON with error handling and backup."""
        try:
            # Create backup if file exists
            if filepath.exists():
                backup_path = filepath.with_suffix('.json.bak')
                safe_file_operation(lambda: filepath.rename(backup_path))

            # Save new data
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)

            logger.debug(f"Saved {filepath.name}")
            return True

        except Exception as e:
            logger.error(f"Failed to save {filepath}: {e}")
            # Restore backup if save failed
            backup_path = filepath.with_suffix('.json.bak')
            if backup_path.exists():
                safe_file_operation(lambda: backup_path.rename(filepath))
            return False

    def _validate_configuration(self):
        """Validate configuration files."""
        # Check folklore database
        if not self.folklore_db.get('folklore'):
            raise ValueError("Folklore database is empty")

        folklore_count = len(self.folklore_db['folklore'])
        if folklore_count < 1:
            raise ValueError(f"Expected at least 1 folklore entry, found {folklore_count}")

        logger.info(f"✓ Validated {folklore_count} folklore entries")

        # Check metadata structure
        required_keys = ['content_rotation', 'generation_history', 'statistics']
        for key in required_keys:
            if key not in self.metadata:
                raise ValueError(f"Missing required metadata key: {key}")

        logger.info("✓ Metadata structure validated")

    def _ensure_directories(self):
        """Create necessary output directories."""
        directories = [
            self.output_dir / 'images',
            self.output_dir / 'audio',
            self.output_dir / 'videos',
            self.project_root / 'logs'
        ]

        for directory in directories:
            directory.mkdir(parents=True, exist_ok=True)

        logger.debug("✓ Output directories ready")

    @retry_with_backoff(max_retries=3, backoff_factor=2.0)
    def select_next_folklore(self) -> Optional[Dict]:
        """
        Select next folklore entry with retry logic.

        Returns:
            Folklore entry dict or None if selection fails
        """
        folklore_list = self.folklore_db.get('folklore', [])

        # Get current cycle state
        used_ids = set(self.metadata['content_rotation']['used_ids_this_cycle'])
        all_ids = {entry['id'] for entry in folklore_list}

        # Check if cycle is complete
        if used_ids >= all_ids:
            logger.info("🔄 Cycle complete! Starting new cycle")
            self._start_new_cycle(all_ids)
            used_ids = set()

        # Get or create cycle order
        cycle_order = self.metadata['content_rotation'].get('cycle_order', [])
        if not cycle_order:
            cycle_order = list(all_ids)
            random.shuffle(cycle_order)
            self.metadata['content_rotation']['cycle_order'] = cycle_order

        # Find next unused entry
        for folklore_id in cycle_order:
            if folklore_id not in used_ids:
                entry = next((e for e in folklore_list if e['id'] == folklore_id), None)
                if entry:
                    logger.info(f"📖 Selected: {entry['name']} (ID: {folklore_id})")
                    return entry

        logger.error("❌ Could not select next folklore entry")
        return None

    def _start_new_cycle(self, all_ids: set):
        """Start new content rotation cycle."""
        self.metadata['content_rotation']['current_cycle'] += 1
        new_order = list(all_ids)
        random.shuffle(new_order)
        self.metadata['content_rotation']['cycle_order'] = new_order
        self.metadata['content_rotation']['used_ids_this_cycle'] = []

        cycle_num = self.metadata['content_rotation']['current_cycle']
        logger.info(f"🆕 Started cycle #{cycle_num}")

    def mark_folklore_used(self, folklore_id: str):
        """Mark folklore entry as used."""
        used_ids = self.metadata['content_rotation']['used_ids_this_cycle']
        if folklore_id not in used_ids:
            used_ids.append(folklore_id)

        self.metadata['content_rotation']['last_used_id'] = folklore_id
        self.metadata['content_rotation']['last_generated_date'] = datetime.now().isoformat()

    @retry_with_backoff(max_retries=2, backoff_factor=3.0, exceptions=(Exception,))
    def fetch_images_with_fallback(self, folklore_entry: Dict,
                                  output_dir: Path) -> List[Path]:
        """
        Fetch images with fallback keywords if primary search fails.

        Args:
            folklore_entry: Folklore database entry
            output_dir: Directory to save images

        Returns:
            List of downloaded image paths
        """
        visual_tags = folklore_entry['visual_tags']

        logger.info(f"🖼️  Step 1/4: Fetching images...")

        try:
            track_api_usage('unsplash', 'image_search')

            images = fetch_images_for_folklore(
                visual_tags=visual_tags,
                output_dir=output_dir,
                count=6
            )

            if images and len(images) >= 3:
                # Validate downloaded images
                valid_images = [img for img in images if validate_image(img)]

                if len(valid_images) >= 3:
                    logger.info(f"✓ Downloaded {len(valid_images)} valid images")
                    return valid_images
                else:
                    logger.warning(f"Only {len(valid_images)} valid images, retrying...")
                    raise ValueError(f"Insufficient valid images: {len(valid_images)}/3")

            # If we got here, not enough images - try fallback
            logger.warning("Primary search insufficient, trying fallback keywords")
            fallback_tags = self._get_fallback_keywords(folklore_entry)

            images = fetch_images_for_folklore(
                visual_tags=fallback_tags,
                output_dir=output_dir,
                count=6
            )

            valid_images = [img for img in images if validate_image(img)]

            if len(valid_images) >= 3:
                logger.info(f"✓ Fallback successful: {len(valid_images)} images")
                return valid_images

            raise ValueError(f"Could not fetch minimum 3 valid images")

        except Exception as e:
            error_msg = f"Image fetching failed: {e}"
            logger.error(error_msg)
            self.errors.append(error_msg)
            raise

    def _get_fallback_keywords(self, folklore_entry: Dict) -> List[str]:
        """Generate fallback keywords based on category and theme."""
        fallback_map = {
            'household_spirits': ['russian cottage', 'traditional interior', 'mystical home'],
            'mythical_creatures': ['fantasy creature', 'mythology', 'magical being'],
            'superstitions': ['mysterious ritual', 'folk tradition', 'ancient custom'],
            'rituals_traditions': ['russian tradition', 'cultural celebration', 'folk festival'],
            'curses_omens': ['mystical symbols', 'dark magic', 'supernatural signs'],
            'folk_heroes': ['heroic warrior', 'legendary figure', 'epic battle']
        }

        category = folklore_entry.get('category', 'mythical_creatures')
        fallback_keywords = fallback_map.get(category, ['russian folklore', 'slavic mythology'])

        # Add theme-based keywords
        theme = folklore_entry.get('theme', 'dark_mystical')
        if 'dark' in theme:
            fallback_keywords.append('dark atmospheric')
        elif 'warm' in theme:
            fallback_keywords.append('warm traditional')
        elif 'winter' in theme:
            fallback_keywords.append('winter snow')

        return fallback_keywords[:4]

    def create_collage_with_validation(self, image_paths: List[Path],
                                      collage_path: Path,
                                      folklore_entry: Dict) -> bool:
        """Create collage with quality validation."""
        logger.info("🎨 Step 2/4: Creating collage...")

        try:
            # Get title - try different fields
            title = folklore_entry.get('name_russian', folklore_entry.get('name', ''))
            subtitle = folklore_entry.get('moral', '')

            success = create_collage(
                image_paths=image_paths,
                output_path=collage_path,
                title=title,
                subtitle=subtitle[:100] if subtitle else None,  # Limit subtitle length
                layout_name=None  # Random template
            )

            if not success:
                raise ValueError("Collage creation returned False")

            # Validate output
            if not validate_image(collage_path, min_width=1080, min_height=1920):
                raise ValueError("Generated collage failed validation")

            logger.info(f"✓ Collage created: {collage_path.name}")
            return True

        except Exception as e:
            error_msg = f"Collage creation failed: {e}"
            logger.error(error_msg)
            self.errors.append(error_msg)
            return False

    def generate_audio_with_validation(self, folklore_entry: Dict,
                                      audio_path: Path) -> bool:
        """Generate TTS audio with validation."""
        logger.info("🎙️  Step 3/4: Generating audio...")

        try:
            track_api_usage('edge_tts', 'synthesis')

            text = folklore_entry.get('story_full', '')
            if not text or len(text) < 50:
                raise ValueError(f"Story text too short: {len(text)} characters")

            voice_tone = folklore_entry.get('voice_tone', 'warm_mysterious')
            target_duration = folklore_entry.get('duration_target', 30)

            success = generate_tts_audio(
                text=text,
                output_path=audio_path,
                voice_tone=voice_tone,
                target_duration=target_duration
            )

            if not success:
                raise ValueError("Audio generation returned False")

            # Validate output
            if not validate_audio(audio_path, min_duration=15, max_duration=45):
                raise ValueError("Generated audio failed validation")

            logger.info(f"✓ Audio generated: {audio_path.name}")
            return True

        except Exception as e:
            error_msg = f"Audio generation failed: {e}"
            logger.error(error_msg)
            self.errors.append(error_msg)
            return False

    def render_video_with_validation(self, collage_path: Path,
                                    audio_path: Path,
                                    video_path: Path) -> bool:
        """Render video with validation."""
        logger.info("🎬 Step 4/4: Rendering video...")

        try:
            success = render_video(
                image_path=collage_path,
                audio_path=audio_path,
                output_path=video_path
            )

            if not success:
                raise ValueError("Video rendering returned False")

            # Validate output
            if not validate_video(video_path, min_duration=20, max_duration=40):
                raise ValueError("Generated video failed validation")

            # Check file size (should be reasonable)
            size_mb = video_path.stat().st_size / (1024 * 1024)
            if size_mb < 0.5:
                raise ValueError(f"Video file too small: {size_mb:.2f} MB")

            logger.info(f"✓ Video rendered: {video_path.name} ({size_mb:.2f} MB)")
            return True

        except Exception as e:
            error_msg = f"Video rendering failed: {e}"
            logger.error(error_msg)
            self.errors.append(error_msg)
            return False

    def generate_content(self, folklore_entry: Dict) -> Optional[Path]:
        """
        Generate complete video content with full error handling.

        Args:
            folklore_entry: Folklore database entry

        Returns:
            Path to generated video or None if failed
        """
        folklore_id = folklore_entry['id']
        folklore_name = folklore_entry['name']
        date_str = datetime.now().strftime('%Y-%m-%d')

        logger.info("=" * 60)
        logger.info(f"🎭 Generating: {folklore_name} (ID: {folklore_id})")
        logger.info("=" * 60)

        try:
            # Create output subdirectory
            output_subdir = self.output_dir / 'images' / f"{date_str}_{folklore_id}"
            output_subdir.mkdir(parents=True, exist_ok=True)

            # Step 1: Fetch images
            image_paths = self.fetch_images_with_fallback(folklore_entry, output_subdir)
            if not image_paths:
                raise ValueError("Failed to fetch images")

            # Step 2: Create collage
            collage_path = self.output_dir / 'images' / f"{date_str}_{folklore_id}_collage.png"
            if not self.create_collage_with_validation(image_paths, collage_path, folklore_entry):
                raise ValueError("Failed to create collage")

            # Step 3: Generate audio
            audio_path = self.output_dir / 'audio' / f"{date_str}_{folklore_id}.mp3"
            if not self.generate_audio_with_validation(folklore_entry, audio_path):
                raise ValueError("Failed to generate audio")

            # Step 4: Render video
            video_filename = f"{date_str}_{folklore_name.replace(' ', '_')}.mp4"
            video_path = self.output_dir / 'videos' / video_filename

            if not self.render_video_with_validation(collage_path, audio_path, video_path):
                raise ValueError("Failed to render video")

            # Success!
            generation_time = (datetime.now() - self.start_time).total_seconds()
            self._update_statistics(folklore_entry, generation_time, success=True)

            logger.info("=" * 60)
            logger.info(f"✅ SUCCESS! Video generated in {generation_time:.1f}s")
            logger.info(f"📹 Output: {video_path}")
            logger.info("=" * 60)

            return video_path

        except Exception as e:
            generation_time = (datetime.now() - self.start_time).total_seconds()
            self._update_statistics(folklore_entry, generation_time,
                                  success=False, error=str(e))

            logger.error("=" * 60)
            logger.error(f"❌ FAILED after {generation_time:.1f}s: {e}")
            logger.error("=" * 60)

            return None

    def _update_statistics(self, folklore_entry: Dict, generation_time: float,
                          success: bool, error: Optional[str] = None):
        """Update metadata statistics."""
        stats = self.metadata['generation_history']
        stats['total_videos_generated'] += 1

        if success:
            stats['successful_generations'] += 1
            stats['last_success_date'] = datetime.now().isoformat()

            # Category stats
            category = folklore_entry.get('category', 'unknown')
            cat_stats = self.metadata['statistics']['by_category']
            cat_stats[category] = cat_stats.get(category, 0) + 1

            # Voice tone stats
            voice = folklore_entry.get('voice_tone', 'unknown')
            voice_stats = self.metadata['statistics']['by_voice_tone']
            voice_stats[voice] = voice_stats.get(voice, 0) + 1

            # Average generation time
            avg_time = self.metadata['statistics'].get('average_generation_time_seconds')
            if avg_time is None:
                self.metadata['statistics']['average_generation_time_seconds'] = generation_time
            else:
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
        try:
            # Check API limits before starting
            alert_if_limits_approaching()

            # Select folklore entry
            folklore_entry = self.select_next_folklore()
            if not folklore_entry:
                logger.error("❌ Could not select folklore entry")
                return False

            # Generate content
            video_path = self.generate_content(folklore_entry)

            if video_path and video_path.exists():
                # Mark as used
                self.mark_folklore_used(folklore_entry['id'])

                # Save metadata
                if not self._save_json_safe(self.content_dir / 'metadata.json', self.metadata):
                    logger.warning("⚠️  Failed to save metadata (generation succeeded)")

                # Print summary
                generation_time = (datetime.now() - self.start_time).total_seconds()
                summary = generate_summary_report(
                    folklore_entry['id'],
                    success=True,
                    generation_time=generation_time,
                    errors=self.errors
                )
                logger.info(f"\n{summary}")

                return True
            else:
                logger.error("❌ Generation failed")
                self._save_json_safe(self.content_dir / 'metadata.json', self.metadata)

                generation_time = (datetime.now() - self.start_time).total_seconds()
                summary = generate_summary_report(
                    folklore_entry.get('id', 'unknown'),
                    success=False,
                    generation_time=generation_time,
                    errors=self.errors
                )
                logger.error(f"\n{summary}")

                return False

        except Exception as e:
            logger.error(f"❌ Critical error in pipeline: {e}", exc_info=True)
            return False


def main():
    """Main entry point."""
    try:
        generator = ProductionContentGenerator()
        success = generator.run()
        sys.exit(0 if success else 1)

    except KeyboardInterrupt:
        logger.info("\n⚠️  Generation cancelled by user")
        sys.exit(130)

    except Exception as e:
        logger.error(f"💥 Fatal error: {e}", exc_info=True)
        sys.exit(1)


if __name__ == '__main__':
    main()
