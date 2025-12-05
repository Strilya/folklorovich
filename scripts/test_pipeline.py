#!/usr/bin/env python3
"""
Folklorovich - Comprehensive Testing Suite
Tests all components of the content generation pipeline.

Author: Folklorovich Project
Date: 2025-12-05
"""

import os
import sys
import json
import time
from pathlib import Path
from typing import List, Dict, Tuple

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from scripts.utils import setup_logging, validate_image, validate_audio, validate_video

# Initialize logging
logger = setup_logging('test_pipeline', level='INFO')


class PipelineTester:
    """Comprehensive testing suite for Folklorovich."""

    def __init__(self):
        """Initialize tester."""
        self.project_root = PROJECT_ROOT
        self.content_dir = self.project_root / 'content'
        self.output_dir = self.project_root / 'output'
        self.scripts_dir = self.project_root / 'scripts'

        self.tests_passed = 0
        self.tests_failed = 0
        self.test_results = []

    def log_test(self, test_name: str, passed: bool, message: str = ""):
        """Log test result."""
        status = "✅ PASS" if passed else "❌ FAIL"
        logger.info(f"{status}: {test_name}")
        if message:
            logger.info(f"    {message}")

        self.test_results.append({
            'test': test_name,
            'passed': passed,
            'message': message
        })

        if passed:
            self.tests_passed += 1
        else:
            self.tests_failed += 1

    def test_project_structure(self) -> bool:
        """Test 1: Verify project structure."""
        logger.info("\n" + "="*60)
        logger.info("TEST 1: Project Structure")
        logger.info("="*60)

        required_dirs = [
            'content',
            'scripts',
            'assets/templates',
            'assets/fonts',
            'output/images',
            'output/audio',
            'output/videos',
            'logs'
        ]

        all_exist = True
        for dir_path in required_dirs:
            full_path = self.project_root / dir_path
            exists = full_path.exists()
            self.log_test(f"Directory exists: {dir_path}", exists)
            if not exists:
                all_exist = False

        return all_exist

    def test_configuration_files(self) -> bool:
        """Test 2: Verify configuration files."""
        logger.info("\n" + "="*60)
        logger.info("TEST 2: Configuration Files")
        logger.info("="*60)

        all_valid = True

        # Test folklore database
        db_path = self.content_dir / 'folklore_database.json'
        try:
            with open(db_path, 'r') as f:
                db_data = json.load(f)

            folklore_count = len(db_data.get('folklore', []))
            expected_count = 75

            self.log_test(
                "Folklore database valid",
                folklore_count == expected_count,
                f"Found {folklore_count} entries (expected {expected_count})"
            )

            if folklore_count != expected_count:
                all_valid = False

            # Check first entry structure
            if db_data.get('folklore'):
                entry = db_data['folklore'][0]
                required_keys = ['id', 'name', 'category', 'story_full', 'visual_tags', 'voice_tone', 'theme']

                for key in required_keys:
                    has_key = key in entry
                    self.log_test(f"Entry has '{key}' field", has_key)
                    if not has_key:
                        all_valid = False

        except Exception as e:
            self.log_test("Folklore database readable", False, str(e))
            all_valid = False

        # Test metadata
        meta_path = self.content_dir / 'metadata.json'
        try:
            with open(meta_path, 'r') as f:
                meta_data = json.load(f)

            required_sections = ['project_info', 'content_rotation', 'generation_history', 'statistics']
            for section in required_sections:
                has_section = section in meta_data
                self.log_test(f"Metadata has '{section}' section", has_section)
                if not has_section:
                    all_valid = False

        except Exception as e:
            self.log_test("Metadata readable", False, str(e))
            all_valid = False

        # Test collage templates
        templates_path = self.project_root / 'assets/templates/collage_layouts.json'
        try:
            with open(templates_path, 'r') as f:
                templates_data = json.load(f)

            template_count = len(templates_data.get('templates', []))
            self.log_test(
                "Collage templates valid",
                template_count >= 8,
                f"Found {template_count} templates"
            )

            if template_count < 8:
                all_valid = False

        except Exception as e:
            self.log_test("Collage templates readable", False, str(e))
            all_valid = False

        return all_valid

    def test_dependencies(self) -> bool:
        """Test 3: Check system dependencies."""
        logger.info("\n" + "="*60)
        logger.info("TEST 3: System Dependencies")
        logger.info("="*60)

        all_installed = True

        # Test Python packages
        packages = [
            'requests',
            'PIL',
            'edge_tts',
            'dotenv'
        ]

        for package in packages:
            try:
                __import__(package)
                self.log_test(f"Python package: {package}", True)
            except ImportError as e:
                self.log_test(f"Python package: {package}", False, str(e))
                all_installed = False

        # Test FFmpeg
        import subprocess
        try:
            result = subprocess.run(['ffmpeg', '-version'], capture_output=True, timeout=5)
            ffmpeg_works = result.returncode == 0
            self.log_test("FFmpeg installed", ffmpeg_works)
            if not ffmpeg_works:
                all_installed = False
        except Exception as e:
            self.log_test("FFmpeg installed", False, str(e))
            all_installed = False

        # Test FFprobe
        try:
            result = subprocess.run(['ffprobe', '-version'], capture_output=True, timeout=5)
            ffprobe_works = result.returncode == 0
            self.log_test("FFprobe installed", ffprobe_works)
            if not ffprobe_works:
                all_installed = False
        except Exception as e:
            self.log_test("FFprobe installed", False, str(e))
            all_installed = False

        return all_installed

    def test_script_imports(self) -> bool:
        """Test 4: Verify all scripts can be imported."""
        logger.info("\n" + "="*60)
        logger.info("TEST 4: Script Imports")
        logger.info("="*60)

        all_importable = True

        scripts = [
            'utils',
            'fetch_images',
            'create_collage',
            'generate_voice',
            'render_video',
            'generate_daily_content_v2'
        ]

        for script in scripts:
            try:
                __import__(f'scripts.{script}')
                self.log_test(f"Import: scripts/{script}.py", True)
            except Exception as e:
                self.log_test(f"Import: scripts/{script}.py", False, str(e))
                all_importable = False

        return all_importable

    def test_folklore_categories(self) -> bool:
        """Test 5: Verify folklore category distribution."""
        logger.info("\n" + "="*60)
        logger.info("TEST 5: Folklore Categories")
        logger.info("="*60)

        try:
            with open(self.content_dir / 'folklore_database.json', 'r') as f:
                db_data = json.load(f)

            categories = {}
            for entry in db_data.get('folklore', []):
                cat = entry.get('category', 'unknown')
                categories[cat] = categories.get(cat, 0) + 1

            expected = {
                'household_spirits': 15,
                'mythical_creatures': 15,
                'superstitions': 15,
                'rituals_traditions': 10,
                'curses_omens': 10,
                'folk_heroes': 10
            }

            all_correct = True
            for cat, expected_count in expected.items():
                actual_count = categories.get(cat, 0)
                is_correct = actual_count == expected_count

                self.log_test(
                    f"Category '{cat}'",
                    is_correct,
                    f"{actual_count}/{expected_count} entries"
                )

                if not is_correct:
                    all_correct = False

            return all_correct

        except Exception as e:
            self.log_test("Category distribution check", False, str(e))
            return False

    def test_env_variables(self) -> bool:
        """Test 6: Check environment variables."""
        logger.info("\n" + "="*60)
        logger.info("TEST 6: Environment Variables")
        logger.info("="*60)

        from dotenv import load_dotenv
        load_dotenv(self.project_root / '.env')

        # Check if .env file exists
        env_file = self.project_root / '.env'
        env_exists = env_file.exists()

        if not env_exists:
            # Check template
            template_file = self.project_root / '.env.template'
            self.log_test(
                "Environment configuration",
                template_file.exists(),
                ".env not found, but .env.template exists"
            )
            return False

        self.log_test("Environment file exists", True, ".env file found")

        # Check for required keys (don't log values for security)
        has_unsplash = os.getenv('UNSPLASH_ACCESS_KEY') is not None
        self.log_test(
            "UNSPLASH_ACCESS_KEY configured",
            has_unsplash,
            "Required for image fetching" if not has_unsplash else "Configured"
        )

        return env_exists and has_unsplash

    def test_utility_functions(self) -> bool:
        """Test 7: Test utility functions."""
        logger.info("\n" + "="*60)
        logger.info("TEST 7: Utility Functions")
        logger.info("="*60)

        all_working = True

        # Test logging setup
        try:
            from scripts.utils import setup_logging
            test_logger = setup_logging('test', level='INFO')
            self.log_test("Logging setup works", test_logger is not None)
        except Exception as e:
            self.log_test("Logging setup works", False, str(e))
            all_working = False

        # Test validation functions exist
        try:
            from scripts.utils import validate_image, validate_audio, validate_video
            self.log_test("Validation functions importable", True)
        except Exception as e:
            self.log_test("Validation functions importable", False, str(e))
            all_working = False

        # Test API tracking
        try:
            from scripts.utils import track_api_usage
            track_api_usage('test_api', 'test_call')

            usage_file = self.project_root / 'logs/api_usage.json'
            self.log_test("API usage tracking works", usage_file.exists())
        except Exception as e:
            self.log_test("API usage tracking works", False, str(e))
            all_working = False

        return all_working

    def test_cycle_rotation(self) -> bool:
        """Test 8: Test content rotation logic."""
        logger.info("\n" + "="*60)
        logger.info("TEST 8: Content Rotation")
        logger.info("="*60)

        try:
            with open(self.content_dir / 'metadata.json', 'r') as f:
                metadata = json.load(f)

            rotation = metadata.get('content_rotation', {})

            # Check required fields
            has_cycle = 'current_cycle' in rotation
            has_order = 'cycle_order' in rotation
            has_used = 'used_ids_this_cycle' in rotation

            self.log_test("Rotation has 'current_cycle'", has_cycle)
            self.log_test("Rotation has 'cycle_order'", has_order)
            self.log_test("Rotation has 'used_ids_this_cycle'", has_used)

            return has_cycle and has_order and has_used

        except Exception as e:
            self.log_test("Content rotation structure", False, str(e))
            return False

    def generate_test_report(self):
        """Generate final test report."""
        logger.info("\n" + "="*60)
        logger.info("TEST SUMMARY")
        logger.info("="*60)

        total_tests = self.tests_passed + self.tests_failed
        pass_rate = (self.tests_passed / total_tests * 100) if total_tests > 0 else 0

        logger.info(f"Total Tests: {total_tests}")
        logger.info(f"Passed: {self.tests_passed} ✅")
        logger.info(f"Failed: {self.tests_failed} ❌")
        logger.info(f"Pass Rate: {pass_rate:.1f}%")
        logger.info("="*60)

        if self.tests_failed > 0:
            logger.info("\nFailed Tests:")
            for result in self.test_results:
                if not result['passed']:
                    logger.info(f"  ❌ {result['test']}")
                    if result['message']:
                        logger.info(f"     {result['message']}")

        # Save report to file
        report_path = self.project_root / 'logs/test_report.json'
        report_path.parent.mkdir(parents=True, exist_ok=True)

        with open(report_path, 'w') as f:
            json.dump({
                'timestamp': time.strftime('%Y-%m-%d %H:%M:%S'),
                'total_tests': total_tests,
                'passed': self.tests_passed,
                'failed': self.tests_failed,
                'pass_rate': pass_rate,
                'results': self.test_results
            }, f, indent=2)

        logger.info(f"\n📄 Full report saved to: {report_path}")

        return self.tests_failed == 0

    def run_all_tests(self) -> bool:
        """Run all tests."""
        logger.info("🧪 Starting Folklorovich Test Suite...")
        logger.info(f"📁 Project Root: {self.project_root}")

        start_time = time.time()

        # Run all tests
        self.test_project_structure()
        self.test_configuration_files()
        self.test_dependencies()
        self.test_script_imports()
        self.test_folklore_categories()
        self.test_env_variables()
        self.test_utility_functions()
        self.test_cycle_rotation()

        # Generate report
        elapsed = time.time() - start_time
        logger.info(f"\n⏱️  Tests completed in {elapsed:.2f} seconds")

        all_passed = self.generate_test_report()

        if all_passed:
            logger.info("\n🎉 ALL TESTS PASSED! System is ready for production.")
        else:
            logger.warning("\n⚠️  Some tests failed. Please fix issues before deployment.")

        return all_passed


def main():
    """Main entry point."""
    tester = PipelineTester()
    success = tester.run_all_tests()
    sys.exit(0 if success else 1)


if __name__ == '__main__':
    main()
