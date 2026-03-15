# -*- coding: utf-8 -*-
"""
Juejin (稀土掘金) Extractor
"""
import re
from typing import Dict, List
from urllib.parse import urljoin, urlparse
from bs4 import BeautifulSoup

from .base import BaseExtractor


class JuejinExtractor(BaseExtractor):
    """Juejin (稀土掘金) article extractor"""
    
    priority = 70
    supported_domains = [
        "juejin.cn",
        "juejin.im",
        "www.juejin.cn"
    ]
    
    def extract(self, url: str, html: str) -> Dict:
        soup = BeautifulSoup(html, 'html.parser')
        
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
        
        # Extract tags
        tags = self._extract_tags(soup)
        
        # Extract statistics
        stats = self._extract_stats(soup)
        
        return {
            "url": url,
            "title": title,
            "content": content,
            "author": author,
            "publish_time": publish_time,
            "images": images,
            "meta": meta,
            "tags": tags,
            "stats": stats,
            "type": "article"
        }
    
    def _extract_title(self, soup: BeautifulSoup) -> str:
        # Try og:title
        og_title = soup.find("meta", property="og:title")
        if og_title:
            return og_title.get("content", "")
        
        # Try article title - Juejin uses .article-title
        title_elem = soup.find(class_=re.compile(r"article-title|post-title|title"))
        if title_elem:
            return title_elem.get_text(strip=True)
        
        # Try h1
        h1 = soup.find("h1")
        if h1:
            return h1.get_text(strip=True)
        
        # Try title tag
        title_tag = soup.find("title")
        if title_tag:
            text = title_tag.get_text(strip=True)
            # Remove suffix
            if "- 掘金" in text:
                text = text.split("- 掘金")[0].strip()
            elif " - 掘金" in text:
                text = text.split(" - 掘金")[0].strip()
            return text
        
        return ""
    
    def _extract_content(self, soup: BeautifulSoup) -> str:
        # Try main content area - Juejin uses .markdown-body
        content_div = soup.find("div", class_=re.compile(r"markdown-body|article-content|content|article-body"))
        if content_div:
            return content_div.get_text(separator="\n", strip=True)
        
        # Try #juejin-content
        juejin_content = soup.find("div", id="juejin")
        if juejin_content:
            return juejin_content.get_text(separator="\n", strip=True)
        
        # Try article tag
        article = soup.find("article")
        if article:
            return article.get_text(separator="\n", strip=True)
        
        # Try main content
        main = soup.find("main")
        if main:
            return main.get_text(separator="\n", strip=True)
        
        return ""
    
    def _extract_author(self, soup: BeautifulSoup) -> str:
        # Try meta author
        author = soup.find("meta", attrs={"name": "author"})
        if author:
            return author.get("content", "")
        
        # Try author link - Juejin has user-info class
        author_elem = soup.find("a", class_=re.compile(r"author|user-info|username"))
        if author_elem:
            return author_elem.get_text(strip=True)
        
        # Try author name span
        author_span = soup.find("span", class_=re.compile(r"author|username|name"))
        if author_span:
            return author_span.get_text(strip=True)
        
        # Try meta article:author
        meta_author = soup.find("meta", property="article:author")
        if meta_author:
            return meta_author.get("content", "")
        
        return ""
    
    def _extract_publish_time(self, soup: BeautifulSoup) -> str:
        # Try meta publish time
        pub_time = soup.find("meta", property="article:published_time")
        if pub_time:
            return pub_time.get("content", "")
        
        # Try meta updated_time
        updated_time = soup.find("meta", property="article:modified_time")
        if updated_time:
            return updated_time.get("content", "")
        
        # Try time tag
        time_elem = soup.find("time")
        if time_elem:
            return time_elem.get("datetime", "") or time_elem.get_text(strip=True)
        
        # Try span with time class
        time_span = soup.find("span", class_=re.compile(r"time|date|publish-time"))
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
        
        # Extract from content
        content_div = soup.find("div", class_=re.compile(r"markdown-body|article-content|content|article-body"))
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
        tag_div = soup.find("div", class_=re.compile(r"tags|tag-list|article-tags"))
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
    
    def _extract_stats(self, soup: BeautifulSoup) -> Dict:
        stats = {}
        
        # Try to find view count
        view_elem = soup.find(class_=re.compile(r"views|view-count|read-count"))
        if view_elem:
            stats["views"] = view_elem.get_text(strip=True)
        
        # Try to find like count
        like_elem = soup.find(class_=re.compile(r"likes|like-count"))
        if like_elem:
            stats["likes"] = like_elem.get_text(strip=True)
        
        # Try to find comment count
        comment_elem = soup.find(class_=re.compile(r"comments|comment-count"))
        if comment_elem:
            stats["comments"] = comment_elem.get_text(strip=True)
        
        return stats
