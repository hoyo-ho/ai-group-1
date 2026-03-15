# -*- coding: utf-8 -*-
"""
Crawler Core with Playwright Support
"""
import time
import random
from typing import Dict, List, Optional
from urllib.parse import urlparse
import requests

from .config import DEFAULT_TIMEOUT, MAX_RETRIES, DEFAULT_HEADERS, PROXY_ENABLED, PROXY_HTTP, PROXY_SOCKS5, ZHIHU_COOKIES, BAIDU_COOKIES
from .extractors import get_extractor, get_extractor_for_playwright
from .exporters import export_content

# Sites that block proxy connections - need to crawl without proxy
NO_PROXY_DOMAINS = [
    "csdn.net",
    "juejin.cn",
    "segmentfault.com",
]


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
        self.playwright_sync = None
        self.stealth_instance = None
        
        # Apply cookies for specific sites
        self._apply_cookies()
    
    def _apply_cookies(self):
        """Apply cookies for known sites"""
        # Apply Zhihu cookies
        for name, value in ZHIHU_COOKIES.items():
            self.session.cookies.set(name, value, domain=".zhihu.com")
        
        # Apply Baidu cookies
        for name, value in BAIDU_COOKIES.items():
            self.session.cookies.set(name, value, domain=".baidu.com")
    
    def _use_proxy(self, url: str) -> bool:
        """Check if we should use proxy for this URL"""
        parsed = urlparse(url)
        domain = parsed.netloc.lower()
        # Don't use proxy for sites that block it
        for no_proxy in NO_PROXY_DOMAINS:
            if no_proxy in domain:
                return False
        return PROXY_ENABLED
    
    def _init_playwright(self, stealth: bool = True):
        """Initialize Playwright browser with optional stealth mode"""
        if self.playwright_browser is None:
            from playwright.sync_api import sync_playwright
            self.playwright_sync = sync_playwright().start()
            
            # Configure proxy for Playwright
            launch_options = {
                "headless": True,
                "args": ["--disable-blink-features=AutomationControlled"]
            }
            
            if PROXY_ENABLED:
                # For now, we'll disable proxy globally and handle per-site
                # If we need proxy, uncomment below:
                # launch_options["proxy"] = {"server": PROXY_HTTP}
                pass
            
            self.playwright_browser = self.playwright_sync.chromium.launch(**launch_options)
            
            # Apply stealth mode if requested
            if stealth:
                try:
                    from playwright_stealth.stealth import Stealth
                    self.stealth_instance = Stealth()
                except ImportError:
                    print("Warning: playwright_stealth not installed, continuing without stealth mode")
                except Exception as e:
                    print(f"Warning: Failed to initialize stealth mode: {e}")
                    
        return self.playwright_browser
    
    def _needs_playwright(self, url: str, html: str, status_code: int = 200) -> bool:
        """Check if we should use Playwright for this URL"""
        # Check if explicitly requested
        if self.use_playwright:
            return True
        
        # Check site_type
        if self.site_type in ["douyin", "csdn", "juejin"]:
            return True
        
        # Check if URL is in known dynamic sites
        if self._should_use_playwright(url):
            return True
        
        # Check for 521 status (CSDN bot detection)
        if status_code == 521:
            return True
        
        # Check if HTML is empty or very small (possible JavaScript rendering needed)
        if not html or len(html) < 1000:
            return True
        
        # Check if HTML suggests JavaScript rendering is needed
        if self._needs_javascript(url, html):
            return True
        
        return False
    
    def crawl(self, url: str) -> Dict:
        """Crawl a URL and extract content"""
        # Try requests first, then playwright if needed
        html, status_code = self._fetch(url)
        
        # Check if we should use playwright
        if self._needs_playwright(url, html, status_code):
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
            # Anti-crawl sites that need stealth browser
            "csdn.net",
            "juejin.cn",
            "segmentfault.com",
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
            browser = self._init_playwright(stealth=True)
            context = browser.new_context(
                viewport={'width': 1920, 'height': 1080},
                user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
            )
            page = context.new_page()
            
            # Apply stealth if available
            if self.stealth_instance:
                self.stealth_instance.apply_stealth_sync(page)
            
            # Add random delay before navigation to mimic human behavior
            time.sleep(random.uniform(0.5, 2.0))
            
            # Navigate to the URL
            page.goto(url, timeout=self.timeout * 1000, wait_until="domcontentloaded")
            
            # Wait for network to be idle (with longer timeout for slow sites)
            try:
                page.wait_for_load_state("networkidle", timeout=30000)
            except Exception:
                # Some sites never fully settle, continue anyway
                pass
            
            # Additional wait for dynamic content
            time.sleep(random.uniform(1.0, 3.0))
            
            html = page.content()
            page.close()
            context.close()
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
    
    def _fetch(self, url: str):
        """Fetch HTML content from URL"""
        # For sites that block proxy, temporarily disable it
        use_proxy = self._use_proxy(url)
        original_proxies = self.session.proxies
        
        if not use_proxy:
            self.session.proxies = None
        
        try:
            for attempt in range(self.max_retries):
                try:
                    response = self.session.get(url, timeout=self.timeout)
                    # Return both HTML and status code
                    return response.text, response.status_code
                except requests.exceptions.RequestException as e:
                    if attempt < self.max_retries - 1:
                        time.sleep(1 * (attempt + 1))
                        continue
                    print(f"Failed to fetch {url}: {e}")
                    return None, 0
            
            return None, 0
        finally:
            # Restore proxies
            self.session.proxies = original_proxies
    
    def close(self):
        """Close the session and browser"""
        self.session.close()
        if self.playwright_browser:
            self.playwright_browser.close()
            if self.playwright_sync:
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
