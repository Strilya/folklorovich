#!/usr/bin/env python3
import os
import requests
import logging
from pathlib import Path
from typing import List
from dotenv import load_dotenv
import random
import time

load_dotenv()
logger = logging.getLogger('VideoFetcher')

PEXELS_API_KEY = os.getenv('PEXELS_API_KEY')
PIXABAY_API_KEY = os.getenv('PIXABAY_API_KEY')


def fetch_pexels_videos(query: str, num: int = 10) -> List[str]:
    if not PEXELS_API_KEY:
        return []
    
    try:
        response = requests.get(
            "https://api.pexels.com/videos/search",
            headers={"Authorization": PEXELS_API_KEY},
            params={"query": query, "per_page": num, "orientation": "portrait"},
            timeout=10
        )
        response.raise_for_status()
        
        urls = []
        for video in response.json().get('videos', []):
            for file in video.get('video_files', []):
                if file.get('height', 0) > file.get('width', 0):
                    urls.append(file['link'])
                    break
        
        logger.info(f"Pexels '{query}': {len(urls)}")
        return urls
    except:
        return []


def fetch_pixabay_videos(query: str, num: int = 10) -> List[str]:
    if not PIXABAY_API_KEY:
        return []
    
    try:
        response = requests.get(
            "https://pixabay.com/api/videos/",
            params={"key": PIXABAY_API_KEY, "q": query, "per_page": num},
            timeout=10
        )
        response.raise_for_status()
        
        urls = []
        for hit in response.json().get('hits', []):
            videos = hit.get('videos', {})
            if 'medium' in videos:
                urls.append(videos['medium']['url'])
        
        logger.info(f"Pixabay '{query}': {len(urls)}")
        return urls
    except:
        return []


def download_videos(urls: List[str], output_dir: Path) -> List[Path]:
    output_dir.mkdir(parents=True, exist_ok=True)
    downloaded = []
    
    for idx, url in enumerate(urls):
        try:
            path = output_dir / f"clip_{idx:02d}.mp4"
            if path.exists():
                downloaded.append(path)
                continue
            
            r = requests.get(url, timeout=30, stream=True)
            r.raise_for_status()
            
            with open(path, 'wb') as f:
                for chunk in r.iter_content(8192):
                    f.write(chunk)
            
            downloaded.append(path)
        except:
            pass
    
    return downloaded


def fetch_russian_videos(keywords: str, num_videos: int = 10) -> List[Path]:
    # Use FIRST 2 words only
    primary = " ".join(keywords.split()[:2])
    logger.info(f"Searching: '{primary}'")
    
    # Get from both
    urls = fetch_pexels_videos(primary, num_videos // 2)
    urls += fetch_pixabay_videos(primary, num_videos // 2)
    
    random.shuffle(urls)
    
    if not urls:
        return []
    
    # Download
    temp_dir = Path(__file__).parent.parent / "output" / f"vtemp_{int(time.time()*1000)}"
    return download_videos(urls[:num_videos], temp_dir)
