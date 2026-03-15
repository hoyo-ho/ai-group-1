# -*- coding: utf-8 -*-
"""
Crawler Configuration
"""
import os
from pathlib import Path

# Project paths
PROJECT_ROOT = Path(__file__).parent.parent
OUTPUT_DIR = Path.home() / "Downloads" / "crawler-output"
DOWNLOADS_DIR = Path.home() / "Downloads"

# Create output directory if not exists
OUTPUT_DIR.mkdir(exist_ok=True)
DOWNLOADS_DIR.mkdir(parents=True, exist_ok=True)

# Crawler settings
DEFAULT_TIMEOUT = 30
MAX_RETRIES = 3
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
DEFAULT_HEADERS = {
    "User-Agent": USER_AGENT,
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.5",
    "Connection": "keep-alive",
}

# Supported exporters
EXPORT_FORMATS = ["json", "csv", "markdown", "pdf", "png", "jpg"]
