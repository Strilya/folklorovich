#!/usr/bin/env python3
"""
Folklorovich - Image Collage Creator
Creates 1080x1920 vertical image collages from multiple photos.

Features:
- 8 different layout templates
- Text overlays (title, subtitle, moral)
- Cyrillic font support
- Instagram-optimized dimensions

Author: Folklorovich Project
Date: 2025-12-05
"""

import os
import json
import logging
import random
from pathlib import Path
from typing import List, Optional, Dict, Tuple

from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageEnhance

# Configure logging
logger = logging.getLogger('CollageCreator')

# Instagram Reels dimensions
OUTPUT_WIDTH = 1080
OUTPUT_HEIGHT = 1920


class CollageCreator:
    """Creates image collages with various layouts."""

    def __init__(self, templates_path: Optional[Path] = None):
        """
        Initialize collage creator.

        Args:
            templates_path: Path to collage_layouts.json
        """
        if templates_path is None:
            project_root = Path(__file__).parent.parent
            templates_path = project_root / 'assets' / 'templates' / 'collage_layouts.json'

        self.templates_path = templates_path
        self.templates = self._load_templates()

        # Load fonts
        self.fonts_dir = Path(__file__).parent.parent / 'assets' / 'fonts'
        self.title_font = self._load_font('Philosopher-Regular.ttf', size=72)
        self.subtitle_font = self._load_font('Roboto-Regular.ttf', size=36)
        self.body_font = self._load_font('Roboto-Regular.ttf', size=28)

        logger.info("Collage creator initialized")

    def _load_templates(self) -> Dict:
        """Load collage layout templates from JSON."""
        try:
            with open(self.templates_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            logger.warning(f"Templates file not found: {self.templates_path}")
            return self._get_default_templates()
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON in templates: {e}")
            return self._get_default_templates()

    def _get_default_templates(self) -> Dict:
        """Return default templates if file not found."""
        return {
            "templates": [
                {
                    "name": "grid_4",
                    "description": "2x2 grid layout",
                    "image_count": 4,
                    "regions": [
                        {"x": 0, "y": 0, "width": 540, "height": 960},
                        {"x": 540, "y": 0, "width": 540, "height": 960},
                        {"x": 0, "y": 960, "width": 540, "height": 960},
                        {"x": 540, "y": 960, "width": 540, "height": 960}
                    ]
                }
            ]
        }

    def _load_font(self, font_name: str, size: int) -> ImageFont.FreeTypeFont:
        """
        Load a TrueType font.

        Args:
            font_name: Font filename
            size: Font size in points

        Returns:
            Loaded font or default font
        """
        font_path = self.fonts_dir / font_name

        try:
            if font_path.exists():
                return ImageFont.truetype(str(font_path), size)
            else:
                logger.warning(f"Font not found: {font_name}, using default")
                return ImageFont.load_default()
        except Exception as e:
            logger.error(f"Error loading font {font_name}: {e}")
            return ImageFont.load_default()

    def select_template(self, template_name: Optional[str] = None) -> Dict:
        """
        Select a collage template.

        Args:
            template_name: Specific template name, or None for random

        Returns:
            Template dictionary
        """
        templates_list = self.templates.get('templates', [])

        if not templates_list:
            raise ValueError("No templates available")

        if template_name:
            # Find specific template
            template = next((t for t in templates_list if t['name'] == template_name), None)
            if template:
                return template
            else:
                logger.warning(f"Template '{template_name}' not found, using random")

        # Select random template
        template = random.choice(templates_list)
        logger.info(f"Selected template: {template['name']}")
        return template

    def load_and_resize_image(self, image_path: Path, target_width: int,
                              target_height: int) -> Image.Image:
        """
        Load and resize image to fit region while maintaining aspect ratio.

        Uses 'cover' strategy: fills region completely, cropping if necessary.

        Args:
            image_path: Path to source image
            target_width: Target width
            target_height: Target height

        Returns:
            Resized PIL Image
        """
        img = Image.open(image_path)

        # Convert to RGB if needed
        if img.mode != 'RGB':
            img = img.convert('RGB')

        # Calculate scaling to cover the region
        img_aspect = img.width / img.height
        target_aspect = target_width / target_height

        if img_aspect > target_aspect:
            # Image is wider, scale by height
            new_height = target_height
            new_width = int(new_height * img_aspect)
        else:
            # Image is taller, scale by width
            new_width = target_width
            new_height = int(new_width / img_aspect)

        # Resize
        img_resized = img.resize((new_width, new_height), Image.Resampling.LANCZOS)

        # Crop to exact dimensions (center crop)
        left = (new_width - target_width) // 2
        top = (new_height - target_height) // 2
        img_cropped = img_resized.crop((left, top, left + target_width, top + target_height))

        return img_cropped

    def create_collage_from_template(self, image_paths: List[Path],
                                    template: Dict) -> Image.Image:
        """
        Create a collage using a specific template.

        Args:
            image_paths: List of source image paths
            template: Template dictionary with regions

        Returns:
            Collage as PIL Image
        """
        # Create blank canvas
        canvas = Image.new('RGB', (OUTPUT_WIDTH, OUTPUT_HEIGHT), color=(20, 20, 20))

        regions = template['regions']
        images_needed = len(regions)

        # Ensure we have enough images (repeat if necessary)
        if len(image_paths) < images_needed:
            logger.warning(f"Not enough images ({len(image_paths)}), repeating...")
            while len(image_paths) < images_needed:
                image_paths.extend(image_paths[:images_needed - len(image_paths)])

        # Place images in regions
        for idx, region in enumerate(regions):
            if idx >= len(image_paths):
                break

            # Load and resize image
            img = self.load_and_resize_image(
                image_paths[idx],
                target_width=region['width'],
                target_height=region['height']
            )

            # Optional: Apply subtle effects
            if random.random() < 0.3:  # 30% chance
                img = ImageEnhance.Contrast(img).enhance(1.1)

            # Paste onto canvas
            canvas.paste(img, (region['x'], region['y']))

        logger.info(f"Created collage with {len(regions)} images")
        return canvas

    def add_text_overlay(self, canvas: Image.Image, title: str,
                        subtitle: Optional[str] = None) -> Image.Image:
        """
        Add text overlays to the collage.

        Args:
            canvas: Base image
            title: Main title text
            subtitle: Optional subtitle text

        Returns:
            Image with text overlay
        """
        draw = ImageDraw.Draw(canvas)

        # Add semi-transparent overlay at top for better text visibility
        overlay = Image.new('RGBA', canvas.size, (0, 0, 0, 0))
        overlay_draw = ImageDraw.Draw(overlay)

        # Dark gradient at top
        for y in range(400):
            alpha = int(180 * (1 - y / 400))  # Fade from 180 to 0
            overlay_draw.rectangle([(0, y), (OUTPUT_WIDTH, y + 1)],
                                  fill=(0, 0, 0, alpha))

        canvas = canvas.convert('RGBA')
        canvas = Image.alpha_composite(canvas, overlay)
        canvas = canvas.convert('RGB')

        draw = ImageDraw.Draw(canvas)

        # Draw title (centered at top)
        title_bbox = draw.textbbox((0, 0), title, font=self.title_font)
        title_width = title_bbox[2] - title_bbox[0]
        title_x = (OUTPUT_WIDTH - title_width) // 2
        title_y = 100

        # Add text shadow for better readability
        shadow_offset = 3
        draw.text((title_x + shadow_offset, title_y + shadow_offset),
                 title, font=self.title_font, fill=(0, 0, 0))
        draw.text((title_x, title_y), title, font=self.title_font, fill=(255, 255, 255))

        # Draw subtitle if provided
        if subtitle:
            subtitle_bbox = draw.textbbox((0, 0), subtitle, font=self.subtitle_font)
            subtitle_width = subtitle_bbox[2] - subtitle_bbox[0]
            subtitle_x = (OUTPUT_WIDTH - subtitle_width) // 2
            subtitle_y = title_y + 100

            draw.text((subtitle_x + shadow_offset, subtitle_y + shadow_offset),
                     subtitle, font=self.subtitle_font, fill=(0, 0, 0))
            draw.text((subtitle_x, subtitle_y),
                     subtitle, font=self.subtitle_font, fill=(220, 220, 220))

        logger.info("Added text overlay")
        return canvas


def create_collage(image_paths: List[Path], output_path: Path,
                  title: str, subtitle: Optional[str] = None,
                  layout_name: Optional[str] = None) -> bool:
    """
    Convenience function to create a collage.

    Args:
        image_paths: List of source image paths
        output_path: Path to save output collage
        title: Main title text
        subtitle: Optional subtitle text
        layout_name: Specific layout name or None for random

    Returns:
        True if successful, False otherwise
    """
    try:
        creator = CollageCreator()

        # Select template
        template = creator.select_template(layout_name)

        # Create collage
        collage = creator.create_collage_from_template(image_paths, template)

        # Add text
        collage = creator.add_text_overlay(collage, title, subtitle)

        # Save
        output_path.parent.mkdir(parents=True, exist_ok=True)
        collage.save(output_path, 'PNG', quality=95)

        logger.info(f"✓ Collage saved to {output_path}")
        return True

    except Exception as e:
        logger.error(f"Failed to create collage: {e}", exc_info=True)
        return False


def main():
    """Test the collage creator."""
    import sys

    logging.basicConfig(level=logging.INFO)

    if len(sys.argv) < 3:
        print("Usage: python create_collage.py <image_dir> <output_path>")
        sys.exit(1)

    image_dir = Path(sys.argv[1])
    output_path = Path(sys.argv[2])

    # Find all images in directory
    image_paths = list(image_dir.glob('*.jpg')) + list(image_dir.glob('*.png'))

    if not image_paths:
        print(f"No images found in {image_dir}")
        sys.exit(1)

    success = create_collage(
        image_paths=image_paths,
        output_path=output_path,
        title="Домовой",
        subtitle="Хранитель дома"
    )

    sys.exit(0 if success else 1)


if __name__ == '__main__':
    main()
