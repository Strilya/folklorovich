#!/usr/bin/env python3
import logging
from pathlib import Path

logger = logging.getLogger('Subtitles')


def format_time(seconds: float) -> str:
    h = int(seconds // 3600)
    m = int((seconds % 3600) // 60)
    s = int(seconds % 60)
    ms = int((seconds % 1) * 1000)
    return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"


def generate_dual_subtitles(russian_text: str, english_text: str, audio_duration: float, output_dir: str, video_id: str):
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Split into SHORT chunks - 3-4 WORDS MAX per subtitle
    def chunk_text(text):
        words = text.split()
        return [" ".join(words[i:i+4]) for i in range(0, len(words), 4)]
    
    ru_chunks = chunk_text(russian_text)
    en_chunks = chunk_text(english_text)
    
    max_chunks = max(len(ru_chunks), len(en_chunks))
    chunk_duration = audio_duration / max_chunks
    
    # Russian SRT
    ru_srt = output_dir / f"{video_id}_russian.srt"
    with open(ru_srt, 'w', encoding='utf-8') as f:
        for i, chunk in enumerate(ru_chunks):
            start = i * chunk_duration
            end = (i + 1) * chunk_duration
            f.write(f"{i+1}\n{format_time(start)} --> {format_time(end)}\n{chunk}\n\n")
    
    # English SRT
    en_srt = output_dir / f"{video_id}_english.srt"
    with open(en_srt, 'w', encoding='utf-8') as f:
        for i, chunk in enumerate(en_chunks):
            start = i * chunk_duration
            end = (i + 1) * chunk_duration
            f.write(f"{i+1}\n{format_time(start)} --> {format_time(end)}\n{chunk}\n\n")
    
    logger.info(f"✅ Subtitles: {len(ru_chunks)} RU, {len(en_chunks)} EN chunks")
    return (ru_srt, en_srt)
