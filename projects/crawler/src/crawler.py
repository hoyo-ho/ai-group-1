# -*- coding: utf-8 -*-
"""
Crawler Core with Playwright Support
"""
import time
from typing import Dict, List, Optional
from urllib.parse import urlparse
import requests

from .config import DEFAULT_TIMEOUT, MAX_RETRIES, DEFAULT_HEADERS, PROXY_ENABLED, PROXY_HTTP, PROXY_SOCKS5
from .extractors import get_extractor, get_extractor_for_playwright
from .exporters import export_content


class Crawler:
    """Web Crawler with optional JavaScript rendering"""
    
    def __init__(self, timeout: int = DEFAULT_TIMEOUT, max_retries: int = MAX_RETRIES, use_playwright: bool = False, site_type: str = None):
        self.timeout = timeout
        self.max_retries = max_retries
        self.use_playwright = use_playwright
        self.site_type = site_type
        self.session = requests.Session()
        self.session.headers.update(DEFAULT_HEADERS)
        
        # Configure proxy
        if PROXY_ENABLED:
            self.session.proxies = {
                "http": PROXY_HTTP,
                "https": PROXY_HTTP,
            }
        
        self.playwright_browser = None
    
    def _init_playwright(self):
        """Initialize Playwright browser"""
        if self.playwright_browser is None:
            from playwright.sync_api import sync_playwright
            self.playwright_sync = sync_playwright().start()
            
            # Configure proxy for Playwright
            launch_options = {"headless": True}
            if PROXY_ENABLED:
                launch_options["proxy"] = {
                    "server": PROXY_HTTP,
                }
            
            self.playwright_browser = self.playwright_sync.chromium.launch(**launch_options)
        return self.playwright_browser
    
    def crawl(self, url: str) -> Dict:
        """Crawl a URL and extract content"""
        # Try requests first, then playwright if needed
        html = self._fetch(url)
        
        # Check if we should use playwright based on extractor requirements
        needs_playwright = self.use_playwright or self._should_use_playwright(url)
        if self.site_type == "douyin":
            needs_playwright = True
        
        if not html or self._needs_javascript(url, html):
            if needs_playwright:
                html = self._fetch_with_playwright(url)
        
        if not html:
            return {"error": "Failed to fetch URL", "url": url}
        
        # Get appropriate extractor (with optional site_type hint)
        extractor = get_extractor(url, self.site_type)
        
        # Extract content
        content = extractor.extract(url, html)
        
        return content
    
    def _should_use_playwright(self, url: str) -> bool:
        """Check if URL likely needs JavaScript rendering"""
        # Known dynamic sites
        dynamic_domains = [
            "bilibili.com",
            "douyin.com",
            "weibo.com",
            "twitter.com",
            "x.com",
            "facebook.com",
            "instagram.com",
            "reddit.com",
            "taobao.com",
            "jd.com",
            "tmall.com",
        ]
        parsed = urlparse(url)
        return any(domain in parsed.netloc.lower() for domain in dynamic_domains)
    
    def _needs_javascript(self, url: str, html: str) -> bool:
        """Check if HTML suggests JavaScript rendering is needed"""
        # Check for common JavaScript indicators
        js_indicators = [
            '<script',
            'JavaScript is not available',
            'window.__INITIAL_STATE__',
            'window.__PRELOAD_STATE__',
        ]
        return any(indicator in html for indicator in js_indicators)
    
    def _fetch_with_playwright(self, url: str) -> Optional[str]:
        """Fetch HTML using Playwright (for JavaScript-rendered pages)"""
        try:
            browser = self._init_playwright()
            page = browser.new_page()
            page.goto(url, timeout=self.timeout * 1000)
            # Wait for network to be idle
            page.wait_for_load_state("networkidle", timeout=30000)
            html = page.content()
            page.close()
            return html
        except Exception as e:
            print(f"Playwright failed to fetch {url}: {e}")
            return None
    
    def crawl_and_export(self, url: str, formats: List[str], filename: str = None, output_dir = None, use_playwright: bool = False, site_type: str = None) -> Dict:
        """Crawl URL and export to specified formats"""
        # Temporarily enable playwright if requested
        original_playwright = self.use_playwright
        original_site_type = self.site_type
        
        if use_playwright:
            self.use_playwright = True
        if site_type:
            self.site_type = site_type
        
        # Crawl content
        content = self.crawl(url)
        
        # Restore original settings
        self.use_playwright = original_playwright
        self.site_type = original_site_type
        
        if "error" in content:
            return content
        
        # Export to formats
        results = export_content(content, formats, filename, output_dir, source_url=url)
        
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
        """Close the session and browser"""
        self.session.close()
        if self.playwright_browser:
            self.playwright_browser.close()
            self.playwright_sync.stop()


def crawl(url: str, formats: List[str] = None, filename: str = None, output_dir = None, use_playwright: bool = False, site_type: str = None) -> Dict:
    """Convenience function to crawl a URL"""
    if formats is None:
        formats = ["json"]
    
    crawler = Crawler(use_playwright=use_playwright, site_type=site_type)
    try:
        result = crawler.crawl_and_export(url, formats, filename, output_dir, use_playwright=use_playwright, site_type=site_type)
        return result
    finally:
        crawler.close()
