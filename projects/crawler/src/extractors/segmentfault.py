# -*- coding: utf-8 -*-
"""
SegmentFault Extractor
"""
import re
from typing import Dict, List
from urllib.parse import urljoin, urlparse
from bs4 import BeautifulSoup

from .base import BaseExtractor


class SegmentfaultExtractor(BaseExtractor):
    """SegmentFault article extractor"""
    
    priority = 70
    supported_domains = [
        "segmentfault.com",
        "www.segmentfault.com",
        "m.segmentfault.com"
    ]
    
    def extract(self, url: str, html: str) -> Dict:
        soup = BeautifulSoup(html, 'html.parser')
        
        # Check if this is a question page or article page
        if "/a/" in url or "/q/" in url:
            return self._extract_article(soup, url)
        elif "/questions" in url:
            return self._extract_question(soup, url)
        else:
            return self._extract_article(soup, url)
    
    def _extract_article(self, soup: BeautifulSoup, url: str) -> Dict:
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
    
    def _extract_question(self, soup: BeautifulSoup, url: str) -> Dict:
        # Extract title
        title = self._extract_title(soup)
        
        # Extract question content
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
        
        # Extract answers
        answers = self._extract_answers(soup)
        
        return {
            "url": url,
            "title": title,
            "content": content,
            "author": author,
            "publish_time": publish_time,
            "images": images,
            "meta": meta,
            "tags": tags,
            "answers": answers,
            "type": "question"
        }
    
    def _extract_title(self, soup: BeautifulSoup) -> str:
        # Try og:title
        og_title = soup.find("meta", property="og:title")
        if og_title:
            return og_title.get("content", "")
        
        # Try h1 title
        h1 = soup.find("h1", class_=re.compile(r"title|article-title|question-title"))
        if h1:
            return h1.get_text(strip=True)
        
        # Try .news__item--title
        title_elem = soup.find(class_=re.compile(r"article-title|post-title|title|news__item--title"))
        if title_elem:
            return title_elem.get_text(strip=True)
        
        # Try title tag
        title_tag = soup.find("title")
        if title_tag:
            text = title_tag.get_text(strip=True)
            # Remove suffix
            if "- SegmentFault" in text:
                text = text.split("- SegmentFault")[0].strip()
            elif " - SegmentFault" in text:
                text = text.split(" - SegmentFault")[0].strip()
            return text
        
        return ""
    
    def _extract_content(self, soup: BeautifulSoup) -> str:
        # Try article content - SegmentFault uses .article-content or .post-content
        content_div = soup.find("div", class_=re.compile(r"article-content|post-content|article-body|content|news__item--content"))
        if content_div:
            return content_div.get_text(separator="\n", strip=True)
        
        # Try .content
        content = soup.find(class_=re.compile(r"content|article"))
        if content:
            return content.get_text(separator="\n", strip=True)
        
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
        
        # Try author link
        author_elem = soup.find("a", class_=re.compile(r"author|user|username"))
        if author_elem:
            return author_elem.get_text(strip=True)
        
        # Try author span
        author_span = soup.find("span", class_=re.compile(r"author|username|name|user-name"))
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
        content_div = soup.find("div", class_=re.compile(r"article-content|post-content|article-body|content"))
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
        tag_div = soup.find("div", class_=re.compile(r"tags|tag-list|article-tags|news__item--tags"))
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
    
    def _extract_answers(self, soup: BeautifulSoup) -> List[Dict]:
        answers = []
        
        # Try to find answer items
        answer_items = soup.find_all(class_=re.compile(r"answer|comment|reply"))
        
        for item in answer_items[:10]:  # Limit to first 10 answers
            answer = {}
            
            # Extract author
            author_elem = item.find("a", class_=re.compile(r"author|user"))
            if author_elem:
                answer["author"] = author_elem.get_text(strip=True)
            
            # Extract content
            content_elem = item.find(class_=re.compile(r"content|answer-content"))
            if content_elem:
                answer["content"] = content_elem.get_text(separator="\n", strip=True)
            
            # Extract time
            time_elem = item.find("time")
            if time_elem:
                answer["time"] = time_elem.get("datetime", "") or time_elem.get_text(strip=True)
            
            if answer.get("content"):
                answers.append(answer)
        
        return answers
