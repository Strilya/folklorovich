"""
Subtitle Generator for Folklorovich
Generates dual language SRT subtitles for superstition reels
"""

from pathlib import Path


def generate_dual_subtitles(
    russian_text: str,
    english_text: str,
    audio_duration: float,
    output_dir: str,
    video_id: str
) -> tuple:
    """
    Generate separate .srt files for Russian and English subtitles

    Args:
        russian_text: Full Russian narration text
        english_text: Full English translation
        audio_duration: Duration of audio in seconds
        output_dir: Directory to save SRT files
        video_id: Unique identifier for the video

    Returns:
        Tuple of (russian_srt_path, english_srt_path)
    """

    # Split text into chunks (2-3 words per subtitle for readability)
    russian_chunks = split_into_subtitle_chunks(russian_text, words_per_chunk=3)
    english_chunks = split_into_subtitle_chunks(english_text, words_per_chunk=3)

    # Ensure chunks align (use max length)
    max_chunks = max(len(russian_chunks), len(english_chunks))

    # Pad shorter list if needed
    while len(russian_chunks) < max_chunks:
        russian_chunks.append("")
    while len(english_chunks) < max_chunks:
        english_chunks.append("")

    # Calculate timing
    time_per_chunk = audio_duration / max_chunks

    # Generate Russian SRT
    russian_srt = generate_srt_file(russian_chunks, time_per_chunk)
    russian_path = Path(output_dir) / f"{video_id}_ru.srt"
    russian_path.parent.mkdir(parents=True, exist_ok=True)
    russian_path.write_text(russian_srt, encoding='utf-8')

    # Generate English SRT
    english_srt = generate_srt_file(english_chunks, time_per_chunk)
    english_path = Path(output_dir) / f"{video_id}_en.srt"
    english_path.write_text(english_srt, encoding='utf-8')

    return (str(russian_path), str(english_path))


def split_into_subtitle_chunks(text: str, words_per_chunk: int = 3) -> list:
    """
    Split text into readable subtitle chunks

    Args:
        text: Full text to split
        words_per_chunk: Number of words per subtitle chunk

    Returns:
        List of text chunks
    """
    words = text.split()
    chunks = []

    for i in range(0, len(words), words_per_chunk):
        chunk = " ".join(words[i:i+words_per_chunk])
        chunks.append(chunk)

    return chunks


def generate_srt_file(chunks: list, time_per_chunk: float) -> str:
    """
    Generate SRT format string from chunks

    Args:
        chunks: List of subtitle text chunks
        time_per_chunk: Duration of each chunk in seconds

    Returns:
        SRT formatted string
    """
    srt_content = []

    for i, chunk in enumerate(chunks):
        if not chunk.strip():  # Skip empty chunks
            continue

        start_time = format_srt_time(i * time_per_chunk)
        end_time = format_srt_time((i + 1) * time_per_chunk)

        srt_content.append(f"{i+1}")
        srt_content.append(f"{start_time} --> {end_time}")
        srt_content.append(chunk)
        srt_content.append("")  # Empty line between entries

    return "\n".join(srt_content)


def format_srt_time(seconds: float) -> str:
    """
    Format time as SRT timestamp (00:00:00,000)

    Args:
        seconds: Time in seconds

    Returns:
        SRT formatted timestamp string
    """
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    millis = int((seconds % 1) * 1000)

    return f"{hours:02d}:{minutes:02d}:{secs:02d},{millis:03d}"


if __name__ == "__main__":
    # Test the subtitle generator
    test_russian = "Это тестовое сообщение для проверки генератора субтитров на русском языке"
    test_english = "This is a test message to verify the subtitle generator in English language"

    output_dir = "../output/subtitles"
    srt_ru, srt_en = generate_dual_subtitles(
        russian_text=test_russian,
        english_text=test_english,
        audio_duration=10.0,
        output_dir=output_dir,
        video_id="test_001"
    )

    print(f"Generated Russian subtitles: {srt_ru}")
    print(f"Generated English subtitles: {srt_en}")
