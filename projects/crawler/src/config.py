# -*- coding: utf-8 -*-
"""
Crawler Configuration
"""
import os
from pathlib import Path

# Project paths
PROJECT_ROOT = Path(__file__).parent.parent
OUTPUT_DIR = Path.home() / "Downloads" / "crawler" / "output"
DOWNLOADS_DIR = Path.home() / "Downloads"

# Create output directory if not exists
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
DOWNLOADS_DIR.mkdir(parents=True, exist_ok=True)

# Crawler settings
DEFAULT_TIMEOUT = 60
MAX_RETRIES = 3
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
DEFAULT_HEADERS = {
    "User-Agent": USER_AGENT,
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.5",
    "Connection": "keep-alive",
}

# Proxy settings (Clash Verge)
PROXY_ENABLED = True
PROXY_HTTP = "http://127.0.0.1:7897"
PROXY_SOCKS5 = "socks5://127.0.0.1:7897"

# Supported exporters
EXPORT_FORMATS = ["json", "csv", "markdown", "pdf", "png", "jpg"]

# Zhihu cookies (from browser)
ZHIHU_COOKIES = {
    "BEC": "738c6d0432e7aaf738ea36855cdce904",
    "HMACCOUNT": "71196C39BDF04C3B",
    "SESSIONID": "20UWwzA1asLnd9g4OWcjSr8lRpmmPfTD2q8YH5JdI98",
    "_xsrf": "odX5W01ghbrtWlBLrR7FcUVp2f0RFGdK",
    "_zap": "5c26cc6b-7b10-4c69-a430-2136ba06badf",
    "z_c0": "2|1:0|10:1773566075|4:z_c0|92:Mi4xaUZTNnFRQUFBQURPa3hOTFdXeFlHeGNBQUFCZ0FsVk5lOGFqYWdBNlpTcmRId25DRDBYdi1QN09tS01hQ0wxU21R|fa02eb04b7ee75feba9b4dc595079f6f64d490d909a09f54de015cdd8b43d15a",
    "q_c1": "bfc24df4ed8c495e9bd9357f38e97d8c|1762570475000|1762570475000",
}

# Baidu cookies
BAIDU_COOKIES = {
    "BDUSS": "3dpUURFWmlNUU45Tm8yQzBBcTUzR3g1c2I0dk01cmJtYlFBd05uflluMHlxQjFwSVFBQUFBJCQAAAAAAQAAAAEAAAAwIdmEcHJpbmNlTmF5dXRvAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAADIb9mgyG~Zob",
}
