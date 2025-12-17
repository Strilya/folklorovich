#!/usr/bin/env python3
import os
import logging
from pathlib import Path
from google.cloud import texttospeech

logger = logging.getLogger('Voice')

# DEEPEST STORYTELLING VOICES with slower pace for drama
VOICES = {
    'mysterious': 'en-US-Studio-Q',      # Deep narrator
    'warm': 'en-US-Studio-M',            # Warm deep male
    'cautionary': 'en-US-Studio-Q',      # Deep authoritative
    'ominous': 'en-US-Studio-Q',         # Deep dramatic
    'informative': 'en-US-Studio-M',     # Deep professional
    'neutral': 'en-US-Studio-M'          # Deep balanced
}


def generate_voice_google(text: str, output_path: str, voice_tone: str = "neutral") -> dict:
    try:
        client = texttospeech.TextToSpeechClient()
        voice_name = VOICES.get(voice_tone, 'en-US-Studio-M')
        
        response = client.synthesize_speech(
            input=texttospeech.SynthesisInput(text=text),
            voice=texttospeech.VoiceSelectionParams(
                language_code="en-US",
                name=voice_name
            ),
            audio_config=texttospeech.AudioConfig(
                audio_encoding=texttospeech.AudioEncoding.MP3,
                speaking_rate=0.92,  # SLOWER for dramatic storytelling
                pitch=-2.0           # DEEPER pitch
            )
        )
        
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_path, 'wb') as f:
            f.write(response.audio_content)
        
        # Get duration
        import subprocess
        cmd = ["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "default=noprint_wrappers=1:nokey=1", str(output_path)]
        result = subprocess.run(cmd, capture_output=True, text=True)
        duration = float(result.stdout.strip()) if result.returncode == 0 else 0.0
        
        logger.info(f"✅ Voice: {duration:.1f}s ({voice_name})")
        return {"path": str(output_path), "duration": duration, "voice": voice_name}
        
    except Exception as e:
        logger.error(f"TTS failed: {e}")
        raise
