# -*- coding: utf-8 -*-
"""
Cnblogs (博客园) Extractor
"""
import re
from typing import Dict, List
from urllib.parse import urljoin, urlparse
from bs4 import BeautifulSoup

from .base import BaseExtractor


class CnblogsExtractor(BaseExtractor):
    """Cnblogs (博客园) article extractor"""
    
    priority = 70
    supported_domains = [
        "cnblogs.com",
        "www.cnblogs.com",
        "m.cnblogs.com"
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
        h1 = soup.find("h1", class_=re.compile(r"title|post-title"))
        if h1:
            return h1.get_text(strip=True)
        
        # Try title tag
        title_tag = soup.find("title")
        if title_tag:
            text = title_tag.get_text(strip=True)
            # Remove site name suffix
            if "- 博客园" in text:
                text = text.split("- 博客园")[0].strip()
            elif " - 博客园" in text:
                text = text.split(" - 博客园")[0].strip()
            return text
        
        return ""
    
    def _extract_content(self, soup: BeautifulSoup) -> str:
        # Try post-body - Cnblogs main content area
        content_div = soup.find("div", class_=re.compile(r"post-body|article-content|content|postDetail"))
        if content_div:
            return content_div.get_text(separator="\n", strip=True)
        
        # Try #cnblogs_post_body
        post_body = soup.find("div", id="cnblogs_post_body")
        if post_body:
            return post_body.get_text(separator="\n", strip=True)
        
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
        
        # Try author from link
        author_elem = soup.find("a", class_=re.compile(r"author|post-author"))
        if author_elem:
            return author_elem.get_text(strip=True)
        
        # Try author from span
        author_span = soup.find("span", class_=re.compile(r"author|poster"))
        if author_span:
            return author_span.get_text(strip=True)
        
        # Try to extract from URL (cnblogs.com/username/)
        match = re.search(r"cnblogs\.com/([a-zA-Z0-9_-]+)/", url)
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
        
        # Try span with time class
        time_span = soup.find("span", class_=re.compile(r"time|date|post-date"))
        if time_span:
            return time_span.get_text(strip=True)
        
        # Try class containing date
        date_elem = soup.find(class_=re.compile(r"date|time|publish"))
        if date_elem:
            text = date_elem.get_text(strip=True)
            # Check if it looks like a date
            if re.search(r"\d{4}[-/年]\d{1,2}[-/月]\d{1,2}", text):
                return text
        
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
        content_div = soup.find("div", class_=re.compile(r"post-body|article-content|content|postDetail"))
        if not content_div:
            content_div = soup.find("div", id="cnblogs_post_body")
        
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
        
        # Try tag list - Cnblogs uses .post-tags
        tag_div = soup.find("div", class_=re.compile(r"post-tags|tag-list"))
        if tag_div:
            for a in tag_div.find_all("a"):
                tag_text = a.get_text(strip=True)
                if tag_text and tag_text != "标签:":
                    tags.append(tag_text)
        
        # Try meta keywords
        keywords = soup.find("meta", attrs={"name": "keywords"})
        if keywords:
            kw = keywords.get("content", "")
            if kw:
                tags.extend([t.strip() for t in kw.split(",") if t.strip()])
        
        return list(set(tags))
