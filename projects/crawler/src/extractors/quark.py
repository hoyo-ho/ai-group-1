# -*- coding: utf-8 -*-
"""
Quark (夸克) Search Extractor
"""
import re
from typing import Dict, List
from urllib.parse import urljoin, urlparse, parse_qs
from bs4 import BeautifulSoup

from .base import BaseExtractor


class QuarkExtractor(BaseExtractor):
    """Quark search results extractor - also handles Quark cloud drive"""
    
    priority = 65
    supported_domains = [
        "quark.cn",
        "www.quark.cn",
        "search.quark.cn",
        "pan.quark.cn",
        "m.quark.cn"
    ]
    
    def extract(self, url: str, html: str) -> Dict:
        soup = BeautifulSoup(html, 'html.parser')
        
        # Check if this is a search results page or cloud drive page
        if "search.quark.cn" in url or "/search" in url:
            return self._extract_search_results(soup, url)
        elif "pan.quark.cn" in url or "/pan" in url:
            return self._extract_cloud_drive(soup, url)
        else:
            return self._extract_content_page(soup, url)
    
    def _extract_search_results(self, soup: BeautifulSoup, url: str) -> Dict:
        """Extract search results from Quark"""
        results = []
        
        # Find result items - Quark search results structure
        for item in soup.find_all("div", class_=re.compile(r"result|item|news-item")):
            result = {}
            
            # Title
            title_elem = item.find("h3") or item.find("h4") or item.find(class_=re.compile(r"title"))
            if title_elem:
                a_tag = title_elem.find("a")
                if a_tag:
                    result["title"] = a_tag.get_text(strip=True)
                    result["url"] = a_tag.get("href", "")
                else:
                    result["title"] = title_elem.get_text(strip=True)
            
            # Description
            desc_elem = item.find("p", class_=re.compile(r"desc|summary|text")) or item.find("div", class_=re.compile(r"content|desc"))
            if desc_elem:
                result["description"] = desc_elem.get_text(strip=True)
            
            # Source
            source_elem = item.find("span", class_=re.compile(r"source|from"))
            if source_elem:
                result["source"] = source_elem.get_text(strip=True)
            
            # Time
            time_elem = item.find("span", class_=re.compile(r"time|date"))
            if time_elem:
                result["time"] = time_elem.get_text(strip=True)
            
            if result.get("title"):
                results.append(result)
        
        # Try alternative: list structure
        if not results:
            for li in soup.find_all("li", class_=re.compile(r"item")):
                a_tag = li.find("a")
                if a_tag:
                    title = a_tag.get_text(strip=True)
                    href = a_tag.get("href", "")
                    if title and href:
                        results.append({
                            "title": title,
                            "url": href
                        })
        
        # Extract search query
        query = self._extract_query(url)
        
        return {
            "url": url,
            "title": "Quark Search Results",
            "query": query,
            "results": results,
            "type": "search"
        }
    
    def _extract_cloud_drive(self, soup: BeautifulSoup, url: str) -> Dict:
        """Extract Quark cloud drive file list"""
        files = []
        
        # Find file items
        for item in soup.find_all("div", class_=re.compile(r"file|item")):
            file_info = {}
            
            # File name
            name_elem = item.find("span", class_=re.compile(r"name|title")) or item.find("a")
            if name_elem:
                file_info["name"] = name_elem.get_text(strip=True)
            
            # File link
            a_tag = item.find("a")
            if a_tag:
                href = a_tag.get("href", "")
                if href:
                    file_info["url"] = urljoin("https://pan.quark.cn", href)
            
            # File size
            size_elem = item.find("span", class_=re.compile(r"size"))
            if size_elem:
                file_info["size"] = size_elem.get_text(strip=True)
            
            # File type
            type_elem = item.find("span", class_=re.compile(r"type"))
            if type_elem:
                file_info["type"] = type_elem.get_text(strip=True)
            
            # Modified time
            time_elem = item.find("span", class_=re.compile(r"time|modified"))
            if time_elem:
                file_info["modified"] = time_elem.get_text(strip=True)
            
            if file_info.get("name"):
                files.append(file_info)
        
        # Try table structure
        if not files:
            for row in soup.find_all("tr"):
                file_info = {}
                
                for td in row.find_all("td"):
                    name_link = td.find("a")
                    if name_link:
                        file_info["name"] = name_link.get_text(strip=True)
                        file_info["url"] = urljoin("https://pan.quark.cn", name_link.get("href", ""))
                    
                    # Check for file type icons
                    if td.get("class"):
                        file_info["type"] = " ".join(td.get("class"))
                
                if file_info.get("name"):
                    files.append(file_info)
        
        return {
            "url": url,
            "title": "Quark Cloud Drive",
            "files": files,
            "type": "cloud_drive"
        }
    
    def _extract_content_page(self, soup: BeautifulSoup, url: str) -> Dict:
        """Extract general content page"""
        
        # Extract title
        title = self._extract_title(soup)
        
        # Extract content
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
            "meta": meta,
            "type": "content"
        }
    
    def _extract_title(self, soup: BeautifulSoup) -> str:
        # Try og:title
        og_title = soup.find("meta", property="og:title")
        if og_title:
            return og_title.get("content", "")
        
        # Try h1
        h1 = soup.find("h1")
        if h1:
            return h1.get_text(strip=True)
        
        # Try title tag
        title_tag = soup.find("title")
        if title_tag:
            return title_tag.get_text(strip=True)
        
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
        for cls in ["content", "article", "post", "text"]:
            elem = soup.find("div", class_=cls)
            if elem:
                return elem.get_text(separator="\n", strip=True)
        
        return ""
    
    def _extract_images(self, soup: BeautifulSoup, base_url: str) -> List[Dict]:
        images = []
        
        # Extract og:image
        og_image = soup.find("meta", property="og:image")
        if og_image:
            images.append({
                "url": og_image.get("content", ""),
                "type": "og:image"
            })
        
        # Extract from img tags
        for img in soup.find_all("img"):
            src = img.get("src") or img.get("data-src")
            if src:
                images.append({
                    "url": urljoin(base_url, src),
                    "alt": img.get("alt", "")
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
        
        # Keywords
        keywords = soup.find("meta", attrs={"name": "keywords"})
        if keywords:
            meta["keywords"] = keywords.get("content", "")
        
        return meta
    
    def _extract_query(self, url: str) -> str:
        """Extract search query from URL"""
        parsed = urlparse(url)
        query_dict = parse_qs(parsed.query)
        
        # Common query parameter names
        for key in ["q", "keyword", "wd", "word", "query"]:
            if key in query_dict:
                return query_dict[key][0]
        
        return ""
