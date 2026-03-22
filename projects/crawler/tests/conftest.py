# -*- coding: utf-8 -*-
"""Pytest configuration and fixtures"""
import pytest
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))


@pytest.fixture
def sample_data():
    """Sample data for testing"""
    return {
        "url": "https://example.com",
        "title": "Example Domain",
        "content": "This is an example content.",
        "meta": {
            "author": "Test Author",
            "description": "Test description"
        },
        "images": [
            {"src": "https://example.com/image1.jpg", "alt": "Image 1"},
            {"src": "https://example.com/image2.jpg", "alt": "Image 2"}
        ]
    }


@pytest.fixture
def tmp_output_dir(tmp_path):
    """Temporary output directory"""
    output_dir = tmp_path / "output"
    output_dir.mkdir()
    return output_dir
