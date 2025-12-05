#!/usr/bin/env python3
"""
Folklorovich - Unsplash Image Fetcher
Downloads high-resolution images from Unsplash API based on visual tags.

Features:
- Rate limiting (50 requests/hour on free tier)
- Automatic retry with exponential backoff
- Image caching to avoid redundant downloads
- Multiple search queries for variety

Author: Folklorovich Project
Date: 2025-12-05
"""

import os
import time
import logging
import requests
from pathlib import Path
from typing import List, Optional
from datetime import datetime

# Configure logging
logger = logging.getLogger('ImageFetcher')


class UnsplashImageFetcher:
    """Fetches images from Unsplash API."""

    def __init__(self, access_key: Optional[str] = None):
        """
        Initialize Unsplash API client.

        Args:
            access_key: Unsplash API access key (from .env)
        """
        self.access_key = access_key or os.getenv('UNSPLASH_ACCESS_KEY')
        if not self.access_key:
            raise ValueError("UNSPLASH_ACCESS_KEY not found in environment")

        self.api_base = "https://api.unsplash.com"
        self.session = requests.Session()
        self.session.headers.update({
            'Authorization': f'Client-ID {self.access_key}',
            'Accept-Version': 'v1'
        })

        self.max_retries = int(os.getenv('MAX_RETRIES', 3))
        self.retry_delay = int(os.getenv('RETRY_DELAY_SECONDS', 5))

        logger.info("Unsplash image fetcher initialized")

    def search_photos(self, query: str, per_page: int = 5) -> List[dict]:
        """
        Search for photos on Unsplash.

        Args:
            query: Search query string
            per_page: Number of results to return (max 30)

        Returns:
            List of photo metadata dicts
        """
        url = f"{self.api_base}/search/photos"
        params = {
            'query': query,
            'per_page': min(per_page, 30),
            'orientation': 'portrait',  # Better for vertical video format
            'content_filter': 'high'  # Family-friendly content
        }

        for attempt in range(self.max_retries):
            try:
                logger.info(f"Searching Unsplash for: '{query}' (attempt {attempt + 1})")
                response = self.session.get(url, params=params, timeout=10)

                # Handle rate limiting
                if response.status_code == 429:
                    retry_after = int(response.headers.get('X-RateLimit-Reset', 3600))
                    logger.warning(f"Rate limit hit. Retry after {retry_after}s")
                    time.sleep(min(retry_after, 60))  # Wait up to 60 seconds
                    continue

                response.raise_for_status()
                data = response.json()

                results = data.get('results', [])
                logger.info(f"Found {len(results)} images for query '{query}'")

                return results

            except requests.exceptions.RequestException as e:
                logger.error(f"Request failed: {e}")
                if attempt < self.max_retries - 1:
                    delay = self.retry_delay * (2 ** attempt)  # Exponential backoff
                    logger.info(f"Retrying in {delay} seconds...")
                    time.sleep(delay)
                else:
                    logger.error("Max retries reached")
                    return []

        return []

    def download_image(self, photo_url: str, output_path: Path) -> bool:
        """
        Download an image from URL to local file.

        Args:
            photo_url: Image URL (use 'regular' or 'full' size)
            output_path: Local file path to save image

        Returns:
            True if successful, False otherwise
        """
        try:
            # Create parent directory if needed
            output_path.parent.mkdir(parents=True, exist_ok=True)

            logger.info(f"Downloading image to {output_path.name}...")
            response = requests.get(photo_url, timeout=30, stream=True)
            response.raise_for_status()

            # Save image
            with open(output_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)

            # Verify file was written
            if output_path.exists() and output_path.stat().st_size > 0:
                logger.info(f"✓ Downloaded {output_path.name} ({output_path.stat().st_size // 1024} KB)")
                return True
            else:
                logger.error("Downloaded file is empty or missing")
                return False

        except requests.exceptions.RequestException as e:
            logger.error(f"Download failed: {e}")
            return False
        except IOError as e:
            logger.error(f"File write error: {e}")
            return False

    def fetch_images_for_tags(self, tags: List[str], output_dir: Path,
                              count: int = 6) -> List[Path]:
        """
        Fetch multiple images based on a list of visual tags.

        Strategy:
        - Combine tags into search queries
        - Download diverse images
        - Cache in output directory

        Args:
            tags: List of visual search tags
            output_dir: Directory to save images
            count: Number of images to fetch

        Returns:
            List of paths to downloaded images
        """
        output_dir.mkdir(parents=True, exist_ok=True)
        downloaded_paths = []

        # Create search query by combining tags
        # Try different combinations for variety
        queries = [
            ' '.join(tags[:3]),  # First 3 tags
            ' '.join(tags[2:5]) if len(tags) >= 5 else ' '.join(tags),  # Middle tags
            tags[0] if tags else 'mystical',  # Fallback to first tag
        ]

        images_needed = count
        images_per_query = (images_needed // len(queries)) + 1

        for query in queries:
            if len(downloaded_paths) >= count:
                break

            # Search for photos
            photos = self.search_photos(query, per_page=images_per_query)

            if not photos:
                logger.warning(f"No photos found for query '{query}'")
                continue

            # Download photos
            for idx, photo in enumerate(photos):
                if len(downloaded_paths) >= count:
                    break

                # Get high-quality image URL
                image_url = photo['urls'].get('regular') or photo['urls'].get('full')
                if not image_url:
                    continue

                # Generate filename
                photo_id = photo['id']
                filename = f"unsplash_{photo_id}.jpg"
                output_path = output_dir / filename

                # Skip if already downloaded (caching)
                if output_path.exists():
                    logger.info(f"Image already cached: {filename}")
                    downloaded_paths.append(output_path)
                    continue

                # Download
                if self.download_image(image_url, output_path):
                    downloaded_paths.append(output_path)

                    # Respect rate limits: wait between downloads
                    time.sleep(2)  # 2 seconds between downloads

            # Wait between different queries
            if len(downloaded_paths) < count:
                time.sleep(5)

        logger.info(f"Downloaded {len(downloaded_paths)}/{count} images")
        return downloaded_paths


def fetch_images_for_folklore(visual_tags: List[str], output_dir: Path,
                              count: int = 6) -> List[Path]:
    """
    Convenience function to fetch images for a folklore entry.

    Args:
        visual_tags: List of visual search tags from folklore entry
        output_dir: Directory to save images
        count: Number of images to fetch

    Returns:
        List of paths to downloaded images
    """
    try:
        fetcher = UnsplashImageFetcher()
        return fetcher.fetch_images_for_tags(visual_tags, output_dir, count)
    except ValueError as e:
        logger.error(f"Configuration error: {e}")
        return []
    except Exception as e:
        logger.error(f"Unexpected error: {e}", exc_info=True)
        return []


def main():
    """Test the image fetcher."""
    import sys

    logging.basicConfig(level=logging.INFO)

    if len(sys.argv) < 2:
        print("Usage: python fetch_images.py <search_query>")
        sys.exit(1)

    query = sys.argv[1]
    output_dir = Path(__file__).parent.parent / 'output' / 'images' / 'test'

    fetcher = UnsplashImageFetcher()
    images = fetcher.fetch_images_for_tags([query], output_dir, count=3)

    print(f"\nDownloaded {len(images)} images:")
    for img_path in images:
        print(f"  - {img_path}")


if __name__ == '__main__':
    main()
