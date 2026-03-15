# -*- coding: utf-8 -*-
"""
Douyin (TikTok China) Extractor - Requires Playwright
"""
import re
import json
from typing import Dict, List
from urllib.parse import urljoin, parse_qs, urlparse
from bs4 import BeautifulSoup

from .base import BaseExtractor


class DouyinExtractor(BaseExtractor):
    """Douyin video extractor - requires Playwright for JavaScript rendering"""
    
    priority = 85
    supported_domains = ["douyin.com", "www.douyin.com", "live.douyin.com"]
    
    def extract(self, url: str, html: str) -> Dict:
        soup = BeautifulSoup(html, 'html.parser')
        
        # Extract title
        title = self._extract_title(soup, url)
        
        # Extract video info
        video_info = self._extract_video_info(soup, url)
        
        # Extract description
        description = self._extract_description(soup)
        
        # Extract author
        author = self._extract_author(soup)
        
        # Extract images
        images = self._extract_images(soup, url)
        
        # Extract stats (likes, comments, shares)
        stats = self._extract_stats(soup)
        
        # Extract music info
        music = self._extract_music(soup)
        
        return {
            "url": url,
            "title": title,
            "video": video_info,
            "description": description,
            "author": author,
            "images": images,
            "stats": stats,
            "music": music
        }
    
    def _extract_title(self, soup: BeautifulSoup, url: str) -> str:
        # Try og:title
        og_title = soup.find("meta", property="og:title")
        if og_title:
            title = og_title.get("content", "")
            if title:
                return title.strip()
        
        # Try from JSON data
        for script in soup.find_all("script"):
            script_text = script.string or ""
            if "window.__INITIAL_STATE__" in script_text or "window.__DATA__" in script_text:
                match = re.search(r'"desc":"([^"]+)"', script_text)
                if match:
                    return match.group(1).replace('\\u0026', '&')
        
        # Try from video title element
        title_elem = soup.find("h1") or soup.find("div", class_=re.compile(r"title"))
        if title_elem:
            return title_elem.get_text(strip=True)
        
        return ""
    
    def _extract_video_info(self, soup: BeautifulSoup, url: str) -> Dict:
        video_info = {}
        
        # Extract video ID from URL
        parsed = urlparse(url)
        video_id = None
        
        # Pattern: /video/7123456789...
        match = re.search(r'/video/(\d+)', url)
        if match:
            video_id = match.group(1)
            video_info["id"] = video_id
        
        # Try to find video URL from page
        for script in soup.find_all("script"):
            script_text = script.string or ""
            
            # Look for play URL in script
            if "playUrl" in script_text or "video" in script_text:
                url_match = re.search(r'(https?://[^\s"\'<>]+(?:mp4|playurl)[^\s"\'<>]*)', script_text)
                if url_match:
                    video_info["play_url"] = url_match.group(1)
                
                # Extract cover image
                cover_match = re.search(r'(https?://[^\s"\'<>]+(?:cover|poster)[^\s"\'<>]*)', script_text)
                if cover_match:
                    video_info["cover"] = cover_match.group(1)
        
        # Find video element directly
        video_elem = soup.find("video")
        if video_elem:
            video_info["src"] = video_elem.get("src", "")
            video_info["poster"] = video_elem.get("poster", "")
        
        return video_info
    
    def _extract_description(self, soup: BeautifulSoup) -> str:
        # Try og:description
        og_desc = soup.find("meta", property="og:description")
        if og_desc:
            return og_desc.get("content", "")
        
        # Try description div
        for cls in ["desc", "description", "content", "video-info"]:
            desc_elem = soup.find("div", class_=re.compile(cls))
            if desc_elem:
                return desc_elem.get_text(strip=True)
        
        return ""
    
    def _extract_author(self, soup: BeautifulSoup) -> Dict:
        author = {}
        
        # Try meta author
        author_meta = soup.find("meta", attrs={"name": "author"})
        if author_meta:
            author["name"] = author_meta.get("content", "")
        
        # Try from JSON data
        for script in soup.find_all("script"):
            script_text = script.string or ""
            
            # Look for author/nickname
            nick_match = re.search(r'"nickname":"([^"]+)"', script_text)
            if nick_match:
                author["nickname"] = nick_match.group(1).replace('\\u0026', '&')
            
            unique_match = re.search(r'"unique_id":"([^"]+)"', script_text)
            if unique_match:
                author["unique_id"] = unique_match.group(1)
            
            avatar_match = re.search(r'(https?://[^\s"\'<>]+avatar[^\s"\'<>]*)', script_text)
            if avatar_match:
                author["avatar"] = avatar_match.group(1)
        
        # Find author link
        author_link = soup.find("a", href=re.compile(r"/user/"))
        if author_link:
            author["url"] = "https://www.douyin.com" + author_link.get("href", "")
            if "nickname" not in author:
                author["nickname"] = author_link.get_text(strip=True)
        
        return author
    
    def _extract_images(self, soup: BeautifulSoup, base_url: str) -> List[Dict]:
        images = []
        
        # Extract og:image
        og_image = soup.find("meta", property="og:image")
        if og_image:
            images.append({
                "url": og_image.get("content", ""),
                "type": "og:image"
            })
        
        # Extract from script data
        for script in soup.find_all("script"):
            script_text = script.string or ""
            if "cover" in script_text.lower():
                img_matches = re.findall(r'(https?://[^\s"\'<>]+\.(?:jpg|jpeg|png|webp)[^\s"\'<>]*)', script_text)
                for img in set(img_matches):
                    if "douyin" in img.lower():
                        images.append({
                            "url": img,
                            "type": "script"
                        })
                        break
        
        return images
    
    def _extract_stats(self, soup: BeautifulSoup) -> Dict:
        stats = {}
        
        # Try from JSON data
        for script in soup.find_all("script"):
            script_text = script.string or ""
            
            # Look for statistics
            if "diggCount" in script_text or "commentCount" in script_text or "shareCount" in script_text:
                digg_match = re.search(r'"diggCount":(\d+)', script_text)
                if digg_match:
                    stats["likes"] = int(digg_match.group(1))
                
                comment_match = re.search(r'"commentCount":(\d+)', script_text)
                if comment_match:
                    stats["comments"] = int(comment_match.group(1))
                
                share_match = re.search(r'"shareCount":(\d+)', script_text)
                if share_match:
                    stats["shares"] = int(share_match.group(1))
                
                play_match = re.search(r'"playCount":(\d+)', script_text)
                if play_match:
                    stats["plays"] = int(play_match.group(1))
        
        return stats
    
    def _extract_music(self, soup: BeautifulSoup) -> Dict:
        music = {}
        
        # Try from JSON data
        for script in soup.find_all("script"):
            script_text = script.string or ""
            
            if "music" in script_text.lower():
                title_match = re.search(r'"musicTitle":"([^"]+)"', script_text)
                if title_match:
                    music["title"] = title_match.group(1).replace('\\u0026', '&')
                
                author_match = re.search(r'"musicAuthor":"([^"]+)"', script_text)
                if author_match:
                    music["author"] = author_match.group(1)
        
        return music
