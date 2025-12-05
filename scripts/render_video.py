#!/usr/bin/env python3
"""
Folklorovich - Video Renderer
Combines image collage and audio into Instagram-ready video using FFmpeg.

Features:
- 1080x1920 vertical format (Instagram Reels)
- Fade in/out effects
- High-quality H.264 encoding
- Audio synchronization
- Russian subtitle generation and burning
- @folklorovich watermark

Author: Folklorovich Project
Date: 2025-12-05
"""

import os
import subprocess
import logging
import tempfile
from pathlib import Path
from typing import Optional

# Configure logging
logger = logging.getLogger('VideoRenderer')


class VideoRenderer:
    """Renders videos using FFmpeg."""

    def __init__(self):
        """Initialize video renderer."""
        # Get video settings from environment or use defaults
        self.width = int(os.getenv('VIDEO_WIDTH', 1080))
        self.height = int(os.getenv('VIDEO_HEIGHT', 1920))
        self.fps = int(os.getenv('VIDEO_FPS', 30))
        self.video_codec = os.getenv('VIDEO_CODEC', 'libx264')
        self.audio_codec = os.getenv('AUDIO_CODEC', 'aac')

        # Check if FFmpeg is available
        if not self._check_ffmpeg():
            raise RuntimeError("FFmpeg not found. Please install FFmpeg.")

        logger.info("Video renderer initialized")

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

    def generate_srt_subtitles(self, text: str, duration: float, output_path: Path) -> bool:
        """
        Generate SRT subtitle file from Russian text.

        Splits text into 2-3 word chunks and creates properly timed subtitles.
        Each subtitle appears for approximately 2 seconds.

        Args:
            text: Russian text to convert to subtitles
            duration: Total video duration in seconds
            output_path: Path to save .srt file

        Returns:
            True if successful, False otherwise
        """
        try:
            # Split text into words
            words = text.strip().split()

            if not words:
                logger.error("Empty text provided for subtitles")
                return False

            # Group words into chunks of 2-3 words
            chunks = []
            i = 0
            while i < len(words):
                # Take 2-3 words per chunk (prefer 3 if available)
                chunk_size = min(3, len(words) - i)
                if chunk_size == 1 and i + 1 < len(words):
                    chunk_size = 2  # Avoid single-word chunks unless it's the last word

                chunk = ' '.join(words[i:i + chunk_size])
                chunks.append(chunk)
                i += chunk_size

            # Calculate timing for each subtitle
            subtitle_duration = 2.0  # 2 seconds per subtitle
            total_subtitle_time = len(chunks) * subtitle_duration

            # If subtitles would exceed video duration, adjust timing
            if total_subtitle_time > duration:
                subtitle_duration = duration / len(chunks)

            # Generate SRT content
            srt_content = []
            current_time = 0.0

            for idx, chunk in enumerate(chunks, start=1):
                start_time = current_time
                end_time = min(current_time + subtitle_duration, duration)

                # Format timestamps (HH:MM:SS,mmm)
                start_str = self._format_srt_timestamp(start_time)
                end_str = self._format_srt_timestamp(end_time)

                srt_content.append(f"{idx}")
                srt_content.append(f"{start_str} --> {end_str}")
                srt_content.append(chunk)
                srt_content.append("")  # Empty line between subtitles

                current_time = end_time

            # Write SRT file
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write('\n'.join(srt_content))

            logger.info(f"Generated {len(chunks)} subtitles: {output_path}")
            return True

        except Exception as e:
            logger.error(f"Subtitle generation failed: {e}", exc_info=True)
            return False

    def _format_srt_timestamp(self, seconds: float) -> str:
        """
        Format seconds as SRT timestamp (HH:MM:SS,mmm).

        Args:
            seconds: Time in seconds

        Returns:
            Formatted timestamp string
        """
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        millisecs = int((seconds % 1) * 1000)

        return f"{hours:02d}:{minutes:02d}:{secs:02d},{millisecs:03d}"

    def render_video(self, image_path: Path, audio_path: Path,
                    output_path: Path, subtitle_text: Optional[str] = None) -> bool:
        """
        Render video from image and audio using FFmpeg.

        Process:
        1. Get audio duration
        2. Generate SRT subtitles if subtitle_text provided
        3. Create video from static image (loop for audio duration)
        4. Add audio track
        5. Apply fade in/out effects
        6. Burn subtitles into video (if provided)
        7. Add @folklorovich watermark
        8. Encode with Instagram-optimized settings

        Args:
            image_path: Path to collage image
            audio_path: Path to audio file
            output_path: Path to save output video
            subtitle_text: Optional Russian text for subtitles

        Returns:
            True if successful, False otherwise
        """
        srt_file = None
        try:
            # Get audio duration
            duration = self.get_audio_duration(audio_path)
            if not duration:
                logger.error("Could not determine audio duration")
                return False

            logger.info(f"Rendering video (duration: {duration:.2f}s)...")

            # Generate subtitles if text provided
            if subtitle_text:
                # Create temporary SRT file
                srt_file = tempfile.NamedTemporaryFile(
                    mode='w',
                    suffix='.srt',
                    delete=False,
                    encoding='utf-8'
                )
                srt_path = Path(srt_file.name)
                srt_file.close()

                success = self.generate_srt_subtitles(subtitle_text, duration, srt_path)
                if not success:
                    logger.warning("Failed to generate subtitles, continuing without them")
                    srt_file = None
                else:
                    logger.info("Subtitles generated, will burn into video")

            # Ensure output directory exists
            output_path.parent.mkdir(parents=True, exist_ok=True)

            # Build FFmpeg command
            # This creates a video from a static image with audio
            cmd = [
                'ffmpeg',
                '-y',  # Overwrite output file
                '-loop', '1',  # Loop the image
                '-i', str(image_path),  # Input image
                '-i', str(audio_path),  # Input audio
                '-c:v', self.video_codec,  # Video codec
                '-t', str(duration),  # Duration matches audio
                '-pix_fmt', 'yuv420p',  # Pixel format for compatibility
                '-c:a', self.audio_codec,  # Audio codec
                '-b:a', '192k',  # Audio bitrate
                '-ar', '44100',  # Audio sample rate
                '-vf', self._build_video_filters(duration, srt_path if srt_file else None),
                '-shortest',  # End when shortest stream ends
                '-movflags', '+faststart',  # Web optimization
                '-preset', 'medium',  # Encoding speed/quality balance
                '-crf', '23',  # Quality (lower = better, 18-28 recommended)
                str(output_path)
            ]

            # Run FFmpeg
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=120  # 2 minute timeout
            )

            if result.returncode != 0:
                logger.error(f"FFmpeg failed: {result.stderr}")
                return False

            # Verify output file
            if output_path.exists() and output_path.stat().st_size > 0:
                size_mb = output_path.stat().st_size / (1024 * 1024)
                logger.info(f"Video rendered: {output_path.name} ({size_mb:.2f} MB)")
                return True
            else:
                logger.error("Output video is missing or empty")
                return False

        except subprocess.TimeoutExpired:
            logger.error("FFmpeg timeout (>2 minutes)")
            return False
        except Exception as e:
            logger.error(f"Video rendering failed: {e}", exc_info=True)
            return False
        finally:
            # Clean up temporary SRT file
            if srt_file:
                try:
                    Path(srt_file.name).unlink(missing_ok=True)
                except Exception as e:
                    logger.warning(f"Could not delete temp SRT file: {e}")

    def _build_video_filters(self, duration: float, subtitle_path: Optional[Path] = None) -> str:
        """
        Build FFmpeg video filter string.

        Adds:
        - Scale to output dimensions
        - Fade in (0.5s)
        - Fade out (0.5s)
        - Subtitles (if provided) with custom styling
        - @folklorovich watermark (bottom right)

        Args:
            duration: Video duration in seconds
            subtitle_path: Optional path to SRT subtitle file

        Returns:
            FFmpeg filter string
        """
        fade_duration = 0.5  # 0.5 second fades

        filters = [
            f"scale={self.width}:{self.height}:force_original_aspect_ratio=decrease",
            f"pad={self.width}:{self.height}:(ow-iw)/2:(oh-ih)/2",  # Center pad
            f"fps={self.fps}",
            f"fade=t=in:st=0:d={fade_duration}",  # Fade in
            f"fade=t=out:st={duration - fade_duration}:d={fade_duration}"  # Fade out
        ]

        # Add subtitles filter if SRT file provided
        if subtitle_path:
            # Escape the path for FFmpeg (handle special characters)
            srt_escaped = str(subtitle_path).replace('\\', '/').replace(':', '\\:')

            # FFmpeg subtitle filter with custom styling
            # Style format: FontName=Arial,FontSize=28,PrimaryColour=&HFFFFFF,etc.
            # Colors in FFmpeg are in &HAABBGGRR format (AA=alpha, BB=blue, GG=green, RR=red)
            # &HFFFFFF = white text
            # &H000000 = black outline
            # &H40000000 = semi-transparent black background (40 hex = ~25% opacity)
            subtitle_style = (
                "FontName=Arial,"
                "FontSize=28,"
                "PrimaryColour=&HFFFFFF,"  # White text
                "OutlineColour=&H000000,"  # Black outline
                "Outline=2,"  # Outline thickness
                "MarginV=50,"  # Bottom margin 50px
                "BackColour=&H40000000,"  # Semi-transparent black background
                "BorderStyle=4"  # Background box style
            )
            filters.append(f"subtitles={srt_escaped}:force_style='{subtitle_style}'")

        # Add @folklorovich watermark (bottom right corner)
        # Position: x=w-tw-20 (20px from right), y=h-th-20 (20px from bottom)
        # Color: white with 20% opacity (0.2 alpha)
        watermark_filter = (
            "drawtext=text='@folklorovich':"
            "fontcolor=white@0.2:"  # White with 20% opacity
            "fontsize=18:"
            "x=w-tw-20:"  # 20px from right edge
            "y=h-th-20"  # 20px from bottom edge
        )
        filters.append(watermark_filter)

        return ','.join(filters)

    def add_watermark(self, video_path: Path, watermark_text: str,
                     output_path: Path) -> bool:
        """
        Add text watermark to video (optional feature).

        Args:
            video_path: Path to input video
            watermark_text: Text to display
            output_path: Path to save output

        Returns:
            True if successful, False otherwise
        """
        try:
            cmd = [
                'ffmpeg',
                '-y',
                '-i', str(video_path),
                '-vf', f"drawtext=text='{watermark_text}':fontcolor=white@0.5:"
                      f"fontsize=24:x=10:y=H-th-10",
                '-codec:a', 'copy',
                str(output_path)
            ]

            result = subprocess.run(cmd, capture_output=True, timeout=60)
            return result.returncode == 0

        except Exception as e:
            logger.error(f"Watermark failed: {e}")
            return False


def render_video(image_path: Path, audio_path: Path, output_path: Path,
                subtitle_text: Optional[str] = None) -> bool:
    """
    Convenience function to render a video.

    Args:
        image_path: Path to collage image
        audio_path: Path to audio file
        output_path: Path to save output video
        subtitle_text: Optional Russian text for subtitles

    Returns:
        True if successful, False otherwise
    """
    try:
        renderer = VideoRenderer()
        return renderer.render_video(image_path, audio_path, output_path, subtitle_text)
    except RuntimeError as e:
        logger.error(f"Renderer initialization failed: {e}")
        return False
    except Exception as e:
        logger.error(f"Video rendering failed: {e}", exc_info=True)
        return False


def main():
    """Test the video renderer."""
    import sys

    logging.basicConfig(level=logging.INFO)

    if len(sys.argv) < 4:
        print("Usage: python render_video.py <image_path> <audio_path> <output_path>")
        sys.exit(1)

    image_path = Path(sys.argv[1])
    audio_path = Path(sys.argv[2])
    output_path = Path(sys.argv[3])

    # Check inputs exist
    if not image_path.exists():
        print(f"Error: Image not found: {image_path}")
        sys.exit(1)

    if not audio_path.exists():
        print(f"Error: Audio not found: {audio_path}")
        sys.exit(1)

    # Render video
    success = render_video(image_path, audio_path, output_path)

    if success:
        print(f"\n✓ Video saved to: {output_path}")
    else:
        print("\n✗ Video rendering failed")

    sys.exit(0 if success else 1)


if __name__ == '__main__':
    main()
