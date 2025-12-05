#!/usr/bin/env python3
"""
Folklorovich - Multi-Source Image Fetcher with Russian Cultural Filtering
Downloads high-resolution images from Unsplash, Pexels, and Pixabay APIs
with strict Russian cultural validation.

Features:
- Multi-source: Unsplash + Pexels + Pixabay
- Strict Russian cultural filtering
- Cyrillic keyword support
- Metadata validation
- Automatic retry with exponential backoff
- Image caching

Author: Folklorovich Project
Date: 2025-12-05
"""

import os
import time
import logging
import requests
from pathlib import Path
from typing import List, Optional, Dict, Any
from datetime import datetime

# Configure logging
logger = logging.getLogger('ImageFetcher')

# Russian cultural keywords for strict filtering
RUSSIAN_KEYWORDS = [
    'Russia', 'Russian', 'Россия', 'русский',
    'Siberia', 'Сибирь', 'Ural', 'Урал',
    'Moscow', 'Москва', 'Golden Ring',
    'Orthodox', 'православный', 'церковь',
    'birch forest', 'берёза', 'берёзовый лес',
    'wooden architecture', 'изба', 'деревянная архитектура',
    'Volga', 'Волга', 'St Petersburg', 'Санкт-Петербург',
    'Kremlin', 'Кремль', 'onion dome', 'луковичный купол',
    'matryoshka', 'матрёшка', 'samovar', 'самовар',
    'Khokhloma', 'хохлома', 'Gzhel', 'гжель', 'Palekh', 'палех'
]

# Forbidden content indicators
FORBIDDEN_KEYWORDS = [
    'spain', 'spanish', 'casa', 'mediterranean',
    'polish', 'poland', 'polska',
    'italy', 'italian', 'italian architecture',
    'france', 'french', 'paris',
    'latin america', 'south america',
    'asia', 'asian', 'china', 'japan',
    'africa', 'african'
]


class ImageValidator:
    """Validates images for Russian cultural authenticity."""

    @staticmethod
    def validate_russian_content(metadata: Dict[str, Any]) -> bool:
        """
        Validate that image contains Russian cultural content.

        Args:
            metadata: Image metadata (description, tags, location, etc.)

        Returns:
            True if valid Russian content, False otherwise
        """
        # Extract searchable text from metadata
        searchable_text = ' '.join([
            str(metadata.get('description', '')),
            str(metadata.get('alt_description', '')),
            ' '.join(metadata.get('tags', [])),
            str(metadata.get('location', '')),
            str(metadata.get('user', {}).get('name', ''))
        ]).lower()

        # Check for forbidden content first
        for keyword in FORBIDDEN_KEYWORDS:
            if keyword.lower() in searchable_text:
                logger.warning(f"Rejected: Forbidden keyword '{keyword}' found in metadata")
                return False

        # Check for Russian keywords
        found_russian = False
        for keyword in RUSSIAN_KEYWORDS:
            if keyword.lower() in searchable_text:
                found_russian = True
                logger.info(f"✓ Russian keyword '{keyword}' found in metadata")
                break

        if not found_russian:
            logger.warning("Rejected: No Russian cultural keywords found in metadata")

        return found_russian


class UnsplashImageFetcher:
    """Fetches images from Unsplash API with Russian cultural filtering."""

    def __init__(self, access_key: Optional[str] = None):
        """Initialize Unsplash API client."""
        self.access_key = access_key or os.getenv('UNSPLASH_ACCESS_KEY')
        if not self.access_key:
            raise ValueError("UNSPLASH_ACCESS_KEY not found in environment")

        self.api_base = "https://api.unsplash.com"
        self.session = requests.Session()
        self.session.headers.update({
            'Authorization': f'Client-ID {self.access_key}',
            'Accept-Version': 'v1'
        })

        self.validator = ImageValidator()
        self.max_retries = int(os.getenv('MAX_RETRIES', 3))
        self.retry_delay = int(os.getenv('RETRY_DELAY_SECONDS', 5))

        logger.info("Unsplash image fetcher initialized")

    def build_russian_query(self, tags: List[str]) -> str:
        """
        Build search query with mandatory Russian context.

        Args:
            tags: Base visual tags

        Returns:
            Enhanced search query with Russian keywords
        """
        # Always include Russian context
        base_tags = ' '.join(tags[:2])  # Use first 2 tags
        russian_context = 'Russia Russian Orthodox wooden architecture birch'

        return f"{base_tags} {russian_context}"

    def search_photos(self, query: str, per_page: int = 10) -> List[dict]:
        """Search for photos on Unsplash with validation."""
        url = f"{self.api_base}/search/photos"
        params = {
            'query': query,
            'per_page': min(per_page, 30),
            'orientation': 'portrait',
            'content_filter': 'high'
        }

        for attempt in range(self.max_retries):
            try:
                logger.info(f"Searching Unsplash for: '{query}' (attempt {attempt + 1})")
                response = self.session.get(url, params=params, timeout=10)

                if response.status_code == 429:
                    retry_after = int(response.headers.get('X-RateLimit-Reset', 3600))
                    logger.warning(f"Rate limit hit. Retry after {retry_after}s")
                    time.sleep(min(retry_after, 60))
                    continue

                response.raise_for_status()
                data = response.json()

                results = data.get('results', [])
                logger.info(f"Found {len(results)} images for query '{query}'")

                # Validate Russian content
                validated = []
                for photo in results:
                    metadata = {
                        'description': photo.get('description', ''),
                        'alt_description': photo.get('alt_description', ''),
                        'tags': [tag.get('title', '') for tag in photo.get('tags', [])],
                        'location': photo.get('location', {}).get('name', ''),
                        'user': photo.get('user', {})
                    }

                    if self.validator.validate_russian_content(metadata):
                        validated.append(photo)

                logger.info(f"Validated {len(validated)}/{len(results)} images as Russian content")
                return validated

            except requests.exceptions.RequestException as e:
                logger.error(f"Request failed: {e}")
                if attempt < self.max_retries - 1:
                    delay = self.retry_delay * (2 ** attempt)
                    logger.info(f"Retrying in {delay} seconds...")
                    time.sleep(delay)

        return []

    def download_image(self, photo_url: str, output_path: Path) -> bool:
        """Download an image from URL to local file."""
        try:
            output_path.parent.mkdir(parents=True, exist_ok=True)

            logger.info(f"Downloading image to {output_path.name}...")
            response = requests.get(photo_url, timeout=30, stream=True)
            response.raise_for_status()

            with open(output_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)

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


class PexelsImageFetcher:
    """Fetches images from Pexels API with Russian cultural filtering."""

    def __init__(self, api_key: Optional[str] = None):
        """Initialize Pexels API client."""
        self.api_key = api_key or os.getenv('PEXELS_API_KEY')
        if not self.api_key:
            raise ValueError("PEXELS_API_KEY not found in environment")

        self.api_base = "https://api.pexels.com/v1"
        self.session = requests.Session()
        self.session.headers.update({
            'Authorization': self.api_key
        })

        self.validator = ImageValidator()
        self.max_retries = 3

        logger.info("Pexels image fetcher initialized")

    def search_photos(self, query: str, per_page: int = 10) -> List[dict]:
        """Search for photos on Pexels with validation."""
        url = f"{self.api_base}/search"
        params = {
            'query': query,
            'per_page': min(per_page, 80),
            'orientation': 'portrait'
        }

        try:
            logger.info(f"Searching Pexels for: '{query}'")
            response = self.session.get(url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()

            photos = data.get('photos', [])
            logger.info(f"Found {len(photos)} images on Pexels")

            # Validate Russian content
            validated = []
            for photo in photos:
                metadata = {
                    'description': photo.get('alt', ''),
                    'alt_description': photo.get('alt', ''),
                    'tags': [],
                    'location': '',
                    'user': {'name': photo.get('photographer', '')}
                }

                if self.validator.validate_russian_content(metadata):
                    validated.append(photo)

            logger.info(f"Validated {len(validated)}/{len(photos)} Pexels images")
            return validated

        except requests.exceptions.RequestException as e:
            logger.error(f"Pexels request failed: {e}")
            return []

    def download_image(self, photo_url: str, output_path: Path) -> bool:
        """Download an image from Pexels."""
        try:
            output_path.parent.mkdir(parents=True, exist_ok=True)

            logger.info(f"Downloading Pexels image to {output_path.name}...")
            response = requests.get(photo_url, timeout=30, stream=True)
            response.raise_for_status()

            with open(output_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)

            if output_path.exists() and output_path.stat().st_size > 0:
                logger.info(f"✓ Downloaded {output_path.name} ({output_path.stat().st_size // 1024} KB)")
                return True

            return False

        except Exception as e:
            logger.error(f"Pexels download failed: {e}")
            return False


class PixabayImageFetcher:
    """Fetches images from Pixabay API with Russian cultural filtering."""

    def __init__(self, api_key: Optional[str] = None):
        """Initialize Pixabay API client."""
        self.api_key = api_key or os.getenv('PIXABAY_API_KEY')
        if not self.api_key:
            raise ValueError("PIXABAY_API_KEY not found in environment")

        self.api_base = "https://pixabay.com/api/"
        self.validator = ImageValidator()
        self.max_retries = 3

        logger.info("Pixabay image fetcher initialized")

    def search_photos(self, query: str, per_page: int = 10) -> List[dict]:
        """Search for photos on Pixabay with validation."""
        params = {
            'key': self.api_key,
            'q': query,
            'per_page': min(per_page, 200),
            'image_type': 'photo',
            'orientation': 'vertical'
        }

        try:
            logger.info(f"Searching Pixabay for: '{query}'")
            response = requests.get(self.api_base, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()

            hits = data.get('hits', [])
            logger.info(f"Found {len(hits)} images on Pixabay")

            # Validate Russian content
            validated = []
            for hit in hits:
                metadata = {
                    'description': hit.get('tags', ''),
                    'alt_description': hit.get('tags', ''),
                    'tags': hit.get('tags', '').split(', '),
                    'location': '',
                    'user': {'name': hit.get('user', '')}
                }

                if self.validator.validate_russian_content(metadata):
                    validated.append(hit)

            logger.info(f"Validated {len(validated)}/{len(hits)} Pixabay images")
            return validated

        except requests.exceptions.RequestException as e:
            logger.error(f"Pixabay request failed: {e}")
            return []

    def download_image(self, photo_url: str, output_path: Path) -> bool:
        """Download an image from Pixabay."""
        try:
            output_path.parent.mkdir(parents=True, exist_ok=True)

            logger.info(f"Downloading Pixabay image to {output_path.name}...")
            response = requests.get(photo_url, timeout=30, stream=True)
            response.raise_for_status()

            with open(output_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)

            if output_path.exists() and output_path.stat().st_size > 0:
                logger.info(f"✓ Downloaded {output_path.name} ({output_path.stat().st_size // 1024} KB)")
                return True

            return False

        except Exception as e:
            logger.error(f"Pixabay download failed: {e}")
            return False


def fetch_images_for_folklore(visual_tags: List[str], output_dir: Path,
                              count: int = 10) -> List[Path]:
    """
    Fetch images from multiple sources with Russian cultural validation.

    Strategy:
    - 4 images from Unsplash
    - 4 images from Pexels
    - 2 images from Pixabay
    - Mix and randomize order

    Args:
        visual_tags: List of visual search tags from folklore entry
        output_dir: Directory to save images
        count: Total number of images to fetch (default 10)

    Returns:
        List of paths to downloaded images
    """
    import random

    output_dir.mkdir(parents=True, exist_ok=True)
    downloaded_paths = []

    # Build Russian-specific query
    base_query = ' '.join(visual_tags[:2])
    russian_query = f"{base_query} Russia Russian Orthodox birch wooden architecture"

    # Also try Cyrillic search
    cyrillic_query = f"{base_query} Россия православный изба берёза"

    # Initialize fetchers (handle missing API keys gracefully)
    fetchers = []

    try:
        unsplash = UnsplashImageFetcher()
        fetchers.append(('unsplash', unsplash, 4))
    except ValueError:
        logger.warning("Unsplash API key not found, skipping")

    try:
        pexels = PexelsImageFetcher()
        fetchers.append(('pexels', pexels, 4))
    except ValueError:
        logger.warning("Pexels API key not found, skipping")

    try:
        pixabay = PixabayImageFetcher()
        fetchers.append(('pixabay', pixabay, 2))
    except ValueError:
        logger.warning("Pixabay API key not found, skipping")

    if not fetchers:
        logger.error("No API keys configured. Cannot fetch images.")
        return []

    # Fetch from each source
    for source_name, fetcher, target_count in fetchers:
        logger.info(f"\n{'='*60}")
        logger.info(f"Fetching {target_count} images from {source_name.upper()}")
        logger.info(f"{'='*60}")

        # Try Russian query first, then Cyrillic
        photos = fetcher.search_photos(russian_query, per_page=target_count * 2)

        if len(photos) < target_count and source_name == 'unsplash':
            logger.info("Trying Cyrillic query for more results...")
            cyrillic_photos = fetcher.search_photos(cyrillic_query, per_page=target_count)
            photos.extend(cyrillic_photos)

        # Download images
        for idx, photo in enumerate(photos[:target_count]):
            if len(downloaded_paths) >= count:
                break

            # Get image URL based on source
            if source_name == 'unsplash':
                image_url = photo['urls'].get('regular') or photo['urls'].get('full')
                photo_id = photo['id']
            elif source_name == 'pexels':
                image_url = photo['src'].get('large') or photo['src'].get('original')
                photo_id = photo['id']
            elif source_name == 'pixabay':
                image_url = photo.get('largeImageURL') or photo.get('webformatURL')
                photo_id = photo['id']
            else:
                continue

            if not image_url:
                continue

            # Generate filename
            timestamp = int(time.time())
            filename = f"{source_name}_{photo_id}_{timestamp}.jpg"
            output_path = output_dir / filename

            # Skip if already exists
            if output_path.exists():
                logger.info(f"Image already cached: {filename}")
                downloaded_paths.append(output_path)
                continue

            # Download
            if fetcher.download_image(image_url, output_path):
                downloaded_paths.append(output_path)
                time.sleep(1)  # Rate limiting

    # Shuffle to mix sources
    random.shuffle(downloaded_paths)

    logger.info(f"\n{'='*60}")
    logger.info(f"✓ Downloaded {len(downloaded_paths)}/{count} total images")
    logger.info(f"{'='*60}\n")

    return downloaded_paths[:count]


def main():
    """Test the image fetcher."""
    import sys

    logging.basicConfig(level=logging.INFO)

    if len(sys.argv) < 2:
        print("Usage: python fetch_images.py <search_query>")
        sys.exit(1)

    query = sys.argv[1]
    output_dir = Path(__file__).parent.parent / 'output' / 'images' / 'test'

    images = fetch_images_for_folklore([query], output_dir, count=10)

    print(f"\nDownloaded {len(images)} images:")
    for img_path in images:
        print(f"  - {img_path}")


if __name__ == '__main__':
    main()
