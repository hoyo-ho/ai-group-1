# -*- coding: utf-8 -*-
"""
Sohu Search Extractor
"""
import re
from typing import Dict, List
from urllib.parse import urljoin, urlparse
from bs4 import BeautifulSoup

from .base import BaseExtractor


class SohuExtractor(BaseExtractor):
    """Sohu search results and content extractor"""
    
    priority = 60
    supported_domains = [
        "sohu.com",
        "www.sohu.com",
        "search.sohu.com",
        "m.sohu.com"
    ]
    
    def extract(self, url: str, html: str) -> Dict:
        soup = BeautifulSoup(html, 'html.parser')
        
        # Check if this is a search results page or article page
        if "search.sohu.com" in url or "/search" in url:
            return self._extract_search_results(soup, url)
        else:
            return self._extract_article(soup, url)
    
    def _extract_search_results(self, soup: BeautifulSoup, url: str) -> Dict:
        """Extract search results from Sohu"""
        results = []
        
        # Find result items - Sohu search results usually in ul/li structure
        for li in soup.find_all("li", class_=re.compile(r"result|item")):
            result = {}
            
            # Title - usually in h3 or h4
            title_elem = li.find("h3") or li.find("h4")
            if title_elem:
                a_tag = title_elem.find("a")
                if a_tag:
                    result["title"] = a_tag.get_text(strip=True)
                    result["url"] = a_tag.get("href", "")
            
            # Description
            desc_elem = li.find("p", class_=re.compile(r"desc|summary")) or li.find("div", class_=re.compile(r"text"))
            if desc_elem:
                result["description"] = desc_elem.get_text(strip=True)
            
            # Source and time
            info_elem = li.find("span", class_=re.compile(r"info|source|time"))
            if info_elem:
                result["source_info"] = info_elem.get_text(strip=True)
            
            if result.get("title"):
                results.append(result)
        
        # Try alternative pattern for news search
        if not results:
            for item in soup.find_all("div", class_=re.compile(r"news-item|article-item")):
                result = {}
                
                a_tag = item.find("a")
                if a_tag:
                    result["title"] = a_tag.get_text(strip=True)
                    result["url"] = a_tag.get("href", "")
                
                desc = item.find("p")
                if desc:
                    result["description"] = desc.get_text(strip=True)
                
                if result.get("title"):
                    results.append(result)
        
        # Extract search query
        query = self._extract_query(url)
        
        return {
            "url": url,
            "title": "Sohu Search Results",
            "query": query,
            "results": results,
            "type": "search"
        }
    
    def _extract_article(self, soup: BeautifulSoup, url: str) -> Dict:
        """Extract article content from Sohu"""
        
        # Extract title
        title = self._extract_title(soup)
        
        # Extract article content
        content = self._extract_content(soup)
        
        # Extract author
        author = self._extract_author(soup)
        
        # Extract publish time
        publish_time = self._extract_publish_time(soup)
        
        # Extract images
        images = self._extract_images(soup, url)
        
        # Extract meta info
        meta = self._extract_meta(soup)
        
        # Extract related articles
        related = self._extract_related(soup)
        
        return {
            "url": url,
            "title": title,
            "content": content,
            "author": author,
            "publish_time": publish_time,
            "images": images,
            "meta": meta,
            "related": related,
            "type": "article"
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
        
        # Try article title class
        title_elem = soup.find(class_=re.compile(r"title|text-title|article-title"))
        if title_elem:
            return title_elem.get_text(strip=True)
        
        return ""
    
    def _extract_content(self, soup: BeautifulSoup) -> str:
        # Try article tag
        article = soup.find("article")
        if article:
            return article.get_text(separator="\n", strip=True)
        
        # Try main content area
        for cls in ["article-content", "article_text", "text", "content", "main-text"]:
            content_div = soup.find("div", class_=cls)
            if content_div:
                return content_div.get_text(separator="\n", strip=True)
        
        # Try article section
        article_section = soup.find("section", class_=re.compile(r"content"))
        if article_section:
            return article_section.get_text(separator="\n", strip=True)
        
        return ""
    
    def _extract_author(self, soup: BeautifulSoup) -> str:
        # Try meta author
        author = soup.find("meta", attrs={"name": "author"})
        if author:
            return author.get("content", "")
        
        # Try author span
        author_elem = soup.find("span", class_=re.compile(r"author|name|editor"))
        if author_elem:
            return author_elem.get_text(strip=True)
        
        # Try rel="author"
        author_link = soup.find("a", rel="author")
        if author_link:
            return author_link.get_text(strip=True)
        
        return ""
    
    def _extract_publish_time(self, soup: BeautifulSoup) -> str:
        # Try meta publish time
        pub_time = soup.find("meta", property="article:published_time")
        if pub_time:
            return pub_time.get("content", "")
        
        # Try time tag
        time_elem = soup.find("time")
        if time_elem:
            return time_elem.get("datetime", "") or time_elem.get_text(strip=True)
        
        # Try span with time class
        time_span = soup.find("span", class_=re.compile(r"time|date|pub-time"))
        if time_span:
            return time_span.get_text(strip=True)
        
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
        
        # Extract from article images
        article = soup.find("article")
        if article:
            for img in article.find_all("img"):
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
    
    def _extract_related(self, soup: BeautifulSoup) -> List[Dict]:
        related = []
        
        # Find related articles section
        for cls in ["related", "recommend", "relative"]:
            related_div = soup.find("div", class_=re.compile(cls))
            if related_div:
                for a in related_div.find_all("a"):
                    title = a.get_text(strip=True)
                    href = a.get("href", "")
                    if title and href:
                        related.append({
                            "title": title,
                            "url": urljoin("https://www.sohu.com", href)
                        })
        
        return related
    
    def _extract_query(self, url: str) -> str:
        """Extract search query from URL"""
        parsed = urlparse(url)
        query_dict = parse_qs(parsed.query)
        
        # Common query parameter names
        for key in ["q", "keyword", "wd", "word", "query"]:
            if key in query_dict:
                return query_dict[key][0]
        
        return ""
