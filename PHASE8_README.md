# Folklorovich - Phase 8: Dual Reel Types

## Overview

Phase 8 implements **TWO distinct reel types** with **strict alternation** for maximum engagement variety.

### Reel Types

**TYPE A: Visual-Only Reels** (15 seconds)
- Pure Russian beauty, NO narration
- 10 images with **BEAT-SYNCED** transitions
- Fast crossfades (0.3s)
- Cinematic music at 100% volume (LOUD)
- Music beat detection for synchronized image changes
- Only @Folklorovich watermark
- Themes: Golden Ring churches, birch forests, Lake Baikal, northern lights, etc.

**TYPE B: Superstition Reels** (25-32 seconds)
- Educational Russian folklore with narration
- 10-13 images with smooth crossfades (0.5s)
- Russian narration (Google Cloud TTS Wavenet voices)
- Dual subtitles (Russian top, English bottom)
- Russian folk music in background at 15% volume (QUIET)
- NO beat sync (narration-focused)
- @Folklorovich watermark

### Alternation Pattern

```
Run 1: VISUAL → Run 2: SUPERSTITION → Run 3: VISUAL → Run 4: SUPERSTITION
```

**NEVER** generates two of the same type in a row.

---

## Setup Instructions

### 1. Install Dependencies

```bash
pip install -r requirements.txt --break-system-packages
```

Key dependencies:
- `google-cloud-texttospeech` - Premium Russian TTS
- `edge-tts` - Fallback TTS
- FFmpeg (system requirement)

### 2. Set Environment Variables

Add to `.env`:

```bash
# Pixabay API (for images)
PIXABAY_API_KEY=your_pixabay_api_key

# Google Cloud TTS (for Russian narration)
GOOGLE_CLOUD_API_KEY=your_google_cloud_api_key
```

**Get API Keys:**
- Pixabay: https://pixabay.com/api/docs/
- Google Cloud TTS: https://console.cloud.google.com/apis/credentials

### 3. Download Background Music

Music is organized into TWO categories:

**A. Cinematic Music (for Visual Reels)**
1. Download 10-15 cinematic/epic tracks from:
   - [YouTube Audio Library](https://www.youtube.com/audiolibrary) (Cinematic category)
   - [Incompetech](https://incompetech.com/music/royalty-free/) (Cinematic/Dramatic)
   - [Pixabay Music](https://pixabay.com/music/) (Cinematic filter)

2. Place all `.mp3` files in `assets/music/cinematic/`

**B. Russian Folk Music (for Superstition Reels)**
1. Download 10-15 Russian folk/traditional tracks from:
   - [YouTube Audio Library](https://www.youtube.com/audiolibrary) (Folk/Traditional)
   - [Free Music Archive](https://freemusicarchive.org/) (Folk/World Music)
   - Search keywords: "Russian folk", "Balalaika", "Slavic folk"

2. Place all `.mp3` files in `assets/music/russian_folk/`

See `assets/music/cinematic/README.md` and `assets/music/russian_folk/README.md` for detailed instructions.

---

## Usage

### Generate Daily Reel

```bash
python scripts/generate_daily_content.py
```

**First run:** Generates a **VISUAL** reel
**Second run:** Generates a **SUPERSTITION** reel
**Third run:** Generates a **VISUAL** reel
...and so on

### Output Files

Videos are saved to:
```
output/videos/
├── 2025-12-06_V001_visual.mp4        # Visual reel
├── 2025-12-06_004_superstition.mp4   # Superstition reel
└── ...
```

Additional outputs:
```
output/audio/          # Russian TTS narration files
output/subtitles/      # Dual language .srt files
output/images/         # Downloaded images from Pixabay
```

---

## Architecture

### Core Modules

| Module | Purpose |
|--------|---------|
| `generate_daily_content.py` | Master orchestrator with alternation logic |
| `render_video.py` | Slideshow video renderer with beat-synced transitions |
| `generate_voice.py` | Google Cloud TTS + Edge TTS fallback |
| `generate_subtitles.py` | Dual language SRT subtitle generator |
| `fetch_images.py` | Pixabay image downloader |
| `music_manager.py` | Random music track selection (NEW) |
| `beat_detector.py` | Music beat detection for visual reels (NEW) |

### Data Files

| File | Purpose |
|------|---------|
| `content/folklore_database.json` | 15 Russian superstitions (Russian + English) |
| `content/visual_themes.json` | 10 visual-only themes (NEW) |
| `content/metadata.json` | Alternation tracking + stats |

### Metadata Structure

```json
{
  "reel_alternation": {
    "last_reel_type": "visual",          // Tracks last generated type
    "visual_reel_count": 5,              // Total visual reels
    "superstition_reel_count": 4,        // Total superstition reels
    "used_superstition_ids": ["001", "004"],  // Cycle tracking
    "used_visual_theme_ids": ["V001"]    // Cycle tracking
  }
}
```

---

## Video Specifications

### Visual Reels (TYPE A) - with Beat Sync

| Property | Value |
|----------|-------|
| Duration | 15 seconds (fixed) |
| Images | 10 (beat-synced durations) |
| Crossfade | 0.3s (fast) |
| Music | Cinematic, 100% volume (LOUD) |
| Beat Sync | ✅ Image transitions synchronized to music beats |
| Text | Watermark only |
| Format | 1080x1920 (9:16 vertical) |
| Codec | H.264, CRF 23 |

**Beat Detection:**
- Automatically analyzes music track to detect beats
- Image durations adjusted dynamically to match beat timestamps
- Creates rhythmic, engaging visual flow
- Falls back to evenly-spaced timing if beat detection fails

### Superstition Reels (TYPE B) - Narration-Focused

| Property | Value |
|----------|-------|
| Duration | 25-32s (matches narration) |
| Images | 10-13 (2.5s each) |
| Crossfade | 0.5s (smooth) |
| Music | Russian folk, 15% volume (QUIET background) |
| Beat Sync | ❌ No (narration-focused, not music-driven) |
| Narration | Russian (Google Cloud TTS) |
| Subtitles | Dual (Russian top, English bottom) |
| Text | Watermark only |
| Format | 1080x1920 (9:16 vertical) |
| Codec | H.264, CRF 23 |

**Music Role:**
- Quiet atmospheric background only
- Does not compete with narration
- Russian folk/traditional style for cultural immersion
- Evenly-paced image transitions (no beat sync)

---

## Visual Themes

10 themes showcasing Russian cultural and natural beauty:

1. **Golden Ring Churches** - Orthodox architecture with golden domes
2. **Birch Forest Seasons** - White birch trees in various seasons
3. **Russian Winter Beauty** - Snow-covered villages and landscapes
4. **Lake Baikal** - Crystal clear Siberian lake
5. **Russian Cultural Ornaments** - Khokhloma, matryoshka, Gzhel
6. **Northern Lights Russia** - Aurora borealis in Arctic regions
7. **Kamchatka Volcanoes** - Dramatic volcanic landscapes
8. **Russian Wooden Architecture** - Traditional izba log cabins
9. **Autumn in Russia** - Golden fall colors
10. **Russian Rivers and Waterways** - Volga River and others

Each theme has 5 keyword sets for image variety.

---

## Russian Superstitions

15 authentic Russian superstitions with full translations:

| ID | Name | Voice Tone |
|----|------|-----------|
| 001 | Black Cat Crossing | Ominous |
| 002 | Spilled Salt | Cautionary |
| 003 | Whistling Indoors | Cautionary |
| 004 | Broken Mirror | Fearful/Grave |
| 005 | Corner Seating | Cautionary |
| 006 | Empty Vessels | Cautionary |
| 007 | Returning Home | Cautionary |
| 008 | Threshold Handshake | Cautionary |
| 009 | Bird at Window | Ominous |
| 010 | Itchy Left Palm | Warm |
| 011 | Itchy Right Palm | Cautionary |
| 012 | Shoes on Table | Ominous |
| 013 | Gift Knives | Ominous |
| 014 | Meeting Empty Bucket | Ominous |
| 015 | Even Flowers for Graves | Cautionary |

Each has:
- `story_russian` - Russian narration text
- `story_full` - English translation
- `voice_tone` - TTS voice selection
- `visual_tags` - Image search keywords

---

## Google Cloud TTS Voices

Premium Wavenet Russian voices used:

| Voice | Gender | Use Case |
|-------|--------|----------|
| ru-RU-Wavenet-A | Male | Wise elder |
| ru-RU-Wavenet-B | Male | Mysterious, ominous, fearful |
| ru-RU-Wavenet-C | Female | Neutral |
| ru-RU-Wavenet-D | Male | Cautionary, serious |
| ru-RU-Wavenet-E | Female | Warm, hopeful |

Natural speech rate (1.0x), no manipulation.

---

## Troubleshooting

### "No images found"

**Cause:** Pixabay API key missing or invalid
**Fix:** Set `PIXABAY_API_KEY` in `.env`

### "No music files found"

**Cause:** `assets/music/` directory is empty
**Fix:** Download background music (see setup instructions)

### "Google Cloud TTS failed"

**Cause:** API key missing or invalid
**Fix:** Set `GOOGLE_CLOUD_API_KEY` in `.env`
**Fallback:** System automatically uses Edge TTS as fallback

### "FFmpeg not found"

**Cause:** FFmpeg not installed
**Fix:** Install FFmpeg:
```bash
# macOS
brew install ffmpeg

# Ubuntu/Debian
sudo apt install ffmpeg
```

### Subtitles not showing

**Cause:** Subtitle paths with special characters
**Fix:** Already handled with path escaping in render_video.py

---

## Testing

### Test Visual Reel Generation

```bash
# First run should create visual reel
python scripts/generate_daily_content.py
```

Expected output:
- 15-second video
- 10 images with BEAT-SYNCED transitions
- Loud cinematic music
- Image changes synchronized to music beats
- No narration
- Only watermark

### Test Superstition Reel Generation

```bash
# Second run should create superstition reel
python scripts/generate_daily_content.py
```

Expected output:
- 25-32 second video
- Russian narration
- Dual subtitles (Russian + English)
- Quiet Russian folk music in background
- NO beat sync (narration-focused)
- Watermark

### Verify Alternation

```bash
# Run 3 times and check output types
python scripts/generate_daily_content.py  # Should be VISUAL
python scripts/generate_daily_content.py  # Should be SUPERSTITION
python scripts/generate_daily_content.py  # Should be VISUAL
```

Check `content/metadata.json` → `reel_alternation.last_reel_type`

---

## Success Criteria

✅ Two distinct reel types working
✅ STRICT alternation (never A→A or B→B)
✅ Visual reels: 15s, 10 images, BEAT-SYNCED transitions, cinematic music
✅ Superstition reels: 25-32s, narration, dual subtitles, Russian folk music
✅ Beat detection for visual reels (synchronized image transitions)
✅ Random music selection from appropriate folders
✅ Both have @Folklorovich watermark
✅ Google Cloud TTS implemented (better Russian voices)
✅ Slideshow with crossfades (NOT static collage)
✅ Russian cultural images only
✅ Music categorized: cinematic vs Russian folk

---

## Next Steps

### Content Expansion

1. Add more visual themes (expand to 20-30)
2. Add more superstitions (expand to 30-50)
3. Create seasonal themes (winter, spring, summer, fall)

### Technical Enhancements

1. Improve beat detection with librosa (more accurate)
2. Implement auto-posting to Instagram/TikTok
3. Add analytics tracking
4. Implement A/B testing for engagement
5. Add Ken Burns effect (zoom/pan) to images
6. Test different crossfade transitions (wipe, slide, etc.)

### Production

1. Set up cron job for daily generation
2. Implement error alerting
3. Create backup system
4. Set up cloud deployment

---

## Credits

- **TTS:** Google Cloud Text-to-Speech (Wavenet Russian voices)
- **Images:** Pixabay API
- **Music:** YouTube Audio Library, Incompetech (royalty-free)
- **Video Processing:** FFmpeg
- **Framework:** Python 3.11+

---

## License

MIT License - See LICENSE file for details

---

## Support

For issues or questions:
1. Check this README
2. Check `generation.log` for error details
3. Review `content/metadata.json` for state tracking
4. Run with debug logging: `export LOG_LEVEL=DEBUG`

---

**Last Updated:** 2025-12-06
**Phase:** 8 - Dual Reel Types
**Status:** ✅ Production Ready
