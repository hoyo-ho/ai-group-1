# -*- coding: utf-8 -*-
"""
CSDN Extractor
"""
import re
from typing import Dict, List
from urllib.parse import urljoin, urlparse
from bs4 import BeautifulSoup

from .base import BaseExtractor


class CsdnExtractor(BaseExtractor):
    """CSDN article extractor"""
    
    priority = 70
    supported_domains = [
        "blog.csdn.net",
        "csdn.net",
        "download.csdn.net",
        "ask.csdn.net"
    ]
    
    def extract(self, url: str, html: str) -> Dict:
        soup = BeautifulSoup(html, 'html.parser')
        
        # Extract title
        title = self._extract_title(soup)
        
        # Extract article content
        content = self._extract_content(soup)
        
        # Extract author
        author = self._extract_author(soup, url)
        
        # Extract publish time
        publish_time = self._extract_publish_time(soup)
        
        # Extract images
        images = self._extract_images(soup, url)
        
        # Extract meta info
        meta = self._extract_meta(soup)
        
        # Extract tags
        tags = self._extract_tags(soup)
        
        return {
            "url": url,
            "title": title,
            "content": content,
            "author": author,
            "publish_time": publish_time,
            "images": images,
            "meta": meta,
            "tags": tags,
            "type": "article"
        }
    
    def _extract_title(self, soup: BeautifulSoup) -> str:
        # Try og:title
        og_title = soup.find("meta", property="og:title")
        if og_title:
            return og_title.get("content", "")
        
        # Try h1 title
        h1 = soup.find("h1", class_=re.compile(r"title|article-title"))
        if h1:
            return h1.get_text(strip=True)
        
        # Try article title div
        title_div = soup.find("div", class_="article-title")
        if title_div:
            return title_div.get_text(strip=True)
        
        # Try title tag
        title_tag = soup.find("title")
        if title_tag:
            return title_tag.get_text(strip=True).split("-")[0].strip()
        
        return ""
    
    def _extract_content(self, soup: BeautifulSoup) -> str:
        # Try main content area - CSDN uses .markdown-body or #content_views
        content_div = soup.find("div", class_=re.compile(r"markdown-body|article_content|content"))
        if content_div:
            return content_div.get_text(separator="\n", strip=True)
        
        # Try content views div
        content_views = soup.find("div", id="content_views")
        if content_views:
            return content_views.get_text(separator="\n", strip=True)
        
        # Try article tag
        article = soup.find("article")
        if article:
            return article.get_text(separator="\n", strip=True)
        
        # Try main content
        main = soup.find("main")
        if main:
            return main.get_text(separator="\n", strip=True)
        
        return ""
    
    def _extract_author(self, soup: BeautifulSoup, url: str) -> str:
        # Try meta author
        author = soup.find("meta", attrs={"name": "author"})
        if author:
            return author.get("content", "")
        
        # Try author info from page
        author_elem = soup.find("a", class_=re.compile(r"author|name|user"))
        if author_elem:
            return author_elem.get_text(strip=True)
        
        # Try author div
        author_div = soup.find("div", class_=re.compile(r"author|nickname"))
        if author_div:
            return author_div.get_text(strip=True)
        
        # Try to extract from URL (blog.csdn.net/username/article/details/...)
        match = re.search(r"blog\.csdn\.net/([^/]+)/", url)
        if match:
            return match.group(1)
        
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
        
        # Try span with time class - CSDN often uses .time
        time_span = soup.find("span", class_=re.compile(r"time|date|time-text"))
        if time_span:
            return time_span.get_text(strip=True)
        
        # Try meta article:time
        article_time = soup.find("meta", attrs={"property": "article:time"})
        if article_time:
            return article_time.get("content", "")
        
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
        
        # Extract from content
        content_div = soup.find("div", class_=re.compile(r"markdown-body|article_content|content"))
        if content_div:
            for img in content_div.find_all("img"):
                src = img.get("src") or img.get("data-src") or img.get("data-original")
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
    
    def _extract_tags(self, soup: BeautifulSoup) -> List[str]:
        tags = []
        
        # Try tag list
        tag_div = soup.find("div", class_=re.compile(r"tags|tag-list"))
        if tag_div:
            for a in tag_div.find_all("a"):
                tag_text = a.get_text(strip=True)
                if tag_text:
                    tags.append(tag_text)
        
        # Try meta keywords
        keywords = soup.find("meta", attrs={"name": "keywords"})
        if keywords:
            kw = keywords.get("content", "")
            if kw:
                tags.extend([t.strip() for t in kw.split(",") if t.strip()])
        
        return list(set(tags))
