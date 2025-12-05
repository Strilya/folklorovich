# Folklorovich Production Deployment Guide

**Version:** 1.0
**Status:** Production-Ready
**Last Updated:** December 5, 2025

This guide covers deploying and operating Folklorovich in a production environment with daily automated content generation.

---

## Table of Contents

1. [Quick Start](#quick-start)
2. [Production Checklist](#production-checklist)
3. [Daily Operation](#daily-operation)
4. [Monitoring and Maintenance](#monitoring-and-maintenance)
5. [Scaling and Optimization](#scaling-and-optimization)
6. [Backup and Recovery](#backup-and-recovery)
7. [Cost Management](#cost-management)

---

## Quick Start

### First-Time Setup (10 minutes)

```bash
# 1. Clone and navigate
cd ~/Desktop/folklorovich

# 2. Install dependencies
python3 -m pip install -r requirements.txt
brew install ffmpeg  # macOS
# OR: sudo apt-get install ffmpeg  # Linux

# 3. Configure environment
cp .env.template .env
nano .env  # Add your UNSPLASH_ACCESS_KEY

# 4. Run tests
python3 scripts/test_pipeline.py

# 5. Generate first video
python3 scripts/generate_daily_content_v2.py
```

**Expected Output:**
```
✅ SUCCESS! Video generated in 45.3s
📹 Output: output/videos/2025-12-05_Domovoi.mp4
```

---

## Production Checklist

### Before Going Live

- [ ] **Configuration**
  - [ ] `.env` file created with valid `UNSPLASH_ACCESS_KEY`
  - [ ] All 75 folklore entries in database
  - [ ] Metadata structure validated
  - [ ] Templates file present (8 templates)

- [ ] **Dependencies**
  - [ ] Python 3.9+ installed
  - [ ] All pip packages installed (`requirements.txt`)
  - [ ] FFmpeg + FFprobe installed
  - [ ] Edge TTS working

- [ ] **Testing**
  - [ ] Test suite passes 100% (`test_pipeline.py`)
  - [ ] Manual generation successful
  - [ ] Video plays in Instagram app
  - [ ] Rotation cycle works correctly

- [ ] **Automation**
  - [ ] GitHub Actions workflow enabled
  - [ ] Secrets configured in GitHub
  - [ ] Schedule set correctly (8 AM EST = 13:00 UTC)
  - [ ] Notifications configured

- [ ] **Monitoring**
  - [ ] Log directory created and writable
  - [ ] API usage tracking enabled
  - [ ] Storage monitoring configured
  - [ ] Alert thresholds set

---

## Daily Operation

### Automated Daily Generation (Recommended)

**GitHub Actions** handles everything automatically:

1. **Runs at 8 AM EST** every day
2. **Selects** next folklore entry
3. **Generates** complete video
4. **Uploads** artifact to GitHub
5. **Updates** metadata
6. **Cleans up** old files
7. **Notifies** on failure

**To monitor:**
```bash
# View latest workflow run
https://github.com/YOUR_USERNAME/folklorovich/actions

# Check generated videos
https://github.com/YOUR_USERNAME/folklorovich/actions/artifacts
```

### Manual Generation

For testing or generating specific content:

```bash
# Standard production generation
python3 scripts/generate_daily_content_v2.py

# With specific folklore ID (for testing)
# (Requires script modification - edit metadata to force specific entry)

# Dry run (no metadata update)
# Set in script: save_metadata = False
```

### Monitoring Daily Runs

**Check Logs:**
```bash
# Today's generation
tail -n 100 logs/daily_generator_$(date +%Y-%m-%d).log

# Recent errors
grep ERROR logs/daily_generator.log | tail -n 20

# API usage today
python3 -c "
import json
from datetime import datetime
with open('logs/api_usage.json') as f:
    data = json.load(f)
    today = datetime.now().strftime('%Y-%m-%d')
    unsplash = data.get('unsplash', {}).get('requests_by_day', {}).get(today, 0)
    print(f'Unsplash requests today: {unsplash}/50')
"
```

**Check Output:**
```bash
# List today's generated files
ls -lh output/videos/*$(date +%Y-%m-%d)*

# Video details
ffprobe output/videos/$(ls -t output/videos | head -1) 2>&1 | grep -E "Duration|Video|Audio"
```

**Check Metadata:**
```bash
# Current cycle status
python3 -c "
import json
with open('content/metadata.json') as f:
    m = json.load(f)
    rotation = m['content_rotation']
    used = len(rotation['used_ids_this_cycle'])
    print(f'Cycle: {rotation[\"current_cycle\"]}')
    print(f'Used: {used}/75 entries')
    print(f'Last: {rotation[\"last_used_id\"]}')
    print(f'Date: {rotation[\"last_generated_date\"][:10]}')
"
```

---

## Monitoring and Maintenance

### Daily Health Check (2 minutes)

Run this every morning:

```bash
#!/bin/bash
# save as: scripts/health_check.sh

echo "🏥 Folklorovich Health Check"
echo "============================"

# 1. Check last generation
LAST_VIDEO=$(ls -t output/videos/*.mp4 2>/dev/null | head -1)
if [ -z "$LAST_VIDEO" ]; then
    echo "❌ No videos generated yet"
else
    echo "✅ Last video: $(basename $LAST_VIDEO)"
    echo "   Size: $(du -h "$LAST_VIDEO" | cut -f1)"
    echo "   Date: $(stat -f %Sm -t "%Y-%m-%d %H:%M" "$LAST_VIDEO")"
fi

# 2. Check API usage
if [ -f logs/api_usage.json ]; then
    TODAY=$(date +%Y-%m-%d)
    USAGE=$(python3 -c "import json; data=json.load(open('logs/api_usage.json')); print(data.get('unsplash',{}).get('requests_by_day',{}).get('$TODAY',0))")
    echo "📊 Unsplash API: $USAGE/50 requests today"
fi

# 3. Check storage
TOTAL_SIZE=$(du -sh output/ | cut -f1)
echo "💾 Storage: $TOTAL_SIZE"

# 4. Check for errors
ERROR_COUNT=$(grep -c ERROR logs/daily_generator.log 2>/dev/null || echo 0)
echo "🔍 Errors in log: $ERROR_COUNT"

# 5. Check cycle status
CYCLE=$(python3 -c "import json; m=json.load(open('content/metadata.json')); print(len(m['content_rotation']['used_ids_this_cycle']))")
echo "🔄 Cycle progress: $CYCLE/75"

echo ""
if [ $ERROR_COUNT -gt 0 ]; then
    echo "⚠️  Check logs: tail -n 50 logs/daily_generator.log"
else
    echo "✅ System healthy"
fi
```

Make executable:
```bash
chmod +x scripts/health_check.sh
./scripts/health_check.sh
```

### Weekly Maintenance (10 minutes)

**Every Sunday:**

```bash
# 1. Review generation statistics
python3 -c "
import json
with open('content/metadata.json') as f:
    m = json.load(f)
    stats = m['generation_history']
    print(f'Total videos: {stats[\"total_videos_generated\"]}')
    print(f'Success rate: {stats[\"successful_generations\"]}/{stats[\"total_videos_generated\"]}')
    print(f'Avg time: {m[\"statistics\"][\"average_generation_time_seconds\"]:.1f}s')
"

# 2. Clean old files
find output/images -type f -mtime +7 -delete
find output/audio -type f -mtime +7 -delete
echo "✅ Cleaned old working files"

# 3. Backup metadata
cp content/metadata.json content/metadata_$(date +%Y%m%d).json.backup
echo "✅ Backed up metadata"

# 4. Check API usage trends
python3 -c "
import json
with open('logs/api_usage.json') as f:
    data = json.load(f)
    total = data.get('unsplash', {}).get('total_requests', 0)
    print(f'Total Unsplash requests: {total}')
"

# 5. Verify all 75 entries usable
python3 scripts/test_pipeline.py > logs/weekly_test.log 2>&1
echo "✅ Test suite results in logs/weekly_test.log"
```

### Monthly Review (30 minutes)

1. **Analyze performance:**
   - Average generation time trending
   - Success rate consistency
   - Popular categories/themes

2. **Content review:**
   - Watch 5-10 random videos
   - Check audio quality
   - Verify text readability
   - Assess visual variety

3. **Optimization opportunities:**
   - Identify slow folklore entries
   - Update visual tags if needed
   - Refresh underperforming templates

4. **Cost review:**
   - Total API calls
   - Storage usage
   - GitHub Actions minutes used

---

## Scaling and Optimization

### Performance Tuning

**Current Performance:**
- Generation time: 30-90 seconds per video
- Image fetching: 10-30 seconds
- Collage creation: 5-10 seconds
- Audio generation: 3-8 seconds
- Video rendering: 10-30 seconds

**Optimization Options:**

**1. Parallel Processing** (not yet implemented):
```python
# Generate audio while creating collage
from concurrent.futures import ThreadPoolExecutor

with ThreadPoolExecutor(max_workers=2) as executor:
    collage_future = executor.submit(create_collage, ...)
    audio_future = executor.submit(generate_audio, ...)

    collage = collage_future.result()
    audio = audio_future.result()
```

**2. Image Caching:**
```python
# Already implemented in fetch_images.py
# Reuses images if folklore entry unchanged
# Check cache: ls -lh output/images/*/.image_cache.json
```

**3. FFmpeg Presets:**
```python
# Faster encoding (slightly lower quality)
'-preset', 'faster'  # Instead of 'medium'

# Or even faster
'-preset', 'veryfast'  # Good for testing
```

**4. Reduce Resolution:**
```python
# For draft/preview mode
VIDEO_WIDTH = 540   # Half resolution
VIDEO_HEIGHT = 960  # Renders 4x faster
```

### Generating Multiple Videos

To generate a week's worth of content:

```bash
#!/bin/bash
# scripts/generate_batch.sh

for i in {1..7}; do
    echo "Generating video $i/7..."

    python3 scripts/generate_daily_content_v2.py

    if [ $? -eq 0 ]; then
        echo "✅ Video $i generated successfully"
    else
        echo "❌ Video $i failed"
        break
    fi

    # Wait 60 seconds between generations (API rate limiting)
    if [ $i -lt 7 ]; then
        echo "Waiting 60 seconds..."
        sleep 60
    fi
done

echo "Batch generation complete!"
```

---

## Backup and Recovery

### What to Backup

**Critical (must backup):**
- `content/metadata.json` - Cycle state
- `.env` - API keys (encrypted!)
- `content/folklore_database.json` - All stories

**Optional (can regenerate):**
- `output/videos/*.mp4` - Generated videos
- `logs/` - Historical logs

### Backup Strategy

**Daily (automated in GitHub Actions):**
```yaml
# Commits metadata.json to git daily
git add content/metadata.json
git commit -m "Update metadata"
```

**Weekly (manual):**
```bash
# Create dated backup
tar -czf backups/folklorovich_$(date +%Y%m%d).tar.gz \
    content/ .env assets/

# Keep last 4 weeks
find backups/ -name "*.tar.gz" -mtime +28 -delete
```

**Monthly (archive):**
```bash
# Full project backup
tar -czf archives/folklorovich_$(date +%Y%m).tar.gz \
    content/ scripts/ assets/ output/videos/

# Upload to cloud storage
# aws s3 cp archives/folklorovich_$(date +%Y%m).tar.gz s3://your-bucket/
```

### Recovery Procedures

**Scenario 1: Metadata Corrupted**
```bash
# Restore from git
git checkout content/metadata.json

# Or restore from backup
cp content/metadata_YYYYMMDD.json.backup content/metadata.json
```

**Scenario 2: Lost Track of Cycle**
```bash
# Reset to beginning of current cycle
python3 -c "
import json
with open('content/metadata.json', 'r+') as f:
    m = json.load(f)
    m['content_rotation']['used_ids_this_cycle'] = []
    f.seek(0)
    json.dump(m, f, indent=2)
    f.truncate()
print('✅ Cycle reset')
"
```

**Scenario 3: Complete System Failure**
```bash
# 1. Clone fresh repo
git clone https://github.com/YOUR_USERNAME/folklorovich.git
cd folklorovich

# 2. Restore .env
cp ~/backups/.env .env

# 3. Install dependencies
pip install -r requirements.txt
brew install ffmpeg

# 4. Test
python3 scripts/test_pipeline.py

# 5. Resume generation
python3 scripts/generate_daily_content_v2.py
```

---

## Cost Management

### Free Tier Limits

**Unsplash API:**
- 50 requests/hour
- ~1,200 requests/day (if spread out)
- **Daily usage:** ~10-20 requests (well within limit)

**Edge TTS:**
- Unlimited free usage
- Microsoft service, no API key needed

**GitHub Actions:**
- 2,000 minutes/month free
- **Daily usage:** ~5-10 minutes
- **Monthly usage:** ~150-300 minutes (well within limit)

**Storage:**
- GitHub: 1 GB free
- **Daily video:** ~5-15 MB
- **Monthly videos:** ~150-450 MB (within limit)

### Cost Optimization

**1. Minimize API Calls:**
```python
# Use image caching (already implemented)
# Don't re-fetch if images exist

# Reduce image count if needed
fetch_images_for_folklore(..., count=4)  # Instead of 6
```

**2. Efficient Storage:**
```bash
# Keep only last 30 days of videos
find output/videos -type f -mtime +30 -delete

# Archive older videos to cheaper storage
tar -czf archive_$(date +%Y%m).tar.gz output/videos/*.mp4
mv archive_*.tar.gz /external/storage/
```

**3. Optimize GitHub Actions:**
```yaml
# Already optimized:
- Shallow clone (fetch-depth: 1)
- Pip caching
- Artifact retention limits
- Cleanup old files
- 30-minute timeout
```

### Monitoring Costs

**Weekly Cost Check:**
```bash
# Unsplash usage
python3 -c "
import json
from datetime import datetime, timedelta
with open('logs/api_usage.json') as f:
    data = json.load(f)
    # Last 7 days
    total = 0
    for i in range(7):
        date = (datetime.now() - timedelta(days=i)).strftime('%Y-%m-%d')
        day_usage = data.get('unsplash', {}).get('requests_by_day', {}).get(date, 0)
        total += day_usage
        print(f'{date}: {day_usage} requests')
    print(f'7-day total: {total} requests')
    print(f'Projected monthly: ~{total * 4} requests')
"

# Storage usage
du -sh output/
du -sh output/videos/

# GitHub Actions minutes (check manually in GitHub)
# Settings → Billing → Plans and usage
```

---

## Emergency Procedures

### System Down

**Symptoms:**
- Videos not generating
- GitHub Actions failing
- Multiple errors in logs

**Response:**

1. **Check external services:**
   ```bash
   # Test Unsplash
   curl -I https://api.unsplash.com/

   # Test Edge TTS
   edge-tts --list-voices | head -1
   ```

2. **Review recent logs:**
   ```bash
   tail -n 200 logs/daily_generator.log
   grep ERROR logs/daily_generator.log | tail -n 10
   ```

3. **Run diagnostics:**
   ```bash
   python3 scripts/test_pipeline.py
   ```

4. **Try manual generation:**
   ```bash
   python3 scripts/generate_daily_content_v2.py
   ```

5. **If still failing, restore from backup:**
   ```bash
   git checkout content/metadata.json
   python3 scripts/generate_daily_content_v2.py
   ```

### API Key Compromised

**If your Unsplash API key is leaked:**

1. **Immediately revoke old key:**
   - Go to https://unsplash.com/oauth/applications
   - Regenerate Access Key

2. **Update everywhere:**
   ```bash
   # Local .env
   nano .env  # Replace key

   # GitHub secrets
   # Settings → Secrets → Update UNSPLASH_ACCESS_KEY

   # Any other deployments
   ```

3. **Verify new key works:**
   ```bash
   python3 scripts/test_pipeline.py
   ```

---

## Success Metrics

### Key Performance Indicators

**Reliability:**
- Target: 95% success rate
- Monitor: `metadata.json → generation_history`

**Performance:**
- Target: < 2 minutes per video
- Monitor: `average_generation_time_seconds`

**Quality:**
- Target: No validation failures
- Monitor: Error logs for "validation failed"

**Cost:**
- Target: Stay within free tiers
- Monitor: `logs/api_usage.json`

### Monthly Report Template

```
Folklorovich Monthly Report - [Month Year]
===========================================

Generation Statistics:
- Total videos: [X]
- Success rate: [X%]
- Average time: [X]s
- Failures: [X]

Content Distribution:
- Household spirits: [X]
- Mythical creatures: [X]
- Superstitions: [X]
- Rituals: [X]
- Curses/omens: [X]
- Folk heroes: [X]

API Usage:
- Unsplash requests: [X]/1200
- Storage used: [X] MB

Issues:
- Critical: [X]
- Warnings: [X]
- Resolved: [X]

Next Month Goals:
- [ ] ...
- [ ] ...
```

---

**Document Version:** 1.0
**Last Updated:** 2025-12-05
**Next Review:** 2026-01-05
**Maintainer:** Folklorovich Project Team
