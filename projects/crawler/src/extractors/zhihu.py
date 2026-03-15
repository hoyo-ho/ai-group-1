# -*- coding: utf-8 -*-
"""
Zhihu Extractor
"""
import re
import json
from typing import Dict, List
from urllib.parse import urljoin, urlparse
from bs4 import BeautifulSoup

from .base import BaseExtractor


class ZhihuExtractor(BaseExtractor):
    """Zhihu article/answer extractor"""
    
    priority = 75
    supported_domains = [
        "zhihu.com",
        "zhihu.com.cn"
    ]
    
    def extract(self, url: str, html: str) -> Dict:
        soup = BeautifulSoup(html, 'html.parser')
        
        # Check if it's a question page
        if "/question/" in url:
            return self._extract_question(url, soup, html)
        elif "/article/" in url:
            return self._extract_article(url, soup, html)
        elif "/people/" in url or "/org/" in url:
            return self._extract_user(url, soup)
        else:
            return self._extract_generic(url, soup, html)
    
    def _extract_question(self, url: str, soup: BeautifulSoup, html: str) -> Dict:
        """Extract question page"""
        # Extract question title
        title = self._extract_title(soup)
        
        # Extract question content
        content = self._extract_question_content(soup, html)
        
        # Extract author
        author = self._extract_author(soup)
        
        # Extract publish time
        publish_time = self._extract_publish_time(soup)
        
        # Extract answers
        answers = self._extract_answers(soup, html)
        
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
            "answers": answers,
            "meta": meta,
            "tags": tags,
            "type": "question"
        }
    
    def _extract_article(self, url: str, soup: BeautifulSoup, html: str) -> Dict:
        """Extract article page"""
        # Extract title
        title = self._extract_title(soup)
        
        # Extract article content
        content = self._extract_article_content(soup, html)
        
        # Extract author
        author = self._extract_author(soup)
        
        # Extract publish time
        publish_time = self._extract_publish_time(soup)
        
        # Extract images
        images = self._extract_images(soup, url)
        
        # Extract meta info
        meta = self._extract_meta(soup)
        
        # Extract likes, comments
        meta.update(self._extract_social_stats(soup))
        
        return {
            "url": url,
            "title": title,
            "content": content,
            "author": author,
            "publish_time": publish_time,
            "images": images,
            "meta": meta,
            "type": "article"
        }
    
    def _extract_user(self, url: str, soup: BeautifulSoup) -> Dict:
        """Extract user profile"""
        # Extract username
        title = self._extract_title(soup)
        
        # Description
        bio = ""
        bio_elem = soup.find("meta", attrs={"name": "description"})
        if bio_elem:
            bio = bio_elem.get("content", "")
        
        # Extract user info
        meta = {}
        
        # Followers, following
        for a in soup.find_all("a", href=re.compile(r"followers|following")):
            span = a.find("span", class_=re.compile(r"count|num"))
            if span:
                text = span.get_text(strip=True)
                if "followers" in a.get("href", ""):
                    meta["followers"] = text
                elif "following" in a.get("href", ""):
                    meta["following"] = text
        
        return {
            "url": url,
            "title": title,
            "content": bio,
            "username": urlparse(url).path.split('/')[-1],
            "meta": meta,
            "type": "user"
        }
    
    def _extract_generic(self, url: str, soup: BeautifulSoup, html: str) -> Dict:
        """Extract generic page"""
        title = self._extract_title(soup)
        content = ""
        
        # Try main content
        main = soup.find("main") or soup.find("div", class_=re.compile(r"content|main"))
        if main:
            content = main.get_text(separator="\n", strip=True)
        
        return {
            "url": url,
            "title": title,
            "content": content[:5000] if content else "",
            "type": "generic"
        }
    
    def _extract_title(self, soup: BeautifulSoup) -> str:
        # Try og:title
        og_title = soup.find("meta", property="og:title")
        if og_title:
            return og_title.get("content", "")
        
        # Try title tag
        title_elem = soup.find("title")
        if title_elem:
            title_text = title_elem.get_text(strip=True)
            # Remove " - 知乎" suffix
            return title_text.replace(" - 知乎", "").replace(" - Zhihu", "").strip()
        
        # Try h1
        h1 = soup.find("h1")
        if h1:
            return h1.get_text(strip=True)
        
        return ""
    
    def _extract_question_content(self, soup: BeautifulSoup, html: str) -> str:
        # Try to find question detail
        question_div = soup.find("div", class_=re.compile(r"question-detail|QuestionDetail"))
        if question_div:
            return question_div.get_text(separator="\n", strip=True)
        
        # Try RichText
        rich_text = soup.find("div", class_=re.compile(r"RichText|ztext"))
        if rich_text:
            return rich_text.get_text(separator="\n", strip=True)
        
        # Try content in meta
        og_desc = soup.find("meta", property="og:description")
        if og_desc:
            return og_desc.get("content", "")
        
        return ""
    
    def _extract_article_content(self, soup: BeautifulSoup, html: str) -> str:
        # Try article content
        article = soup.find("article") or soup.find("div", class_=re.compile(r"article-content|post-content"))
        if article:
            return article.get_text(separator="\n", strip=True)
        
        # Try RichText
        rich_text = soup.find("div", class_=re.compile(r"RichText|ztext|content"))
        if rich_text:
            return rich_text.get_text(separator="\n", strip=True)
        
        # Try to extract from script JSON
        for script in soup.find_all("script"):
            script_text = script.string or ""
            if "initialState" in script_text or "content" in script_text:
                try:
                    # Try to find JSON data
                    match = re.search(r'"content"\s*:\s*"([^"]+)"', script_text)
                    if match:
                        return match.group(1)
                except:
                    pass
        
        # Fallback: og:description
        og_desc = soup.find("meta", property="og:description")
        if og_desc:
            return og_desc.get("content", "")
        
        return ""
    
    def _extract_answers(self, soup: BeautifulSoup, html: str) -> List[Dict]:
        answers = []
        
        # Find answer items
        answer_items = soup.find_all("div", class_=re.compile(r"answer-item|List-item"))
        
        for item in answer_items[:5]:  # Top 5 answers
            answer = {}
            
            # Author
            author_elem = item.find("a", class_=re.compile(r"author|name"))
            if author_elem:
                answer["author"] = author_elem.get_text(strip=True)
            
            # Content
            content_elem = item.find("div", class_=re.compile(r"content|RichText"))
            if content_elem:
                answer["content"] = content_elem.get_text(separator="\n", strip=True)[:500]
            
            # Votes
            votes_elem = item.find("span", class_=re.compile(r"vote|count"))
            if votes_elem:
                answer["votes"] = votes_elem.get_text(strip=True)
            
            if answer:
                answers.append(answer)
        
        return answers
    
    def _extract_author(self, soup: BeautifulSoup) -> str:
        # Try meta author
        author_meta = soup.find("meta", attrs={"name": "author"})
        if author_meta:
            return author_meta.get("content", "")
        
        # Try link with author class
        author_link = soup.find("a", class_=re.compile(r"author|name|user"))
        if author_link:
            return author_link.get_text(strip=True)
        
        # Try avatar wrapper
        avatar = soup.find("span", class_=re.compile(r"author-name"))
        if avatar:
            return avatar.get_text(strip=True)
        
        return ""
    
    def _extract_publish_time(self, soup: BeautifulSoup) -> str:
        # Try meta article:published_time
        pub_time = soup.find("meta", property="article:published_time")
        if pub_time:
            return pub_time.get("content", "")
        
        # Try time element
        time_elem = soup.find("time")
        if time_elem:
            return time_elem.get("datetime", "") or time_elem.get_text(strip=True)
        
        # Try span with date class
        date_span = soup.find("span", class_=re.compile(r"date|time|publish"))
        if date_span:
            return date_span.get_text(strip=True)
        
        return ""
    
    def _extract_images(self, soup: BeautifulSoup, base_url: str) -> List[Dict]:
        images = []
        
        # og:image
        og_image = soup.find("meta", property="og:image")
        if og_image:
            images.append({
                "url": og_image.get("content", ""),
                "type": "og:image"
            })
        
        # Content images
        content_div = soup.find("div", class_=re.compile(r"content|RichText|ztext"))
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
        
        return meta
    
    def _extract_tags(self, soup: BeautifulSoup) -> List[str]:
        tags = []
        
        # Try topic tags
        tag_div = soup.find("div", class_=re.compile(r"topic|tag"))
        if tag_div:
            for a in tag_div.find_all("a"):
                tag_text = a.get_text(strip=True)
                if tag_text:
                    tags.append(tag_text)
        
        return list(set(tags))
    
    def _extract_social_stats(self, soup: BeautifulSoup) -> Dict:
        stats = {}
        
        # Likes
        like_elem = soup.find("span", class_=re.compile(r"like|vote"))
        if like_elem:
            stats["likes"] = like_elem.get_text(strip=True)
        
        # Comments
        comment_elem = soup.find("span", class_=re.compile(r"comment"))
        if comment_elem:
            stats["comments"] = comment_elem.get_text(strip=True)
        
        return stats
