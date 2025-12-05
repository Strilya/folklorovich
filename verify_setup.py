#!/usr/bin/env python3
"""
Folklorovich Setup Verification Script
Checks if all components are properly installed and configured.

Usage: python verify_setup.py
"""

import sys
import subprocess
from pathlib import Path

# ANSI color codes for output
GREEN = '\033[92m'
RED = '\033[91m'
YELLOW = '\033[93m'
BLUE = '\033[94m'
RESET = '\033[0m'


def print_header(text):
    """Print colored header."""
    print(f"\n{BLUE}{'=' * 60}{RESET}")
    print(f"{BLUE}{text:^60}{RESET}")
    print(f"{BLUE}{'=' * 60}{RESET}\n")


def check_item(description, success, details=""):
    """Print check result."""
    status = f"{GREEN}✓{RESET}" if success else f"{RED}✗{RESET}"
    print(f"  {status} {description}")
    if details:
        print(f"      {details}")
    return success


def main():
    """Run all verification checks."""
    print_header("Folklorovich Setup Verification")

    all_checks_passed = True
    project_root = Path(__file__).parent

    # 1. Check directory structure
    print(f"{YELLOW}[1/7] Checking directory structure...{RESET}")

    required_dirs = [
        'content',
        'scripts',
        'assets/fonts',
        'assets/templates',
        'output/images',
        'output/audio',
        'output/videos',
        '.github/workflows'
    ]

    for dir_path in required_dirs:
        full_path = project_root / dir_path
        all_checks_passed &= check_item(
            f"Directory: {dir_path}",
            full_path.exists(),
            f"Path: {full_path}"
        )

    # 2. Check required files
    print(f"\n{YELLOW}[2/7] Checking required files...{RESET}")

    required_files = [
        'README.md',
        'QUICKSTART.md',
        'requirements.txt',
        '.env.template',
        '.gitignore',
        'content/folklore_database.json',
        'content/metadata.json',
        'assets/templates/collage_layouts.json',
        'scripts/generate_daily_content.py',
        'scripts/fetch_images.py',
        'scripts/create_collage.py',
        'scripts/generate_voice.py',
        'scripts/render_video.py',
        '.github/workflows/daily_generation.yml'
    ]

    for file_path in required_files:
        full_path = project_root / file_path
        all_checks_passed &= check_item(
            f"File: {file_path}",
            full_path.exists()
        )

    # 3. Check fonts
    print(f"\n{YELLOW}[3/7] Checking fonts...{RESET}")

    fonts = ['Roboto-Regular.ttf', 'Roboto-Bold.ttf', 'Philosopher-Regular.ttf']
    for font in fonts:
        font_path = project_root / 'assets' / 'fonts' / font
        exists = font_path.exists()
        size = font_path.stat().st_size / 1024 if exists else 0
        all_checks_passed &= check_item(
            f"Font: {font}",
            exists and size > 10,  # At least 10KB
            f"Size: {size:.1f} KB" if exists else "Not found"
        )

    # 4. Check Python dependencies
    print(f"\n{YELLOW}[4/7] Checking Python dependencies...{RESET}")

    required_packages = [
        'PIL',  # Pillow
        'requests',
        'edge_tts',
        'cv2',  # opencv-python
        'dotenv',
        'anthropic'
    ]

    for package in required_packages:
        try:
            __import__(package)
            check_item(f"Python package: {package}", True, "Installed")
        except ImportError:
            all_checks_passed &= check_item(
                f"Python package: {package}",
                False,
                "Not installed - run: pip install -r requirements.txt"
            )

    # 5. Check FFmpeg
    print(f"\n{YELLOW}[5/7] Checking FFmpeg...{RESET}")

    try:
        result = subprocess.run(
            ['ffmpeg', '-version'],
            capture_output=True,
            text=True,
            timeout=5
        )
        version_line = result.stdout.split('\n')[0] if result.stdout else "Unknown version"
        all_checks_passed &= check_item(
            "FFmpeg installed",
            result.returncode == 0,
            version_line
        )

        # Check ffprobe too
        result = subprocess.run(
            ['ffprobe', '-version'],
            capture_output=True,
            text=True,
            timeout=5
        )
        all_checks_passed &= check_item(
            "ffprobe installed",
            result.returncode == 0
        )

    except (subprocess.TimeoutExpired, FileNotFoundError):
        all_checks_passed &= check_item(
            "FFmpeg installed",
            False,
            "Install with: brew install ffmpeg (macOS) or apt-get install ffmpeg (Linux)"
        )

    # 6. Check configuration
    print(f"\n{YELLOW}[6/7] Checking configuration...{RESET}")

    env_file = project_root / '.env'
    env_template = project_root / '.env.template'

    check_item("Environment template exists", env_template.exists())

    if env_file.exists():
        check_item(".env file exists", True, "✓ Ready for API keys")
        # Check if it has the required keys (not empty template)
        with open(env_file) as f:
            content = f.read()
            has_unsplash = 'UNSPLASH_ACCESS_KEY' in content
            check_item(
                "Unsplash API key configured",
                has_unsplash and 'your_unsplash' not in content,
                "Remember to add your actual API key!"
            )
    else:
        all_checks_passed &= check_item(
            ".env file exists",
            False,
            "Run: cp .env.template .env"
        )

    # 7. Check folklore database
    print(f"\n{YELLOW}[7/7] Checking content database...{RESET}")

    try:
        import json
        with open(project_root / 'content' / 'folklore_database.json') as f:
            db = json.load(f)
            folklore_count = len(db.get('folklore', []))

            check_item(
                f"Folklore entries: {folklore_count}",
                folklore_count > 0,
                f"Target: 75 entries (current: {folklore_count})"
            )

            if folklore_count > 0:
                entry = db['folklore'][0]
                required_fields = ['id', 'name', 'story_full', 'visual_tags', 'voice_tone']
                missing = [f for f in required_fields if f not in entry]

                check_item(
                    "Database schema valid",
                    len(missing) == 0,
                    f"Missing fields: {missing}" if missing else "All required fields present"
                )

    except Exception as e:
        all_checks_passed &= check_item(
            "Folklore database valid",
            False,
            f"Error: {e}"
        )

    # Final summary
    print_header("Verification Summary")

    if all_checks_passed:
        print(f"{GREEN}✓ All checks passed! Your Folklorovich setup is ready.{RESET}\n")
        print("Next steps:")
        print("  1. Add your Unsplash API key to .env")
        print("  2. Populate folklore_database.json with 75 entries")
        print("  3. Run: python scripts/generate_daily_content.py")
        return 0
    else:
        print(f"{RED}✗ Some checks failed. Please fix the issues above.{RESET}\n")
        print("Need help? Check:")
        print("  - README.md for detailed documentation")
        print("  - QUICKSTART.md for setup instructions")
        return 1


if __name__ == '__main__':
    sys.exit(main())
