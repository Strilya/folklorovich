#!/usr/bin/env python3
"""
Folklorovich - Utility Functions
Shared utilities for error handling, logging, validation, and monitoring.

Author: Folklorovich Project
Date: 2025-12-05
"""

import os
import sys
import json
import time
import logging
import functools
from pathlib import Path
from datetime import datetime
from typing import Optional, Callable, Any, Dict
from logging.handlers import RotatingFileHandler

# Project paths
PROJECT_ROOT = Path(__file__).parent.parent
LOGS_DIR = PROJECT_ROOT / 'logs'
OUTPUT_DIR = PROJECT_ROOT / 'output'


def setup_logging(name: str = 'folklorovich', level: str = 'INFO') -> logging.Logger:
    """
    Set up comprehensive logging with rotating file handlers.

    Creates:
    - Daily rotating log files in logs/ directory
    - Console output for real-time monitoring
    - Separate error log for failures

    Args:
        name: Logger name
        level: Logging level (DEBUG, INFO, WARNING, ERROR)

    Returns:
        Configured logger instance
    """
    # Create logs directory
    LOGS_DIR.mkdir(parents=True, exist_ok=True)

    # Create logger
    logger = logging.getLogger(name)
    logger.setLevel(getattr(logging, level.upper()))

    # Remove existing handlers to avoid duplicates
    logger.handlers.clear()

    # Format
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    # Main log file (rotating, 10MB max, keep 7 backups)
    log_file = LOGS_DIR / f"{name}.log"
    file_handler = RotatingFileHandler(
        log_file,
        maxBytes=10 * 1024 * 1024,  # 10 MB
        backupCount=7
    )
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    # Error log file (only errors and critical)
    error_log = LOGS_DIR / f"{name}_errors.log"
    error_handler = RotatingFileHandler(
        error_log,
        maxBytes=5 * 1024 * 1024,  # 5 MB
        backupCount=3
    )
    error_handler.setLevel(logging.ERROR)
    error_handler.setFormatter(formatter)
    logger.addHandler(error_handler)

    # Daily log file (one file per day)
    daily_log = LOGS_DIR / f"{name}_{datetime.now().strftime('%Y-%m-%d')}.log"
    daily_handler = logging.FileHandler(daily_log)
    daily_handler.setLevel(logging.INFO)
    daily_handler.setFormatter(formatter)
    logger.addHandler(daily_handler)

    return logger


def retry_with_backoff(max_retries: int = 3, backoff_factor: float = 2.0,
                       exceptions: tuple = (Exception,)):
    """
    Decorator for retrying functions with exponential backoff.

    Args:
        max_retries: Maximum number of retry attempts
        backoff_factor: Multiplier for wait time between retries
        exceptions: Tuple of exceptions to catch and retry

    Example:
        @retry_with_backoff(max_retries=3, backoff_factor=2.0)
        def fetch_data():
            # Code that might fail
            pass
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            logger = logging.getLogger('folklorovich')

            for attempt in range(max_retries):
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    if attempt == max_retries - 1:
                        logger.error(f"{func.__name__} failed after {max_retries} attempts: {e}")
                        raise

                    wait_time = backoff_factor ** attempt
                    logger.warning(
                        f"{func.__name__} failed (attempt {attempt + 1}/{max_retries}): {e}. "
                        f"Retrying in {wait_time:.1f}s..."
                    )
                    time.sleep(wait_time)

            return None
        return wrapper
    return decorator


def validate_image(image_path: Path, min_width: int = 1080,
                   min_height: int = 1080) -> bool:
    """
    Validate image quality and dimensions.

    Args:
        image_path: Path to image file
        min_width: Minimum acceptable width
        min_height: Minimum acceptable height

    Returns:
        True if image is valid, False otherwise
    """
    try:
        from PIL import Image

        if not image_path.exists():
            return False

        # Check file size (should be > 10KB)
        if image_path.stat().st_size < 10 * 1024:
            return False

        # Check dimensions
        with Image.open(image_path) as img:
            width, height = img.size
            if width < min_width or height < min_height:
                return False

            # Check if image is corrupted
            img.verify()

        return True

    except Exception as e:
        logging.getLogger('folklorovich').error(f"Image validation failed: {e}")
        return False


def validate_audio(audio_path: Path, min_duration: float = 10.0,
                   max_duration: float = 45.0) -> bool:
    """
    Validate audio file quality and duration.

    Args:
        audio_path: Path to audio file
        min_duration: Minimum acceptable duration in seconds
        max_duration: Maximum acceptable duration in seconds

    Returns:
        True if audio is valid, False otherwise
    """
    import subprocess

    try:
        if not audio_path.exists():
            return False

        # Check file size (should be > 5KB)
        if audio_path.stat().st_size < 5 * 1024:
            return False

        # Get duration using ffprobe
        cmd = [
            'ffprobe',
            '-v', 'error',
            '-show_entries', 'format=duration',
            '-of', 'default=noprint_wrappers=1:nokey=1',
            str(audio_path)
        ]

        result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
        if result.returncode != 0:
            return False

        duration = float(result.stdout.strip())

        return min_duration <= duration <= max_duration

    except Exception as e:
        logging.getLogger('folklorovich').error(f"Audio validation failed: {e}")
        return False


def validate_video(video_path: Path, min_duration: float = 25.0,
                   max_duration: float = 35.0) -> bool:
    """
    Validate video file quality and specifications.

    Args:
        video_path: Path to video file
        min_duration: Minimum acceptable duration in seconds
        max_duration: Maximum acceptable duration in seconds

    Returns:
        True if video is valid, False otherwise
    """
    import subprocess

    try:
        if not video_path.exists():
            return False

        # Check file size (should be > 100KB)
        if video_path.stat().st_size < 100 * 1024:
            return False

        # Get video info using ffprobe
        cmd = [
            'ffprobe',
            '-v', 'error',
            '-show_entries', 'format=duration:stream=width,height',
            '-of', 'json',
            str(video_path)
        ]

        result = subprocess.run(cmd, capture_output=True, text=True, timeout=15)
        if result.returncode != 0:
            return False

        info = json.loads(result.stdout)

        # Check duration
        duration = float(info['format']['duration'])
        if not (min_duration <= duration <= max_duration):
            return False

        # Check dimensions (should be 1080x1920 or close)
        streams = info.get('streams', [])
        if streams:
            width = streams[0].get('width', 0)
            height = streams[0].get('height', 0)

            # Allow some tolerance
            if not (1000 <= width <= 1200 and 1800 <= height <= 2000):
                return False

        return True

    except Exception as e:
        logging.getLogger('folklorovich').error(f"Video validation failed: {e}")
        return False


def track_api_usage(api_name: str, request_type: str = 'general') -> None:
    """
    Track API usage for cost monitoring.

    Args:
        api_name: Name of API (e.g., 'unsplash', 'edge_tts')
        request_type: Type of request for detailed tracking
    """
    usage_file = PROJECT_ROOT / 'logs' / 'api_usage.json'

    try:
        # Load existing usage data
        if usage_file.exists():
            with open(usage_file, 'r') as f:
                usage_data = json.load(f)
        else:
            usage_data = {}

        # Initialize API tracking if needed
        if api_name not in usage_data:
            usage_data[api_name] = {
                'total_requests': 0,
                'requests_by_day': {},
                'requests_by_type': {}
            }

        # Update counters
        today = datetime.now().strftime('%Y-%m-%d')
        usage_data[api_name]['total_requests'] += 1
        usage_data[api_name]['requests_by_day'][today] = \
            usage_data[api_name]['requests_by_day'].get(today, 0) + 1
        usage_data[api_name]['requests_by_type'][request_type] = \
            usage_data[api_name]['requests_by_type'].get(request_type, 0) + 1
        usage_data[api_name]['last_request'] = datetime.now().isoformat()

        # Save updated data
        usage_file.parent.mkdir(parents=True, exist_ok=True)
        with open(usage_file, 'w') as f:
            json.dump(usage_data, f, indent=2)

    except Exception as e:
        logging.getLogger('folklorovich').warning(f"Could not track API usage: {e}")


def check_storage_usage() -> Dict[str, Any]:
    """
    Check disk usage of output directories.

    Returns:
        Dictionary with storage statistics
    """
    import shutil

    stats = {
        'total_size_mb': 0,
        'images_size_mb': 0,
        'audio_size_mb': 0,
        'videos_size_mb': 0,
        'timestamp': datetime.now().isoformat()
    }

    try:
        def get_dir_size(path: Path) -> float:
            """Get directory size in MB"""
            total = 0
            if path.exists():
                for item in path.rglob('*'):
                    if item.is_file():
                        total += item.stat().st_size
            return total / (1024 * 1024)

        stats['images_size_mb'] = round(get_dir_size(OUTPUT_DIR / 'images'), 2)
        stats['audio_size_mb'] = round(get_dir_size(OUTPUT_DIR / 'audio'), 2)
        stats['videos_size_mb'] = round(get_dir_size(OUTPUT_DIR / 'videos'), 2)
        stats['total_size_mb'] = round(
            stats['images_size_mb'] + stats['audio_size_mb'] + stats['videos_size_mb'],
            2
        )

        # Get available disk space
        disk_usage = shutil.disk_usage(OUTPUT_DIR)
        stats['available_gb'] = round(disk_usage.free / (1024**3), 2)

    except Exception as e:
        logging.getLogger('folklorovich').warning(f"Could not check storage: {e}")

    return stats


def alert_if_limits_approaching() -> None:
    """
    Check if approaching free-tier limits and log warnings.

    Checks:
    - Unsplash API: 50 requests/hour
    - Storage: Warn if > 1GB used
    """
    logger = logging.getLogger('folklorovich')
    usage_file = PROJECT_ROOT / 'logs' / 'api_usage.json'

    try:
        # Check API usage
        if usage_file.exists():
            with open(usage_file, 'r') as f:
                usage_data = json.load(f)

            # Check Unsplash (50 req/hour limit)
            if 'unsplash' in usage_data:
                today = datetime.now().strftime('%Y-%m-%d')
                today_requests = usage_data['unsplash']['requests_by_day'].get(today, 0)

                if today_requests > 40:
                    logger.warning(
                        f"⚠️  Unsplash API usage high today: {today_requests}/50 requests. "
                        "Approaching free tier limit!"
                    )

        # Check storage
        storage = check_storage_usage()
        if storage['total_size_mb'] > 1000:  # > 1GB
            logger.warning(
                f"⚠️  Storage usage high: {storage['total_size_mb']} MB. "
                "Consider cleaning up old files."
            )

        if storage.get('available_gb', 999) < 5:  # < 5GB free
            logger.error(
                f"❌ Low disk space: {storage.get('available_gb', 0)} GB available. "
                "Free up space immediately!"
            )

    except Exception as e:
        logger.warning(f"Could not check limits: {e}")


def generate_summary_report(folklore_id: str, success: bool,
                           generation_time: float, errors: list = None) -> str:
    """
    Generate human-readable summary report after generation.

    Args:
        folklore_id: ID of folklore entry generated
        success: Whether generation succeeded
        generation_time: Time taken in seconds
        errors: List of errors encountered

    Returns:
        Formatted summary string
    """
    lines = [
        "=" * 60,
        "FOLKLOROVICH GENERATION REPORT",
        "=" * 60,
        f"Folklore ID: {folklore_id}",
        f"Status: {'✅ SUCCESS' if success else '❌ FAILED'}",
        f"Generation Time: {generation_time:.2f} seconds",
        f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
    ]

    if errors:
        lines.append("\nErrors Encountered:")
        for i, error in enumerate(errors, 1):
            lines.append(f"  {i}. {error}")

    # Add storage info
    storage = check_storage_usage()
    lines.extend([
        "",
        "Storage Usage:",
        f"  Images: {storage['images_size_mb']} MB",
        f"  Audio: {storage['audio_size_mb']} MB",
        f"  Videos: {storage['videos_size_mb']} MB",
        f"  Total: {storage['total_size_mb']} MB",
    ])

    lines.append("=" * 60)

    return "\n".join(lines)


def safe_file_operation(operation: Callable, *args, **kwargs) -> Optional[Any]:
    """
    Safely perform file operations with error handling.

    Args:
        operation: File operation function to execute
        *args, **kwargs: Arguments to pass to operation

    Returns:
        Result of operation or None if failed
    """
    logger = logging.getLogger('folklorovich')

    try:
        return operation(*args, **kwargs)
    except PermissionError as e:
        logger.error(f"Permission denied: {e}")
    except FileNotFoundError as e:
        logger.error(f"File not found: {e}")
    except OSError as e:
        logger.error(f"OS error: {e}")
    except Exception as e:
        logger.error(f"Unexpected error in file operation: {e}")

    return None


# Initialize logging when module is imported
logger = setup_logging()
