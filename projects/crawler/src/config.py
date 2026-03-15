# -*- coding: utf-8 -*-
"""
Crawler Configuration
"""
import os
from pathlib import Path

# Project paths
PROJECT_ROOT = Path(__file__).parent.parent
OUTPUT_DIR = PROJECT_ROOT / "output"
DOWNLOADS_DIR = Path.home() / "Downloads"

# Create output directory if not exists
OUTPUT_DIR.mkdir(exist_ok=True)
DOWNLOADS_DIR.mkdir(parents=True, exist_ok=True)

# Crawler settings
DEFAULT_TIMEOUT = 30
MAX_RETRIES = 3
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"

# Supported exporters
EXPORT_FORMATS = ["json", "csv", "markdown", "pdf", "png", "jpg"]
