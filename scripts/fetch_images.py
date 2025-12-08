#!/usr/bin/env python3
"""
Folklorovich - Image Fetcher
FIXED: Always includes "Russia" or "Russian" in searches
"""

import os
import time
import logging
import requests
from pathlib import Path
from typing import List
import random

logger = logging.getLogger('ImageFetcher')


def enhance_keywords_with_russian(base_keywords: List[str]) -> str:
    """
    FORCE Russian context into every search.
    
    CRITICAL: Always start with "Russia" or "Russian" to avoid American content.
    """
    # Clean base keywords
    query_words = [w for w in base_keywords if w.lower() not in ['traditional', 'folk', 'art']]
    
    # ALWAYS start with Russia/Russian
    if not any(word.lower() in ['russia', 'russian'] for word in query_words):
        query_words.insert(0, "Russia")
    
    query = " ".join(query_words[:4])  # Max 4 words for better results
    
    logger.info(f"Search query: '{query}'")
    return query


class UnsplashImageFetcher:
    """Fetches images from Unsplash API."""
    
    def __init__(self, access_key: str = None):
        self.access_key = access_key or os.getenv('UNSPLASH_ACCESS_KEY')
        if not self.access_key:
            raise ValueError("UNSPLASH_ACCESS_KEY not found")
        
        self.api_base = "https://api.unsplash.com"
        self.session = requests.Session()
        self.session.headers.update({
            'Authorization': f'Client-ID {self.access_key}',
            'Accept-Version': 'v1'
        })
        
        self.max_retries = 3
        self.retry_delay = 5
    
    def search_photos(self, query: str, per_page: int = 5) -> List[dict]:
        """Search Unsplash for photos."""
        url = f"{self.api_base}/search/photos"
        params = {
            'query': query,
            'per_page': min(per_page, 30),
            'orientation': 'portrait',
            'content_filter': 'high'
        }
        
        for attempt in range(self.max_retries):
            try:
                response = self.session.get(url, params=params, timeout=10)
                
                if response.status_code == 429:
                    retry_after = int(response.headers.get('X-RateLimit-Reset', 60))
                    logger.warning(f"Rate limit hit. Waiting {min(retry_after, 60)}s")
                    time.sleep(min(retry_after, 60))
                    continue
                
                response.raise_for_status()
                data = response.json()
                results = data.get('results', [])
                
                logger.info(f"Found {len(results)} images")
                return results
            
            except requests.exceptions.RequestException as e:
                logger.error(f"Request failed: {e}")
                if attempt < self.max_retries - 1:
                    delay = self.retry_delay * (2 ** attempt)
                    logger.info(f"Retrying in {delay}s...")
                    time.sleep(delay)
        
        return []
    
    def download_image(self, url: str, output_path: Path) -> bool:
        """Download image from URL."""
        try:
            response = requests.get(url, timeout=30, stream=True)
            response.raise_for_status()
            
            with open(output_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            
            logger.info(f"Downloaded: {output_path.name}")
            return True
        
        except Exception as e:
            logger.error(f"Download failed: {e}")
            return False
    
    def fetch_images_for_tags(self, tags: List[str], output_dir: Path, count: int = 6) -> List[Path]:
        """Fetch images based on tags."""
        output_dir.mkdir(parents=True, exist_ok=True)
        downloaded_paths = []
        
        for query in tags:
            if len(downloaded_paths) >= count:
                break
            
            photos = self.search_photos(query, per_page=count - len(downloaded_paths))
            
            if not photos:
                logger.warning(f"No photos for '{query}'")
                continue
            
            for photo in photos:
                if len(downloaded_paths) >= count:
                    break
                
                image_url = photo['urls'].get('regular') or photo['urls'].get('full')
                if not image_url:
                    continue
                
                photo_id = photo['id']
                filename = f"unsplash_{photo_id}.jpg"
                output_path = output_dir / filename
                
                # Skip if cached
                if output_path.exists():
                    logger.info(f"Cached: {filename}")
                    downloaded_paths.append(output_path)
                    continue
                
                if self.download_image(image_url, output_path):
                    downloaded_paths.append(output_path)
                    time.sleep(2)  # Rate limiting
            
            if len(downloaded_paths) < count:
                time.sleep(5)
        
        logger.info(f"Total downloaded: {len(downloaded_paths)}/{count}")
        return downloaded_paths


def fetch_images_russian(keywords: str, num_images: int = 2) -> List[Path]:
    """
    Fetch Russian cultural images.
    
    CRITICAL FIX: Always includes "Russia" or "Russian" in search.
    """
    output_dir = Path("output/images")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    access_key = os.getenv("UNSPLASH_ACCESS_KEY")
    fetcher = UnsplashImageFetcher(access_key)
    
    # FORCE Russian context
    enhanced_query = enhance_keywords_with_russian(keywords.split())
    
    return fetcher.fetch_images_for_tags(
        tags=[enhanced_query],
        output_dir=output_dir,
        count=num_images
    )
