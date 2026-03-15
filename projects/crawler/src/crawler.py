# -*- coding: utf-8 -*-
"""
Crawler Core
"""
import time
from typing import Dict, List, Optional
from urllib.parse import urlparse
import requests

from .config import DEFAULT_TIMEOUT, MAX_RETRIES, USER_AGENT
from .extractors import get_extractor
from .exporters import export_content


class Crawler:
    """Web Crawler"""
    
    def __init__(self, timeout: int = DEFAULT_TIMEOUT, max_retries: int = MAX_RETRIES):
        self.timeout = timeout
        self.max_retries = max_retries
        self.session = requests.Session()
        self.session.headers.update({"User-Agent": USER_AGENT})
    
    def crawl(self, url: str) -> Dict:
        """Crawl a URL and extract content"""
        # Fetch HTML
        html = self._fetch(url)
        
        if not html:
            return {"error": "Failed to fetch URL", "url": url}
        
        # Get appropriate extractor
        extractor = get_extractor(url)
        
        # Extract content
        content = extractor.extract(url, html)
        
        return content
    
    def crawl_and_export(self, url: str, formats: List[str], filename: str = None, output_dir = None) -> Dict:
        """Crawl URL and export to specified formats"""
        # Crawl content
        content = self.crawl(url)
        
        if "error" in content:
            return content
        
        # Export to formats
        results = export_content(content, formats, filename, output_dir)
        
        return {
            "url": url,
            "content": content,
            "exports": results
        }
    
    def _fetch(self, url: str) -> Optional[str]:
        """Fetch HTML content from URL"""
        for attempt in range(self.max_retries):
            try:
                response = self.session.get(url, timeout=self.timeout)
                response.raise_for_status()
                return response.text
            except requests.exceptions.RequestException as e:
                if attempt < self.max_retries - 1:
                    time.sleep(1 * (attempt + 1))
                    continue
                print(f"Failed to fetch {url}: {e}")
                return None
        
        return None
    
    def close(self):
        """Close the session"""
        self.session.close()


def crawl(url: str, formats: List[str] = None, filename: str = None, output_dir = None) -> Dict:
    """Convenience function to crawl a URL"""
    if formats is None:
        formats = ["json"]
    
    crawler = Crawler()
    try:
        result = crawler.crawl_and_export(url, formats, filename, output_dir)
        return result
    finally:
        crawler.close()
