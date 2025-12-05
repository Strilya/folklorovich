#!/usr/bin/env python3
"""
Folklorovich - Slideshow Video Renderer
Creates dynamic slideshow videos with crossfade transitions and text overlays.

SLIDESHOW FEATURES:
- Each image displays for exactly 2 seconds
- Smooth crossfade transitions (0.5s) between images
- Text overlay (folklore name) visible throughout video
- 1080x1920 vertical format (Instagram Reels/TikTok)
- Synced to audio duration

Author: Folklorovich Project
Date: 2025-12-05
Updated: Complete rewrite for slideshow rendering
"""

import os
import subprocess
import logging
from pathlib import Path
from typing import Optional, List

# Configure logging
logger = logging.getLogger('VideoRenderer')


class SlideshowRenderer:
    """Renders slideshow videos using FFmpeg complex filters."""

    def __init__(self):
        """Initialize slideshow renderer."""
        # Get video settings from environment or use defaults
        self.width = int(os.getenv('VIDEO_WIDTH', 1080))
        self.height = int(os.getenv('VIDEO_HEIGHT', 1920))
        self.fps = int(os.getenv('VIDEO_FPS', 30))
        self.video_codec = os.getenv('VIDEO_CODEC', 'libx264')
        self.audio_codec = os.getenv('AUDIO_CODEC', 'aac')

        # Slideshow settings
        self.image_duration = 2.0  # Each image displays for 2 seconds
        self.fade_duration = 0.5   # 0.5 second crossfade between images

        # Check if FFmpeg is available
        if not self._check_ffmpeg():
            raise RuntimeError("FFmpeg not found. Please install FFmpeg.")

        logger.info("Slideshow renderer initialized")
        logger.info(f"Settings: {self.width}x{self.height} @ {self.fps}fps, "
                   f"{self.image_duration}s per image, {self.fade_duration}s crossfade")

    def _check_ffmpeg(self) -> bool:
        """Check if FFmpeg is installed."""
        try:
            subprocess.run(['ffmpeg', '-version'], capture_output=True, check=True)
            return True
        except (subprocess.CalledProcessError, FileNotFoundError):
            logger.error("FFmpeg not found. Install with: brew install ffmpeg")
            return False

    def get_audio_duration(self, audio_path: Path) -> Optional[float]:
        """
        Get duration of audio file using ffprobe.

        Args:
            audio_path: Path to audio file

        Returns:
            Duration in seconds or None if error
        """
        try:
            cmd = [
                'ffprobe',
                '-v', 'error',
                '-show_entries', 'format=duration',
                '-of', 'default=noprint_wrappers=1:nokey=1',
                str(audio_path)
            ]

            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            duration = float(result.stdout.strip())
            return duration

        except (subprocess.CalledProcessError, ValueError, FileNotFoundError) as e:
            logger.error(f"Error getting audio duration: {e}")
            return None

    def _build_slideshow_filter(self, num_images: int, audio_duration: float) -> str:
        """
        Build FFmpeg complex filter for slideshow with crossfade transitions.

        The filter chain:
        1. Scale each image to 1080x1920 (crop to fit)
        2. Display each for 2 seconds
        3. Crossfade 0.5s between consecutive images
        4. Loop last image if needed to match audio duration

        Args:
            num_images: Number of input images
            audio_duration: Total duration to match

        Returns:
            FFmpeg filter_complex string
        """
        filters = []

        # Step 1: Scale and format each input image
        for i in range(num_images):
            filters.append(
                f"[{i}:v]scale={self.width}:{self.height}:force_original_aspect_ratio=increase,"
                f"crop={self.width}:{self.height},setsar=1,fps={self.fps}[v{i}]"
            )

        # Step 2: Create slideshow with crossfades
        # Each image is 2 seconds, with 0.5s crossfade overlap
        # Effective time per image = 2s - 0.5s overlap = 1.5s of unique content per transition

        if num_images == 1:
            # Single image: just loop it for the duration
            filters.append(f"[v0]trim=duration={audio_duration},setpts=PTS-STARTPTS[out]")
        else:
            # Multiple images: create crossfade chain
            fade_filters = []

            for i in range(num_images - 1):
                # Calculate fade timing
                # Image i starts at: i * 1.5s (accounting for overlaps)
                # Fade starts at: i * 2s + (2s - 0.5s) = i * 2s + 1.5s
                offset = i * (self.image_duration - self.fade_duration)

                if i == 0:
                    # First transition: v0 fades to v1
                    fade_filters.append(
                        f"[v0][v1]xfade=transition=fade:duration={self.fade_duration}:"
                        f"offset={self.image_duration - self.fade_duration}[f0]"
                    )
                else:
                    # Subsequent transitions: previous fade result fades to next image
                    fade_filters.append(
                        f"[f{i-1}][v{i+1}]xfade=transition=fade:duration={self.fade_duration}:"
                        f"offset={offset + self.image_duration - self.fade_duration}[f{i}]"
                    )

            # Add the fade chain to filters
            filters.extend(fade_filters)

            # The final output is the last fade result
            final_label = f"f{num_images - 2}" if num_images > 2 else "f0"

            # Calculate expected slideshow duration
            # Note: with xfade, total duration = (N * image_duration) - ((N-1) * fade_duration)
            # For 10 images: (10 * 2.0) - (9 * 0.5) = 20.0 - 4.5 = 15.5s
            slideshow_duration = (num_images * self.image_duration) - ((num_images - 1) * self.fade_duration)

            # The xfade filter will handle the timing internally
            # We just need to trim or extend the final result to match audio_duration
            if slideshow_duration < audio_duration:
                # Slideshow is shorter than audio - we need to extend the last frame
                remaining_time = audio_duration - slideshow_duration
                logger.info(f"Extending video by {remaining_time:.2f}s to match audio (slideshow: {slideshow_duration:.2f}s, audio: {audio_duration:.2f}s)")

                # Create a static frame from the last faded output and extend it
                filters.append(
                    f"[{final_label}]tpad=stop_mode=clone:stop_duration={remaining_time}[out]"
                )
            elif slideshow_duration > audio_duration:
                # Slideshow is longer than audio - trim it
                logger.info(f"Trimming slideshow from {slideshow_duration:.2f}s to {audio_duration:.2f}s")
                filters.append(f"[{final_label}]trim=duration={audio_duration},setpts=PTS-STARTPTS[out]")
            else:
                # Perfect match (unlikely but possible)
                filters.append(f"[{final_label}]copy[out]")

        return ';'.join(filters)

    def _add_text_overlay(self, title_text: str) -> str:
        """
        Build FFmpeg drawtext filter for title overlay.

        The text appears at the top of the video with:
        - Shadow for readability
        - Semi-transparent background box
        - Cyrillic font support

        Args:
            title_text: Text to display

        Returns:
            FFmpeg drawtext filter string
        """
        # Escape special characters for FFmpeg
        safe_text = title_text.replace(':', '\\:').replace("'", "\\'")

        # Font settings
        font_size = 70
        font_color = "white"
        box_color = "black@0.6"  # Semi-transparent black background

        # Position: centered horizontally, near top
        x_pos = "(w-text_w)/2"  # Centered
        y_pos = "80"  # 80 pixels from top

        drawtext_filter = (
            f"drawtext=text='{safe_text}':"
            f"fontsize={font_size}:"
            f"fontcolor={font_color}:"
            f"x={x_pos}:y={y_pos}:"
            f"box=1:boxcolor={box_color}:boxborderw=20:"
            f"shadowcolor=black@0.8:shadowx=2:shadowy=2"
        )

        return drawtext_filter

    def render_slideshow(self, image_paths: List[Path], audio_path: Path,
                        output_path: Path, title_text: str,
                        audio_duration: float) -> bool:
        """
        Render slideshow video with crossfade transitions and text overlay.

        Process:
        1. Validate inputs
        2. Build complex filter for slideshow
        3. Add text overlay
        4. Combine with audio
        5. Encode with Instagram-optimized settings

        Args:
            image_paths: List of image file paths
            audio_path: Path to audio file
            output_path: Path to save output video
            title_text: Text to display as overlay
            audio_duration: Duration to match (from audio)

        Returns:
            True if successful, False otherwise
        """
        try:
            # Validate inputs
            if not image_paths:
                logger.error("No images provided")
                return False

            if not audio_path.exists():
                logger.error(f"Audio file not found: {audio_path}")
                return False

            num_images = len(image_paths)
            logger.info(f"Rendering slideshow with {num_images} images, "
                       f"duration: {audio_duration:.2f}s")

            # Ensure output directory exists
            output_path.parent.mkdir(parents=True, exist_ok=True)

            # Build FFmpeg command
            cmd = ['ffmpeg', '-y']  # Overwrite output

            # Add input images
            for img_path in image_paths:
                cmd.extend(['-loop', '1', '-t', str(self.image_duration), '-i', str(img_path)])

            # Add audio input
            cmd.extend(['-i', str(audio_path)])

            # Build filter_complex for slideshow
            slideshow_filter = self._build_slideshow_filter(num_images, audio_duration)

            # Add text overlay to the final output
            text_overlay = self._add_text_overlay(title_text)
            full_filter = f"{slideshow_filter};[out]{text_overlay}[final]"

            # Add filter_complex to command
            cmd.extend(['-filter_complex', full_filter])

            # Map outputs
            cmd.extend([
                '-map', '[final]',  # Video from filter
                '-map', f'{num_images}:a',  # Audio from audio input
            ])

            # Video encoding settings
            cmd.extend([
                '-c:v', self.video_codec,
                '-preset', 'medium',  # Encoding speed/quality balance
                '-crf', '23',  # Quality (18-28 range, 23 is good balance)
                '-pix_fmt', 'yuv420p',  # Compatibility
                '-r', str(self.fps),  # Frame rate
            ])

            # Audio encoding settings
            cmd.extend([
                '-c:a', self.audio_codec,
                '-b:a', '192k',  # Audio bitrate
                '-ar', '44100',  # Sample rate
            ])

            # Duration and optimization
            cmd.extend([
                '-t', str(audio_duration),  # Match audio duration exactly
                '-shortest',  # End when shortest stream ends
                '-movflags', '+faststart',  # Web optimization
            ])

            # Output file
            cmd.append(str(output_path))

            # Log the command for debugging
            logger.debug(f"FFmpeg command: {' '.join(cmd)}")

            # Run FFmpeg
            logger.info("Running FFmpeg (this may take 30-60 seconds)...")
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=180  # 3 minute timeout
            )

            if result.returncode != 0:
                logger.error(f"FFmpeg failed with return code {result.returncode}")
                logger.error(f"FFmpeg stderr: {result.stderr[-1000:]}")  # Last 1000 chars
                return False

            # Verify output file
            if output_path.exists() and output_path.stat().st_size > 0:
                size_mb = output_path.stat().st_size / (1024 * 1024)
                logger.info(f"✓ Slideshow video rendered: {output_path.name} ({size_mb:.2f} MB)")

                # Verify duration matches
                actual_duration = self.get_audio_duration(output_path)
                if actual_duration:
                    duration_diff = abs(actual_duration - audio_duration)
                    logger.info(f"Video duration: {actual_duration:.2f}s "
                               f"(target: {audio_duration:.2f}s, diff: {duration_diff:.2f}s)")

                return True
            else:
                logger.error("Output video is missing or empty")
                return False

        except subprocess.TimeoutExpired:
            logger.error("FFmpeg timeout (>3 minutes)")
            return False
        except Exception as e:
            logger.error(f"Slideshow rendering failed: {e}", exc_info=True)
            return False


def render_slideshow_video(image_paths: List[Path], audio_path: Path,
                           output_path: Path, title_text: str,
                           audio_duration: float) -> bool:
    """
    Convenience function to render a slideshow video.

    Args:
        image_paths: List of image file paths
        audio_path: Path to audio file
        output_path: Path to save output video
        title_text: Text to display as overlay
        audio_duration: Duration to match (from audio)

    Returns:
        True if successful, False otherwise
    """
    try:
        renderer = SlideshowRenderer()
        return renderer.render_slideshow(
            image_paths, audio_path, output_path, title_text, audio_duration
        )
    except RuntimeError as e:
        logger.error(f"Renderer initialization failed: {e}")
        return False
    except Exception as e:
        logger.error(f"Slideshow rendering failed: {e}", exc_info=True)
        return False


def main():
    """Test the slideshow renderer."""
    import sys

    logging.basicConfig(level=logging.INFO)

    if len(sys.argv) < 4:
        print("Usage: python render_video.py <image1> <image2> [...] <audio_path> <output_path>")
        print("Example: python render_video.py img1.jpg img2.jpg img3.jpg audio.mp3 output.mp4")
        sys.exit(1)

    # Parse arguments: all but last 2 are images, second to last is audio, last is output
    image_paths = [Path(p) for p in sys.argv[1:-2]]
    audio_path = Path(sys.argv[-2])
    output_path = Path(sys.argv[-1])

    # Check inputs exist
    for img_path in image_paths:
        if not img_path.exists():
            print(f"Error: Image not found: {img_path}")
            sys.exit(1)

    if not audio_path.exists():
        print(f"Error: Audio not found: {audio_path}")
        sys.exit(1)

    # Get audio duration
    renderer = SlideshowRenderer()
    audio_duration = renderer.get_audio_duration(audio_path)

    if not audio_duration:
        print("Error: Could not determine audio duration")
        sys.exit(1)

    print(f"Creating slideshow with {len(image_paths)} images, duration: {audio_duration:.2f}s")

    # Render slideshow
    success = render_slideshow_video(
        image_paths=image_paths,
        audio_path=audio_path,
        output_path=output_path,
        title_text="Test Slideshow",
        audio_duration=audio_duration
    )

    if success:
        print(f"\n✓ Slideshow video saved to: {output_path}")
    else:
        print("\n✗ Slideshow rendering failed")

    sys.exit(0 if success else 1)


if __name__ == '__main__':
    main()
