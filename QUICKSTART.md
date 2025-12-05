# Folklorovich - Quick Start Guide

## 🚀 Getting Started in 5 Minutes

### Step 1: Install Prerequisites

**Install FFmpeg:**
```bash
# macOS
brew install ffmpeg

# Ubuntu/Debian
sudo apt-get install ffmpeg

# Verify installation
ffmpeg -version
```

### Step 2: Setup Python Environment

```bash
cd ~/Desktop/folklorovich

# Create virtual environment
python3 -m venv venv

# Activate it
source venv/bin/activate  # macOS/Linux
# OR
venv\Scripts\activate  # Windows

# Install dependencies
pip install --upgrade pip
pip install -r requirements.txt
```

### Step 3: Configure API Keys

```bash
# Copy template
cp .env.template .env

# Edit .env and add your Unsplash API key
nano .env  # or use any text editor
```

Get your free Unsplash API key:
1. Go to https://unsplash.com/developers
2. Create an account (free)
3. Create a new application
4. Copy the "Access Key"
5. Paste it in `.env` file

### Step 4: Add Folklore Content

Edit `content/folklore_database.json` and add your 75 folklore entries. The file already contains 3 example entries as templates.

**Minimum required fields per entry:**
- `id`: Unique 3-digit number (001-075)
- `name`: Name in English
- `name_russian`: Name in Russian (Cyrillic)
- `story_full`: Full 30-second narration in Russian
- `visual_tags`: Array of search terms for Unsplash
- `voice_tone`: One of: warm_grandfather, mysterious_elder, energetic_youth, solemn_narrator

### Step 5: Generate Your First Video

```bash
python scripts/generate_daily_content.py
```

**Output:**
- Video: `output/videos/YYYY-MM-DD_FolkloreName.mp4`
- Collage: `output/images/YYYY-MM-DD_XXX_collage.png`
- Audio: `output/audio/YYYY-MM-DD_XXX.mp3`

### Step 6: Test Individual Components

**Test image fetching:**
```bash
python scripts/fetch_images.py "russian folklore"
```

**Test TTS voice:**
```bash
python scripts/generate_voice.py "Привет, это тест голоса"
```

**Test collage creation:**
```bash
# First fetch some test images
mkdir -p output/images/test
python scripts/fetch_images.py "mystical forest"

# Then create a collage
python scripts/create_collage.py output/images/test output/test_collage.png
```

## 📊 Project Status Check

```bash
# Check if all dependencies are installed
pip list | grep -E "(Pillow|requests|edge-tts|opencv|anthropic)"

# Check if FFmpeg is available
which ffmpeg

# Verify fonts are installed
ls -lh assets/fonts/

# Check folklore database
python -c "import json; data = json.load(open('content/folklore_database.json')); print(f'Folklore entries: {len(data[\"folklore\"])}')"
```

## 🔧 Common Issues

### Issue: "UNSPLASH_ACCESS_KEY not found"
**Solution:** Make sure you created `.env` file and added your API key.

### Issue: "FFmpeg not found"
**Solution:** Install FFmpeg using your package manager (see Step 1).

### Issue: "Font does not support Cyrillic"
**Solution:** The included fonts (Roboto, Philosopher) support Cyrillic. If you added custom fonts, make sure they support Russian characters.

### Issue: "Rate limit exceeded" (Unsplash)
**Solution:** Free tier allows 50 requests/hour. Wait or use cached images.

## 📝 Next Steps

1. **Populate Database:** Add all 75 folklore entries to `content/folklore_database.json`
2. **Customize Layouts:** Edit `assets/templates/collage_layouts.json` to add/modify templates
3. **Setup Automation:** Push to GitHub and configure secrets for daily automation
4. **Post to Instagram:** Download videos from `output/videos/` and post manually

## 🤖 GitHub Actions Setup (Optional)

1. Push your repository to GitHub
2. Go to Settings → Secrets and variables → Actions
3. Add secret: `UNSPLASH_ACCESS_KEY` with your API key
4. The workflow will run daily at 9 AM UTC automatically
5. Download generated videos from Actions → Artifacts

## 💡 Tips

- **Start Small:** Begin with 10-15 folklore entries, test thoroughly, then expand to 75
- **Test Locally:** Always test generation locally before relying on GitHub Actions
- **Visual Variety:** Use diverse `visual_tags` for better image variety
- **Voice Variety:** Mix different `voice_tone` options across entries
- **Duration:** Keep `story_full` between 150-200 characters in Russian for 25-30s videos

## 📖 Full Documentation

See [README.md](README.md) for complete documentation including:
- Detailed architecture explanations
- All configuration options
- Troubleshooting guide
- API usage details

---

**Questions?** Open an issue on GitHub or check the README.md
