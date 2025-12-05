#!/usr/bin/env python3
"""
Folklorovich - TTS Voice Generator
Generates Russian narration audio using Edge TTS (free, unlimited).

Features:
- Multiple Russian voice profiles
- Speed adjustment to match target duration
- High-quality audio output (MP3)
- Duration validation

Author: Folklorovich Project
Date: 2025-12-05
"""

import os
import asyncio
import logging
from pathlib import Path
from typing import Optional
import subprocess

try:
    import edge_tts
except ImportError:
    logging.error("edge-tts not installed. Run: pip install edge-tts")
    raise

# Configure logging
logger = logging.getLogger('VoiceGenerator')

# Voice profiles mapping
VOICE_PROFILES = {
    'warm_grandfather': {
        'voice': 'ru-RU-DmitryNeural',
        'rate': '+0%',
        'pitch': '-5Hz',
        'description': 'Warm, friendly storytelling voice'
    },
    'mysterious_elder': {
        'voice': 'ru-RU-SvetlanaNeural',
        'rate': '-10%',
        'pitch': '-10Hz',
        'description': 'Slow, enigmatic female voice'
    },
    'energetic_youth': {
        'voice': 'ru-RU-DariyaNeural',
        'rate': '+10%',
        'pitch': '+5Hz',
        'description': 'Upbeat, modern female voice'
    },
    'solemn_narrator': {
        'voice': 'ru-RU-DmitryNeural',
        'rate': '-5%',
        'pitch': '-15Hz',
        'description': 'Formal, serious male voice'
    },
    # New voice tones for superstitions
    'ominous': {
        'voice': 'ru-RU-DmitryNeural',
        'rate': '-5%',
        'pitch': '-15Hz',
        'description': 'Dark, foreboding male voice'
    },
    'cautionary': {
        'voice': 'ru-RU-SvetlanaNeural',
        'rate': '-5%',
        'pitch': '-5Hz',
        'description': 'Warning, careful female voice'
    },
    'stern': {
        'voice': 'ru-RU-DmitryNeural',
        'rate': '+0%',
        'pitch': '-10Hz',
        'description': 'Strict, firm male voice'
    },
    'warm_storyteller': {
        'voice': 'ru-RU-SvetlanaNeural',
        'rate': '+0%',
        'pitch': '+0Hz',
        'description': 'Warm, engaging female storyteller'
    },
    'wise_elder': {
        'voice': 'ru-RU-DmitryNeural',
        'rate': '-10%',
        'pitch': '-10Hz',
        'description': 'Slow, wise elder male voice'
    },
    'protective': {
        'voice': 'ru-RU-SvetlanaNeural',
        'rate': '-5%',
        'pitch': '+0Hz',
        'description': 'Caring, protective female voice'
    }
}

DEFAULT_VOICE_PROFILE = 'warm_grandfather'


class TTSGenerator:
    """Generates TTS audio using Microsoft Edge TTS."""

    def __init__(self):
        """Initialize TTS generator."""
        self.voice_profiles = VOICE_PROFILES
        logger.info("TTS generator initialized")

    def get_voice_config(self, voice_tone: str) -> dict:
        """
        Get voice configuration for a given tone.

        Args:
            voice_tone: Voice tone name (e.g., 'warm_grandfather')

        Returns:
            Voice configuration dict
        """
        config = self.voice_profiles.get(voice_tone)

        if not config:
            logger.warning(f"Unknown voice tone '{voice_tone}', using default")
            config = self.voice_profiles[DEFAULT_VOICE_PROFILE]

        return config

    async def generate_audio_async(self, text: str, output_path: Path,
                                   voice_config: dict) -> bool:
        """
        Generate TTS audio asynchronously.

        Args:
            text: Text to synthesize
            output_path: Path to save audio file
            voice_config: Voice configuration dict

        Returns:
            True if successful, False otherwise
        """
        try:
            # Create TTS communicator
            communicate = edge_tts.Communicate(
                text=text,
                voice=voice_config['voice'],
                rate=voice_config.get('rate', '+0%'),
                pitch=voice_config.get('pitch', '+0Hz')
            )

            # Ensure output directory exists
            output_path.parent.mkdir(parents=True, exist_ok=True)

            # Generate and save audio
            await communicate.save(str(output_path))

            # Verify file exists and has content
            if output_path.exists() and output_path.stat().st_size > 0:
                logger.info(f"✓ Generated audio: {output_path.name} "
                          f"({output_path.stat().st_size // 1024} KB)")
                return True
            else:
                logger.error("Generated audio file is empty or missing")
                return False

        except Exception as e:
            logger.error(f"TTS generation failed: {e}", exc_info=True)
            return False

    def generate_audio(self, text: str, output_path: Path,
                      voice_config: dict) -> bool:
        """
        Generate TTS audio (synchronous wrapper).

        Args:
            text: Text to synthesize
            output_path: Path to save audio file
            voice_config: Voice configuration dict

        Returns:
            True if successful, False otherwise
        """
        # Run async function
        return asyncio.run(self.generate_audio_async(text, output_path, voice_config))

    def get_audio_duration(self, audio_path: Path) -> Optional[float]:
        """
        Get duration of audio file in seconds using ffprobe.

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

        except subprocess.CalledProcessError as e:
            logger.error(f"ffprobe failed: {e}")
            return None
        except (ValueError, FileNotFoundError) as e:
            logger.error(f"Error getting audio duration: {e}")
            return None

    def adjust_speed_for_duration(self, text: str, target_duration: float,
                                  voice_config: dict, tolerance: float = 2.0) -> dict:
        """
        Adjust voice speed to match target duration.

        This is a simplified approach - for production, you'd generate
        test audio and iteratively adjust.

        Args:
            text: Text to synthesize
            target_duration: Target duration in seconds
            voice_config: Base voice configuration
            tolerance: Acceptable duration difference in seconds

        Returns:
            Adjusted voice configuration
        """
        # Estimate speech rate (rough approximation)
        # Average Russian speech: ~4-5 characters per second
        estimated_duration = len(text) / 4.5

        if abs(estimated_duration - target_duration) <= tolerance:
            # Already close enough
            return voice_config

        # Calculate speed adjustment
        speed_multiplier = estimated_duration / target_duration

        # Convert to percentage (Edge TTS format)
        # +50% means 1.5x speed, -50% means 0.5x speed
        if speed_multiplier > 1:
            # Need to speed up
            rate_adjustment = int((speed_multiplier - 1) * 100)
            rate_adjustment = min(rate_adjustment, 100)  # Max +100%
            new_rate = f"+{rate_adjustment}%"
        else:
            # Need to slow down
            rate_adjustment = int((1 - speed_multiplier) * 100)
            rate_adjustment = min(rate_adjustment, 50)  # Max -50%
            new_rate = f"-{rate_adjustment}%"

        adjusted_config = voice_config.copy()
        adjusted_config['rate'] = new_rate

        logger.info(f"Adjusted speech rate to {new_rate} "
                   f"(estimated: {estimated_duration:.1f}s, target: {target_duration}s)")

        return adjusted_config


def generate_tts_audio(text: str, output_path: Path, voice_tone: str,
                      target_duration: Optional[float] = None) -> bool:
    """
    Convenience function to generate TTS audio.

    Args:
        text: Text to synthesize (Russian)
        output_path: Path to save audio file
        voice_tone: Voice tone name (e.g., 'warm_grandfather')
        target_duration: Optional target duration in seconds

    Returns:
        True if successful, False otherwise
    """
    try:
        generator = TTSGenerator()

        # Get voice configuration
        voice_config = generator.get_voice_config(voice_tone)

        # Adjust speed if target duration specified
        if target_duration:
            voice_config = generator.adjust_speed_for_duration(
                text, target_duration, voice_config
            )

        # Generate audio
        logger.info(f"Generating TTS with voice: {voice_config['voice']}")
        success = generator.generate_audio(text, output_path, voice_config)

        if not success:
            return False

        # Validate duration
        if target_duration:
            actual_duration = generator.get_audio_duration(output_path)
            if actual_duration:
                diff = abs(actual_duration - target_duration)
                if diff > 3.0:  # More than 3 seconds off
                    logger.warning(f"Duration mismatch: {actual_duration:.1f}s vs "
                                 f"target {target_duration}s (diff: {diff:.1f}s)")
                else:
                    logger.info(f"Duration: {actual_duration:.1f}s "
                              f"(target: {target_duration}s, diff: {diff:.1f}s)")

        return True

    except Exception as e:
        logger.error(f"TTS generation failed: {e}", exc_info=True)
        return False


async def list_available_voices():
    """List all available Edge TTS voices."""
    voices = await edge_tts.list_voices()

    print("Available Russian voices:")
    print("-" * 60)

    for voice in voices:
        if voice['Locale'].startswith('ru-'):
            print(f"Name: {voice['ShortName']}")
            print(f"  Gender: {voice['Gender']}")
            print(f"  Locale: {voice['Locale']}")
            print()


def main():
    """Test the TTS generator."""
    import sys

    logging.basicConfig(level=logging.INFO)

    if len(sys.argv) < 2:
        print("Usage:")
        print("  python generate_voice.py <text>")
        print("  python generate_voice.py --list-voices")
        sys.exit(1)

    if sys.argv[1] == '--list-voices':
        asyncio.run(list_available_voices())
        sys.exit(0)

    text = ' '.join(sys.argv[1:])
    output_path = Path(__file__).parent.parent / 'output' / 'audio' / 'test.mp3'

    success = generate_tts_audio(
        text=text,
        output_path=output_path,
        voice_tone='warm_grandfather',
        target_duration=10
    )

    if success:
        print(f"\n✓ Audio saved to: {output_path}")
    else:
        print("\n✗ Audio generation failed")

    sys.exit(0 if success else 1)


if __name__ == '__main__':
    main()
