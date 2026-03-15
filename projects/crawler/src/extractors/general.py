# -*- coding: utf-8 -*-
"""
General Web Page Extractor
"""
from typing import Dict, List
from urllib.parse import urljoin
from bs4 import BeautifulSoup

from .base import BaseExtractor


class GeneralExtractor(BaseExtractor):
    """General web page extractor"""
    
    priority = 10
    supported_domains = []  # Default fallback
    
    def extract(self, url: str, html: str) -> Dict:
        soup = BeautifulSoup(html, 'html.parser')
        
        # Remove script and style elements
        for script in soup(["script", "style", "nav", "footer", "header"]):
            script.decompose()
        
        # Extract title
        title = self._extract_title(soup)
        
        # Extract main content
        content = self._extract_content(soup)
        
        # Extract images
        images = self._extract_images(soup, url)
        
        # Extract meta info
        meta = self._extract_meta(soup)
        
        return {
            "url": url,
            "title": title,
            "content": content,
            "images": images,
            "meta": meta
        }
    
    def _extract_title(self, soup: BeautifulSoup) -> str:
        # Try og:title first
        og_title = soup.find("meta", property="og:title")
        if og_title:
            return og_title.get("content", "")
        
        # Try h1
        h1 = soup.find("h1")
        if h1:
            return h1.get_text(strip=True)
        
        # Try title tag
        title = soup.find("title")
        if title:
            return title.get_text(strip=True)
        
        return ""
    
    def _extract_content(self, soup: BeautifulSoup) -> str:
        # Try article tag
        article = soup.find("article")
        if article:
            return article.get_text(separator="\n", strip=True)
        
        # Try main tag
        main = soup.find("main")
        if main:
            return main.get_text(separator="\n", strip=True)
        
        # Try common content class names
        for cls in ["content", "article", "post", "entry", "main-content"]:
            elem = soup.find(class_=cls)
            if elem:
                return elem.get_text(separator="\n", strip=True)
        
        # Fallback to body
        body = soup.find("body")
        if body:
            return body.get_text(separator="\n", strip=True)
        
        return ""
    
    def _extract_images(self, soup: BeautifulSoup, base_url: str) -> List[Dict]:
        images = []
        for img in soup.find_all("img"):
            src = img.get("src") or img.get("data-src") or img.get("data-lazy")
            if src:
                full_url = urljoin(base_url, src)
                alt = img.get("alt", "")
                images.append({
                    "url": full_url,
                    "alt": alt
                })
        return images
    
    def _extract_meta(self, soup: BeautifulSoup) -> Dict:
        meta = {}
        
        # Description
        desc = soup.find("meta", attrs={"name": "description"})
        if desc:
            meta["description"] = desc.get("content", "")
        
        og_desc = soup.find("meta", property="og:description")
        if og_desc:
            meta["og_description"] = og_desc.get("content", "")
        
        # Author
        author = soup.find("meta", attrs={"name": "author"})
        if author:
            meta["author"] = author.get("content", "")
        
        # Published time
        pub_time = soup.find("meta", property="article:published_time")
        if pub_time:
            meta["published_time"] = pub_time.get("content", "")
        
        return meta
