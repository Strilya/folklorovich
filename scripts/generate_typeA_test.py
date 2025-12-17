#!/usr/bin/env python3
"""
Generate a single Type A test video to review current implementation.
"""

import os
import sys
import json
import random
from pathlib import Path
from datetime import datetime

PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from scripts.render_video import create_slideshow_video
from scripts.fetch_images import fetch_images_russian

print("\n" + "="*70)
print("GENERATING TYPE A TEST VIDEO")
print("="*70 + "\n")

# Load visual themes
themes_file = PROJECT_ROOT / "content/visual_themes.json"
with open(themes_file, 'r') as f:
    themes = json.load(f)['themes']

# Pick a random theme
theme = random.choice(themes)
print(f"📋 Theme: {theme['name']}")
print(f"🔍 Keywords: {', '.join(theme['keywords'][:3])}")
print()

# Fetch 12 images
print("📸 Fetching 12 images from Unsplash...")
keywords = " ".join(theme['keywords'][:2])
image_paths = fetch_images_russian(keywords=keywords, num_images=12)
print(f"   ✅ Downloaded {len(image_paths)} images")
print()

# Select music
music_dir = PROJECT_ROOT / "assets/music/cinematic"
music_files = list(music_dir.glob("*.mp3"))
music_path = str(random.choice(music_files))
print(f"🎵 Music: {Path(music_path).name}")
print()

# Output location
output_dir = PROJECT_ROOT / "output/videos"
output_dir.mkdir(parents=True, exist_ok=True)
output_path = output_dir / f"test_typeA_{datetime.now().strftime('%Y%m%d_%H%M%S')}.mp4"

# Render
print("🎬 Rendering Type A video (15s, 12 images)...")
create_slideshow_video(
    image_paths=[str(p) for p in image_paths],
    output_path=str(output_path),
    reel_type="visual",
    music_path=music_path
)

print()
print("="*70)
print("✅ VIDEO CREATED!")
print("="*70)
print(f"\n📹 Location: {output_path}\n")
print("🔍 REVIEW CHECKLIST:")
print("   • Are images distinctly Russian/cultural?")
print("   • Is the pacing good (1.25s per image)?")
print("   • Does it hook viewers in first 3 seconds?")
print("   • Is content interesting/unique?")
print("   • Does it align with folklore/mystery brand?")
print("   • Would YOU scroll past this or watch it?")
print("\n" + "="*70 + "\n")
