# Folklorovich Troubleshooting Guide

**Last Updated:** December 5, 2025

This guide covers common issues and their solutions for the Folklorovich automated content generation system.

---

## Table of Contents

1. [Installation Issues](#installation-issues)
2. [API and Authentication](#api-and-authentication)
3. [Image Generation](#image-generation)
4. [Audio Generation](#audio-generation)
5. [Video Rendering](#video-rendering)
6. [File System and Permissions](#file-system-and-permissions)
7. [GitHub Actions](#github-actions)
8. [Performance Issues](#performance-issues)
9. [Logging and Debugging](#logging-and-debugging)

---

## Installation Issues

### Python Dependencies Won't Install

**Problem:** `pip install -r requirements.txt` fails

**Solutions:**
```bash
# 1. Upgrade pip first
python3 -m pip install --upgrade pip

# 2. Install dependencies one by one to identify culprit
pip install requests
pip install Pillow
pip install edge-tts
pip install python-dotenv

# 3. Check Python version (3.9+ required)
python3 --version

# 4. Use virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### FFmpeg Not Found

**Problem:** `ffmpeg: command not found`

**Solutions:**

**macOS:**
```bash
brew install ffmpeg
ffmpeg -version  # Verify installation
```

**Ubuntu/Debian:**
```bash
sudo apt-get update
sudo apt-get install -y ffmpeg
ffmpeg -version
```

**Windows:**
1. Download from https://ffmpeg.org/download.html
2. Add to PATH environment variable
3. Restart terminal

**Verification:**
```bash
ffmpeg -version
ffprobe -version
```

### ImportError: No module named 'PIL'

**Problem:** Pillow not properly installed

**Solution:**
```bash
pip uninstall Pillow
pip install Pillow --upgrade

# If still fails, install image libraries:
# macOS:
brew install libjpeg libpng

# Ubuntu:
sudo apt-get install libjpeg-dev libpng-dev
```

---

## API and Authentication

### Unsplash API: 401 Unauthorized

**Problem:** Image fetching fails with authentication error

**Solutions:**

1. **Check .env file:**
```bash
# Verify .env exists
ls -la ~/Desktop/folklorovich/.env

# Check contents (don't share your actual key!)
cat .env
```

2. **Correct .env format:**
```bash
# .env file should look like this:
UNSPLASH_ACCESS_KEY=your_actual_key_here

# NOT like this (common mistakes):
UNSPLASH_ACCESS_KEY="your_key"  # ❌ Remove quotes
UNSPLASH_ACCESS_KEY = your_key  # ❌ Remove spaces around =
```

3. **Get new API key:**
   - Go to https://unsplash.com/developers
   - Create new application
   - Copy "Access Key" (not Secret Key)
   - Paste into `.env`

4. **Test API key:**
```python
python3 -c "
import os
from dotenv import load_dotenv
load_dotenv('.env')
print('API Key:', os.getenv('UNSPLASH_ACCESS_KEY')[:10] + '...')
"
```

### Unsplash API: 429 Rate Limit

**Problem:** Too many requests in one hour

**Symptoms:**
```
WARNING: Rate limit hit. Retry after 3600s
ERROR: Failed to fetch images after 3 retries
```

**Solutions:**

1. **Check current usage:**
```bash
cat logs/api_usage.json
```

2. **Wait for reset (50 requests/hour on free tier)**

3. **Reduce image count temporarily:**
Edit `scripts/generate_daily_content_v2.py`:
```python
# Change from 6 to 4 images
images = fetch_images_for_folklore(..., count=4)
```

4. **Upgrade to Unsplash Plus:**
   - 5,000 requests/hour
   - https://unsplash.com/pricing

### Edge TTS Connection Error

**Problem:** Cannot connect to TTS service

**Solutions:**

1. **Check internet connection:**
```bash
ping microsoft.com
```

2. **Test Edge TTS directly:**
```bash
edge-tts --list-voices | grep ru-RU
```

3. **Try alternate voice:**
```python
# In generate_voice.py, change voice:
'voice': 'ru-RU-DmitryNeural'  # Try different voice
```

4. **Update edge-tts:**
```bash
pip install --upgrade edge-tts
```

---

## Image Generation

### No Images Downloaded

**Problem:** `fetch_images.py` finds 0 results

**Diagnosis:**
```bash
# Check logs
tail -n 50 logs/daily_generator.log

# Test Unsplash manually
python3 scripts/fetch_images.py "russian folklore"
```

**Solutions:**

1. **Verify visual tags are reasonable:**
```python
# Check folklore entry visual_tags
python3 -c "
import json
with open('content/folklore_database.json') as f:
    data = json.load(f)
    print(data['folklore'][0]['visual_tags'])
"
```

2. **Use fallback keywords (automatic in v2):**
   - Script should automatically use fallback
   - Check logs for "trying fallback keywords"

3. **Manual override:**
```python
# Edit specific folklore entry
# Change visual_tags to more generic terms
"visual_tags": ["russian culture", "traditional art", "folk scene"]
```

### Downloaded Images Too Small

**Problem:** Images fail validation (< 1080px)

**Solutions:**

1. **Check validation logs:**
```bash
grep "validation failed" logs/daily_generator.log
```

2. **Adjust minimum size in utils.py:**
```python
# Make validation more lenient
validate_image(image_path, min_width=800, min_height=800)
```

3. **Request higher quality from Unsplash:**
Edit `fetch_images.py`:
```python
# Add quality parameter
url = f"{url}&w=4000&q=95&fm=jpg"
```

### Collage Creation Fails

**Problem:** Pillow errors or corrupted output

**Solutions:**

1. **Verify fonts exist:**
```bash
ls -l assets/fonts/
# Should see: Philosopher-Regular.ttf, Roboto-Regular.ttf
```

2. **Download missing fonts:**
```bash
# Philosopher font
wget -P assets/fonts/ https://fonts.google.com/download?family=Philosopher

# Roboto font
wget -P assets/fonts/ https://fonts.google.com/download?family=Roboto
```

3. **Test collage independently:**
```bash
python3 scripts/create_collage.py \
  output/images/001/ \
  output/test_collage.png
```

4. **Check template file:**
```bash
python3 -c "
import json
with open('assets/templates/collage_layouts.json') as f:
    templates = json.load(f)
    print(f'Templates: {len(templates[\"templates\"])}')
"
```

---

## Audio Generation

### TTS Generation Extremely Slow

**Problem:** Audio takes >30 seconds to generate

**Solutions:**

1. **Check internet speed:**
```bash
# Test download speed
curl -o /dev/null https://www.microsoft.com/
```

2. **Reduce text length:**
```python
# Check story_full length
python3 -c "
import json
with open('content/folklore_database.json') as f:
    data = json.load(f)
    for entry in data['folklore'][:5]:
        print(f'{entry[\"id\"]}: {len(entry[\"story_full\"])} chars')
"
```

3. **Try faster voice:**
```python
# Edit voice profile in generate_voice.py
'rate': '+20%'  # Speed up by 20%
```

### Audio Duration Wrong

**Problem:** Audio is 15 seconds when expecting 30

**Diagnosis:**
```bash
# Check actual duration
ffprobe -v error -show_entries format=duration \
  -of default=noprint_wrappers=1:nokey=1 \
  output/audio/2025-12-05_001.mp3
```

**Solutions:**

1. **Adjust speed in voice config:**
```python
# In generate_voice.py
'rate': '-10%'  # Slow down by 10%
```

2. **Lengthen story text:**
   - Add 50-100 more characters to `story_full`

3. **Disable duration validation temporarily:**
```python
# In generate_daily_content_v2.py
validate_audio(audio_path, min_duration=10, max_duration=60)
```

---

## Video Rendering

### FFmpeg Encoding Fails

**Problem:** Video rendering returns error

**Common Errors:**

**1. Codec not found:**
```
Error: Unknown encoder 'libx264'
```

**Solution:**
```bash
# Reinstall FFmpeg with libx264
brew reinstall ffmpeg

# Or compile with x264
brew install ffmpeg --with-libx264
```

**2. Invalid pixel format:**
```
Error: Incompatible pixel format
```

**Solution:**
Edit `render_video.py`:
```python
'-pix_fmt', 'yuv420p'  # Ensure this line exists
```

**3. Audio/video sync issues:**
```
Error: Stream duration mismatch
```

**Solution:**
```bash
# Verify audio file is not corrupted
ffprobe output/audio/2025-12-05_001.mp3

# Regenerate audio if needed
rm output/audio/2025-12-05_001.mp3
python3 scripts/generate_voice.py "Test text"
```

### Video File Size Too Large

**Problem:** 30-second video is 50+ MB

**Solutions:**

1. **Adjust CRF (quality):**
```python
# In render_video.py, increase CRF (lower quality, smaller size)
'-crf', '28'  # Was 23, now 28 (23=high quality, 28=good quality)
```

2. **Reduce bitrate:**
```python
# Add video bitrate limit
'-b:v', '2M'  # 2 Mbps max
```

3. **Compress audio:**
```python
'-b:a', '128k'  # Reduce from 192k to 128k
```

**Expected sizes:**
- Good quality: 5-10 MB per 30s
- High quality: 10-20 MB per 30s
- Excellent quality: 20-30 MB per 30s

### Video Won't Play on Instagram

**Problem:** Upload fails or video unrecognized

**Solutions:**

1. **Verify format:**
```bash
ffprobe output/videos/2025-12-05_Domovoi.mp4
# Should show:
# - 1080x1920 resolution
# - H.264 codec
# - AAC audio
# - 20-60 seconds duration
```

2. **Re-encode for Instagram:**
```bash
ffmpeg -i input.mp4 \
  -vf "scale=1080:1920:force_original_aspect_ratio=decrease,pad=1080:1920:(ow-iw)/2:(oh-ih)/2" \
  -c:v libx264 -preset slow -crf 23 \
  -c:a aac -b:a 192k \
  -pix_fmt yuv420p \
  -movflags +faststart \
  output_instagram.mp4
```

---

## File System and Permissions

### Permission Denied Errors

**Problem:** Cannot write to output directories

**Solutions:**

```bash
# Fix permissions
chmod -R 755 ~/Desktop/folklorovich/output
chmod -R 755 ~/Desktop/folklorovich/logs

# Or change ownership
sudo chown -R $USER:$USER ~/Desktop/folklorovich
```

### Disk Space Full

**Problem:** No space left on device

**Diagnosis:**
```bash
# Check usage
du -sh ~/Desktop/folklorovich/output/*

# Check available space
df -h ~/Desktop
```

**Solutions:**

1. **Clean old files:**
```bash
# Remove files older than 7 days
find output/images -type f -mtime +7 -delete
find output/audio -type f -mtime +7 -delete
find output/videos -type f -mtime +30 -delete  # Keep videos longer
```

2. **Compress old videos:**
```bash
# Compress videos older than 30 days
find output/videos -name "*.mp4" -mtime +30 -exec \
  ffmpeg -i {} -vcodec libx265 -crf 28 {}.compressed.mp4 \;
```

3. **Move to external storage:**
```bash
# Create archive
tar -czf folklorovich_archive_$(date +%Y%m%d).tar.gz output/

# Move to external drive
mv folklorovich_archive_*.tar.gz /Volumes/ExternalDrive/
```

---

## GitHub Actions

### Workflow Doesn't Run

**Problem:** Scheduled workflow not executing

**Solutions:**

1. **Check schedule syntax:**
```yaml
# Must use UTC time
schedule:
  - cron: '0 13 * * *'  # 1 PM UTC = 8 AM EST
```

2. **Verify secrets configured:**
   - Go to repo Settings → Secrets and variables → Actions
   - Add `UNSPLASH_ACCESS_KEY`

3. **Check workflow file location:**
```bash
# Must be exactly:
.github/workflows/daily_generation.yml
```

4. **Enable Actions:**
   - Settings → Actions → General
   - Allow all actions

5. **Manual trigger test:**
   - Actions tab → Daily Generation → Run workflow

### Workflow Fails on FFmpeg

**Problem:** FFmpeg not found in Ubuntu runner

**Solution:**
Workflow should include:
```yaml
- name: Install FFmpeg
  run: |
    sudo apt-get update
    sudo apt-get install -y ffmpeg
```

Already in workflow, but if failing:
```yaml
# Add explicit path
- name: Test FFmpeg
  run: |
    which ffmpeg
    ffmpeg -version
```

### Secrets Not Available

**Problem:** UNSPLASH_ACCESS_KEY is empty

**Solutions:**

1. **Add secret to repository:**
   - Settings → Secrets → New repository secret
   - Name: `UNSPLASH_ACCESS_KEY`
   - Value: Your Unsplash key

2. **Reference correctly in workflow:**
```yaml
env:
  UNSPLASH_ACCESS_KEY: ${{ secrets.UNSPLASH_ACCESS_KEY }}
```

3. **Debug (don't expose key!):**
```yaml
- name: Check env
  run: |
    echo "Key length: ${#UNSPLASH_ACCESS_KEY}"
    # Don't echo the actual key!
```

---

## Performance Issues

### Generation Takes > 5 Minutes

**Problem:** Each video takes very long

**Diagnosis:**
```bash
# Check what's slow
grep "Step [1-4]" logs/daily_generator.log | tail -n 4
```

**Solutions by Step:**

**Step 1 (Images) slow:**
- Reduce image count from 6 to 4
- Use caching (should auto-cache)
- Check internet speed

**Step 2 (Collage) slow:**
- Reduce image resolution
- Use simpler templates
- Check CPU usage

**Step 3 (Audio) slow:**
- Reduce text length
- Check Edge TTS service status
- Try different voice

**Step 4 (Video) slow:**
- Use faster FFmpeg preset: `'-preset', 'faster'`
- Reduce CRF quality
- Check disk I/O

### High Memory Usage

**Problem:** Process uses > 2GB RAM

**Solutions:**

```python
# Process images one at a time instead of all at once
# In create_collage.py:
for idx, image_path in enumerate(image_paths):
    img = Image.open(image_path)
    # ... process ...
    img.close()  # Explicitly close
```

---

## Logging and Debugging

### Enable Verbose Logging

```bash
# Set in .env
LOG_LEVEL=DEBUG

# Run with debug
python3 scripts/generate_daily_content_v2.py
```

### View Recent Logs

```bash
# Last 100 lines
tail -n 100 logs/daily_generator.log

# Follow in real-time
tail -f logs/daily_generator.log

# Errors only
grep ERROR logs/daily_generator.log

# Today's logs
grep "$(date +%Y-%m-%d)" logs/daily_generator.log
```

### Clean All Logs

```bash
# Remove old logs
rm -f logs/*.log
rm -f logs/*.log.*

# Keep last 7 days only
find logs -name "*.log" -mtime +7 -delete
```

---

## Emergency Recovery

### Complete Reset

If everything is broken:

```bash
cd ~/Desktop/folklorovich

# 1. Backup current state
cp content/metadata.json content/metadata.json.backup

# 2. Clear all output
rm -rf output/images/*
rm -rf output/audio/*
rm -rf output/videos/*

# 3. Clear logs
rm -rf logs/*

# 4. Reset metadata
# Edit content/metadata.json - set used_ids_this_cycle to []

# 5. Reinstall dependencies
pip install -r requirements.txt --force-reinstall

# 6. Test
python3 scripts/test_pipeline.py
```

---

## Getting Help

1. **Check logs first:**
   ```bash
   tail -n 200 logs/daily_generator.log
   ```

2. **Run test suite:**
   ```bash
   python3 scripts/test_pipeline.py
   ```

3. **Verify configuration:**
   ```bash
   python3 -c "import json; print(json.load(open('content/metadata.json'))['project_info'])"
   ```

4. **Create issue with:**
   - Error message
   - Relevant log excerpts
   - Steps to reproduce
   - System info (OS, Python version)

---

**Last Updated:** 2025-12-05
**Version:** 1.0
**Maintainer:** Folklorovich Project
