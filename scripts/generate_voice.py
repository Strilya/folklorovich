#!/usr/bin/env python3
"""
Folklorovich - Voice Generator
RUSSIAN NARRATION with Edge TTS
"""

import os
import asyncio
import logging
import subprocess
from pathlib import Path

try:
    import edge_tts
    EDGE_TTS_AVAILABLE = True
except ImportError:
    EDGE_TTS_AVAILABLE = False

logger = logging.getLogger('VoiceGenerator')

# ENGLISH VOICES (Edge TTS)
VOICE_PROFILES = {
    'mysterious': {'voice': 'en-US-ChristopherNeural', 'rate': '+0%', 'pitch': '-10Hz'},
    'warm': {'voice': 'en-US-JennyNeural', 'rate': '+0%', 'pitch': '+0Hz'},
    'cautionary': {'voice': 'en-US-GuyNeural', 'rate': '+0%', 'pitch': '-5Hz'},
    'ominous': {'voice': 'en-GB-RyanNeural', 'rate': '+0%', 'pitch': '-15Hz'},
    'wise_elder': {'voice': 'en-US-ChristopherNeural', 'rate': '+0%', 'pitch': '-5Hz'},
    'neutral': {'voice': 'en-US-JennyNeural', 'rate': '+0%', 'pitch': '+0Hz'},
    'fearful_grave': {'voice': 'en-GB-RyanNeural', 'rate': '+0%', 'pitch': '-15Hz'},
    'hopeful_bright': {'voice': 'en-US-AriaNeural', 'rate': '+0%', 'pitch': '+5Hz'}
}


def generate_voice_google(text: str, output_path: str, voice_tone: str = "neutral") -> dict:
    """
    FALLBACK: Use Edge TTS with English voices
    (Google Cloud TTS not required)
    """
    logger.warning("Google Cloud TTS not available, using Edge TTS fallback")
    
    # Use Edge TTS instead
    voice_config = VOICE_PROFILES.get(voice_tone, VOICE_PROFILES['neutral'])
    
    async def generate():
        communicate = edge_tts.Communicate(
            text=text,
            voice=voice_config['voice'],
            rate=voice_config['rate'],
            pitch=voice_config['pitch']
        )
        await communicate.save(output_path)
    
    asyncio.run(generate())
    
    duration = get_audio_duration_ffprobe(output_path)
    
    return {
        "path": output_path,
        "duration": duration,
        "voice": voice_config['voice']
    }


def get_audio_duration_ffprobe(audio_path: str) -> float:
    cmd = ["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "default=noprint_wrappers=1:nokey=1", audio_path]
    result = subprocess.run(cmd, capture_output=True, text=True, check=True)
    return float(result.stdout.strip())


def generate_tts_audio(text: str, output_path: Path, voice_tone: str, target_duration=None) -> bool:
    """Generate RUSSIAN TTS audio"""
    try:
        voice_config = VOICE_PROFILES.get(voice_tone, VOICE_PROFILES['neutral'])
        
        logger.info(f"Generating RUSSIAN TTS: {voice_config['voice']}")
        
        async def generate():
            communicate = edge_tts.Communicate(
                text=text,
                voice=voice_config['voice'],
                rate=voice_config['rate'],
                pitch=voice_config['pitch']
            )
            Path(output_path).parent.mkdir(parents=True, exist_ok=True)
            await communicate.save(str(output_path))
        
        asyncio.run(generate())
        
        if Path(output_path).exists() and Path(output_path).stat().st_size > 0:
            logger.info(f"✓ Audio generated: {Path(output_path).name}")
            return True
        return False
        
    except Exception as e:
        logger.error(f"TTS failed: {e}")
        return False
