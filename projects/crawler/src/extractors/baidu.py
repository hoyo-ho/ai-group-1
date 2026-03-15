# -*- coding: utf-8 -*-
"""
Baidu Search Results Extractor
"""
import re
from typing import Dict, List
from urllib.parse import urljoin
from bs4 import BeautifulSoup

from .base import BaseExtractor


class BaiduExtractor(BaseExtractor):
    """Baidu search results extractor"""
    
    priority = 70
    supported_domains = ["baidu.com", "www.baidu.com"]
    
    def extract(self, url: str, html: str) -> Dict:
        soup = BeautifulSoup(html, 'html.parser')
        
        # Extract search results
        results = self._extract_results(soup)
        
        # Extract search query
        query = self._extract_query(soup, url)
        
        # Extract related searches
        related = self._extract_related(soup)
        
        # Extract title
        title = self._extract_title(soup)
        
        return {
            "url": url,
            "title": title,
            "query": query,
            "results": results,
            "related_searches": related
        }
    
    def _extract_title(self, soup: BeautifulSoup) -> str:
        # Try title tag
        title_tag = soup.find("title")
        if title_tag:
            return title_tag.get_text(strip=True)
        
        # Try og:title
        og_title = soup.find("meta", property="og:title")
        if og_title:
            return og_title.get("content", "")
        
        return "Baidu Search"
    
    def _extract_query(self, soup: BeautifulSoup, url: str) -> str:
        # Extract from URL query parameter
        match = re.search(r'[?&]wd=([^&]+)', url)
        if match:
            from urllib.parse import unquote
            return unquote(match.group(1))
        
        match = re.search(r'[?&]word=([^&]+)', url)
        if match:
            from urllib.parse import unquote
            return unquote(match.group(1))
        
        # Try to find from input field
        input_elem = soup.find("input", id="kw") or soup.find("input", name="wd")
        if input_elem and input_elem.get("value"):
            return input_elem.get("value")
        
        return ""
    
    def _extract_results(self, soup: BeautifulSoup) -> List[Dict]:
        results = []
        
        # Method 1: Find result containers (new Baidu layout)
        for container in soup.find_all("div", class_="result"):
            result = self._parse_result_container(container)
            if result:
                results.append(result)
        
        # Method 2: Find result c-container (legacy layout)
        for container in soup.find_all("div", class_=re.compile(r"c-container")):
            result = self._parse_result_container(container)
            if result:
                results.append(result)
        
        # Method 3: Find result via h3 title pattern
        for h3 in soup.find_all("h3", class_="t"):
            a_tag = h3.find("a")
            if a_tag:
                url = a_tag.get("href", "")
                title = a_tag.get_text(strip=True)
                
                # Skip if already added
                if any(r.get("url") == url for r in results):
                    continue
                
                # Try to find description
                desc = ""
                parent = h3.find_parent(["div", "section"])
                if parent:
                    # Find the content after h3
                    for sibling in parent.find_next_siblings():
                        if sibling.name == "div":
                            cls = sibling.get("class", [])
                            if "c-abstract" in cls or "c-span18" in cls or "c-span-last" in cls:
                                desc = sibling.get_text(strip=True)
                                break
                            if sibling.find("h3"):  # Next result
                                break
                
                results.append({
                    "title": title,
                    "url": url,
                    "description": desc,
                    "source": "h3"
                })
        
        return results
    
    def _parse_result_container(self, container) -> Dict:
        """Parse a result container div"""
        result = {}
        
        # Find title (usually in h3)
        h3 = container.find("h3")
        if h3:
            a_tag = h3.find("a")
            if a_tag:
                result["title"] = a_tag.get_text(strip=True)
                result["url"] = a_tag.get("href", "")
        
        # Find description
        abstract = container.find("div", class_="c-abstract")
        if abstract:
            result["description"] = abstract.get_text(strip=True)
        else:
            # Try other patterns
            for cls in ["c-snippet", "c-content", "c-span18"]:
                elem = container.find("div", class_=cls)
                if elem:
                    result["description"] = elem.get_text(strip=True)
                    break
        
        # Find source/site
        source = container.find("cite")
        if source:
            result["source"] = source.get_text(strip=True)
        
        # Only return if we have essential data
        if result.get("title") and result.get("url"):
            return result
        
        return None
    
    def _extract_related(self, soup: BeautifulSoup) -> List[str]:
        related = []
        
        # Find related searches section
        for div in soup.find_all("div", id=re.compile(r"rs")):
            for a in div.find_all("a"):
                text = a.get_text(strip=True)
                if text and text not in related:
                    related.append(text)
        
        # Find from .op-recommend-* patterns
        for div in soup.find_all("div", class_=re.compile(r"op-recommend")):
            for a in div.find_all("a"):
                text = a.get_text(strip=True)
                if text and text not in related:
                    related.append(text)
        
        return related
