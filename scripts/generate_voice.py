#!/usr/bin/env python3
"""
Folklorovich - TTS Voice Generator
Generates Russian narration audio using Google Cloud TTS (premium quality)
with Edge TTS as fallback (free, unlimited).

Features:
- Google Cloud TTS Wavenet voices (premium Russian quality)
- Edge TTS fallback (free, unlimited)
- Multiple Russian voice profiles
- Natural speech rate
- High-quality audio output (MP3)
- Duration validation

Author: Folklorovich Project
Date: 2025-12-06
"""

import os
import asyncio
import logging
from pathlib import Path
from typing import Optional
import subprocess

# Try to import Google Cloud TTS (preferred)
try:
    from google.cloud import texttospeech
    GOOGLE_TTS_AVAILABLE = True
except ImportError:
    GOOGLE_TTS_AVAILABLE = False
    logging.warning("google-cloud-texttospeech not installed. Using Edge TTS fallback.")

# Import Edge TTS as fallback
try:
    import edge_tts
    EDGE_TTS_AVAILABLE = True
except ImportError:
    EDGE_TTS_AVAILABLE = False
    logging.error("edge-tts not installed. Run: pip install edge-tts")

# Configure logging
logger = logging.getLogger('VoiceGenerator')

# Google Cloud TTS Voice profiles (premium quality)
GOOGLE_VOICE_PROFILES = {
    'mysterious': 'ru-RU-Wavenet-B',      # Male, deep
    'warm': 'ru-RU-Wavenet-E',            # Female, warm
    'cautionary': 'ru-RU-Wavenet-D',      # Male, serious
    'ominous': 'ru-RU-Wavenet-B',         # Male, dark
    'wise_elder': 'ru-RU-Wavenet-A',      # Male, older
    'neutral': 'ru-RU-Wavenet-C',         # Female, neutral
    'fearful_grave': 'ru-RU-Wavenet-B',   # Male, deep (for grave warnings)
    'hopeful_bright': 'ru-RU-Wavenet-E',  # Female, warm (for positive superstitions)
}

# Edge TTS Voice profiles (fallback)
EDGE_VOICE_PROFILES = {
    'warm_grandfather': {
        'voice': 'ru-RU-DmitryNeural',
        'rate': '+0%',
        'pitch': '-5Hz',
        'description': 'Warm, friendly storytelling voice'
    },
    'mysterious_elder': {
        'voice': 'ru-RU-SvetlanaNeural',
        'rate': '+0%',
        'pitch': '-10Hz',
        'description': 'Slow, enigmatic female voice'
    },
    'energetic_youth': {
        'voice': 'ru-RU-DariyaNeural',
        'rate': '+0%',
        'pitch': '+5Hz',
        'description': 'Upbeat, modern female voice'
    },
    'solemn_narrator': {
        'voice': 'ru-RU-DmitryNeural',
        'rate': '+0%',
        'pitch': '-15Hz',
        'description': 'Formal, serious male voice'
    },
    # Map folklore voice tones to Edge TTS
    'mysterious': {
        'voice': 'ru-RU-DmitryNeural',
        'rate': '+0%',
        'pitch': '-10Hz',
        'description': 'Mysterious male voice'
    },
    'warm': {
        'voice': 'ru-RU-SvetlanaNeural',
        'rate': '+0%',
        'pitch': '+0Hz',
        'description': 'Warm female voice'
    },
    'cautionary': {
        'voice': 'ru-RU-DmitryNeural',
        'rate': '+0%',
        'pitch': '-5Hz',
        'description': 'Cautionary male voice'
    },
    'ominous': {
        'voice': 'ru-RU-DmitryNeural',
        'rate': '+0%',
        'pitch': '-15Hz',
        'description': 'Ominous deep voice'
    },
    'wise_elder': {
        'voice': 'ru-RU-DmitryNeural',
        'rate': '+0%',
        'pitch': '-5Hz',
        'description': 'Wise elder voice'
    },
    'neutral': {
        'voice': 'ru-RU-SvetlanaNeural',
        'rate': '+0%',
        'pitch': '+0Hz',
        'description': 'Neutral female voice'
    },
    'fearful_grave': {
        'voice': 'ru-RU-DmitryNeural',
        'rate': '+0%',
        'pitch': '-15Hz',
        'description': 'Fearful grave warning voice'
    },
    'hopeful_bright': {
        'voice': 'ru-RU-SvetlanaNeural',
        'rate': '+0%',
        'pitch': '+5Hz',
        'description': 'Hopeful bright voice'
    }
}

DEFAULT_VOICE_PROFILE = 'warm_grandfather'


def generate_voice_google(text: str, output_path: str, voice_tone: str = "neutral") -> dict:
    """
    Generate Russian TTS using Google Cloud (better quality than Edge TTS)

    Args:
        text: Russian text to synthesize
        output_path: Path to save MP3 file
        voice_tone: Voice tone (mysterious, warm, cautionary, etc.)

    Returns:
        Dict with path, duration, and voice name
    """
    if not GOOGLE_TTS_AVAILABLE:
        raise ImportError("Google Cloud TTS not available. Install: pip install google-cloud-texttospeech")

    # Check for API key
    api_key = os.getenv("GOOGLE_CLOUD_API_KEY")
    if not api_key:
        raise ValueError("GOOGLE_CLOUD_API_KEY environment variable not set")

    # Initialize client with API key
    client = texttospeech.TextToSpeechClient(
        client_options={"api_key": api_key}
    )

    # Get voice name for this tone
    voice_name = GOOGLE_VOICE_PROFILES.get(voice_tone, "ru-RU-Wavenet-C")

    # Configure voice
    voice = texttospeech.VoiceSelectionParams(
        language_code="ru-RU",
        name=voice_name
    )

    # Configure audio (natural rate, no manipulation)
    audio_config = texttospeech.AudioConfig(
        audio_encoding=texttospeech.AudioEncoding.MP3,
        speaking_rate=1.0,  # Natural pace
        pitch=0.0
    )

    # Synthesis input
    synthesis_input = texttospeech.SynthesisInput(text=text)

    # Generate speech
    logger.info(f"Generating Google Cloud TTS with voice: {voice_name}")
    response = client.synthesize_speech(
        input=synthesis_input,
        voice=voice,
        audio_config=audio_config
    )

    # Ensure output directory exists
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)

    # Save audio file
    with open(output_path, "wb") as out:
        out.write(response.audio_content)

    logger.info(f"✓ Generated audio: {Path(output_path).name} "
                f"({Path(output_path).stat().st_size // 1024} KB)")

    # Calculate actual duration (use ffprobe)
    duration = get_audio_duration_ffprobe(output_path)

    return {
        "path": output_path,
        "duration": duration,
        "voice": voice_name
    }


def get_audio_duration_ffprobe(audio_path: str) -> float:
    """Get audio file duration using ffprobe"""
    cmd = [
        "ffprobe", "-v", "error",
        "-show_entries", "format=duration",
        "-of", "default=noprint_wrappers=1:nokey=1",
        audio_path
    ]
    result = subprocess.run(cmd, capture_output=True, text=True, check=True)
    duration = float(result.stdout.strip())
    return duration


class TTSGenerator:
    """Generates TTS audio using Microsoft Edge TTS (fallback)."""

    def __init__(self):
        """Initialize TTS generator."""
        self.voice_profiles = EDGE_VOICE_PROFILES
        logger.info("TTS generator initialized (Edge TTS fallback)")

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
        DISABLED: Previously adjusted voice speed to match target duration.
        Now returns natural speech rate to avoid chipmunk voice.

        Args:
            text: Text to synthesize
            target_duration: Target duration in seconds (IGNORED)
            voice_config: Base voice configuration
            tolerance: Acceptable duration difference in seconds (IGNORED)

        Returns:
            Voice configuration with natural (+0%) speech rate
        """
        # Use natural speech rate - no manipulation
        adjusted_config = voice_config.copy()
        adjusted_config['rate'] = '+0%'

        logger.info(f"Using natural speech rate (+0%) - no speed manipulation")

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
