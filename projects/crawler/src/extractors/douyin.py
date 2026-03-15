# -*- coding: utf-8 -*-
"""
Douyin (TikTok China) Extractor - Requires Playwright
"""
import re
import json
from typing import Dict, List
from urllib.parse import urljoin, parse_qs, urlparse, unquote
from bs4 import BeautifulSoup

from .base import BaseExtractor


class DouyinExtractor(BaseExtractor):
    """Douyin video extractor - requires Playwright for JavaScript rendering"""
    
    priority = 85
    supported_domains = ["douyin.com", "www.douyin.com", "live.douyin.com"]
    
    def extract(self, url: str, html: str) -> Dict:
        soup = BeautifulSoup(html, 'html.parser')
        
        # Try to extract RENDER_DATA first (most reliable source)
        render_data = self._extract_render_data(soup)
        
        # Extract title
        title = self._extract_title(soup, url, render_data)
        
        # Extract video info
        video_info = self._extract_video_info(soup, url, render_data)
        
        # Extract description
        description = self._extract_description(soup, render_data)
        
        # Extract author
        author = self._extract_author(soup, render_data)
        
        # Extract images
        images = self._extract_images(soup, url, render_data)
        
        # Extract stats (likes, comments, shares)
        stats = self._extract_stats(soup, render_data)
        
        # Extract music info
        music = self._extract_music(soup, render_data)
        
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
    
    def _extract_render_data(self, soup: BeautifulSoup) -> Dict:
        """Extract and parse RENDER_DATA from script tag"""
        # Find RENDER_DATA script tag
        render_script = soup.find("script", id="RENDER_DATA")
        if render_script and render_script.string:
            try:
                # URL decode the data
                encoded_data = render_script.string
                decoded_data = unquote(encoded_data)
                return json.loads(decoded_data)
            except (json.JSONDecodeError, TypeError) as e:
                pass
        
        # Fallback: try to find RENDER_DATA in other script tags
        for script in soup.find_all("script"):
            script_text = script.string or ""
            if "RENDER_DATA" in script_text:
                match = re.search(r'RENDER_DATA\s*=\s*({.*?});', script_text, re.DOTALL)
                if match:
                    try:
                        encoded_data = match.group(1)
                        decoded_data = unquote(encoded_data)
                        return json.loads(decoded_data)
                    except (json.JSONDecodeError, TypeError):
                        pass
        
        return {}
    
    def _extract_title(self, soup: BeautifulSoup, url: str, render_data: Dict) -> str:
        # Try og:title
        og_title = soup.find("meta", property="og:title")
        if og_title:
            title = og_title.get("content", "")
            if title:
                return title.strip()
        
        # Try from RENDER_DATA
        if render_data:
            # Try common paths for title/desc
            title = self._get_nested_value(render_data, [
                "aweme.detail.desc",
                "video.desc",
                "detail.desc",
                "aweme.detail.title",
                "video.title"
            ])
            if title:
                return title
        
        # Try from JSON data in scripts
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
    
    def _get_nested_value(self, data: Dict, keys: List[str]) -> str:
        """Safely get nested value from dict using dot notation keys"""
        for key in keys:
            value = data
            for k in key.split('.'):
                if isinstance(value, dict):
                    value = value.get(k)
                elif isinstance(value, list) and len(value) > 0:
                    # If it's a list and we need to go deeper, get first element
                    value = value[0]
                    if isinstance(value, dict):
                        value = value.get(k)
                    else:
                        break
                else:
                    break
            if value and isinstance(value, str) and value.strip():
                return value.strip()
        return ""
    
    def _get_nested_list(self, data: Dict, keys: List[str]) -> List:
        """Safely get nested list from dict using dot notation keys"""
        for key in keys:
            value = data
            for k in key.split('.'):
                if isinstance(value, dict):
                    value = value.get(k)
                elif isinstance(value, list) and len(value) > 0:
                    value = value[0]
                    if isinstance(value, dict):
                        value = value.get(k)
                    else:
                        break
                else:
                    break
            if value and isinstance(value, list):
                return value
        return []
    
    def _extract_video_info(self, soup: BeautifulSoup, url: str, render_data: Dict) -> Dict:
        video_info = {}
        
        # Extract video ID from URL
        parsed = urlparse(url)
        video_id = None
        
        # Pattern: /video/7123456789...
        match = re.search(r'/video/(\d+)', url)
        if match:
            video_id = match.group(1)
            video_info["id"] = video_id
        
        # Try to find video URL from RENDER_DATA
        if render_data:
            # Get video URL list and extract first URL
            url_list = self._get_nested_list(render_data, [
                "video.play_addr.url_list",
                "aweme.detail.video.play_addr.url_list",
                "aweme.detail.video.download_addr.url_list",
                "video.download_addr.url_list",
            ])
            if url_list and len(url_list) > 0:
                first_url = url_list[0]
                if isinstance(first_url, dict):
                    video_info["play_url"] = first_url.get("url", "")
                else:
                    video_info["play_url"] = first_url
            
            # Also try direct URL field
            if not video_info.get("play_url"):
                video_url = self._get_nested_value(render_data, [
                    "aweme.detail.video.play_addr.h264_play_url",
                    "aweme.detail.video.play_addr.download_suffix",
                ])
                if video_url:
                    video_info["play_url"] = video_url
            
            # Extract cover image from RENDER_DATA
            cover_list = self._get_nested_list(render_data, [
                "video.cover.url_list",
                "aweme.detail.video.cover.url_list",
            ])
            if cover_list and len(cover_list) > 0:
                first_cover = cover_list[0]
                if isinstance(first_cover, dict):
                    video_info["cover"] = first_cover.get("url", "")
                else:
                    video_info["cover"] = first_cover
            else:
                # Try direct cover URL
                cover = self._get_nested_value(render_data, [
                    "aweme.detail.video.cover.download_suffix",
                ])
                if cover:
                    video_info["cover"] = cover
        
        # Fallback: try to find video URL from page scripts
        if not video_info.get("play_url"):
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
    
    def _extract_description(self, soup: BeautifulSoup, render_data: Dict) -> str:
        # Try RENDER_DATA first
        if render_data:
            desc = self._get_nested_value(render_data, [
                "aweme.detail.desc",
                "video.desc",
                "detail.desc",
            ])
            if desc:
                return desc
        
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
    
    def _extract_author(self, soup: BeautifulSoup, render_data: Dict) -> Dict:
        author = {}
        
        # Try RENDER_DATA first
        if render_data:
            author_info = render_data.get("aweme", {}).get("detail", {}).get("author", {})
            if author_info:
                author["nickname"] = author_info.get("nickname", "")
                author["unique_id"] = author_info.get("unique_id", "")
                avatar = author_info.get("avatar", {})
                if isinstance(avatar, dict):
                    author["avatar"] = avatar.get("url_list", [{}])[0].get("url", "")
                elif isinstance(avatar, list) and len(avatar) > 0:
                    if isinstance(avatar[0], dict):
                        author["avatar"] = avatar[0].get("url", "")
                    else:
                        author["avatar"] = avatar[0]
        
        # Try meta author
        if not author:
            author_meta = soup.find("meta", attrs={"name": "author"})
            if author_meta:
                author["name"] = author_meta.get("content", "")
        
        # Try from JSON data
        if not author.get("nickname"):
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
    
    def _extract_images(self, soup: BeautifulSoup, base_url: str, render_data: Dict) -> List[Dict]:
        images = []
        
        # Try RENDER_DATA first
        if render_data:
            # Try to get cover from video
            cover = self._get_nested_value(render_data, [
                "video.cover.url_list",
                "aweme.detail.video.cover.url_list",
            ])
            if cover:
                if isinstance(cover, list) and len(cover) > 0:
                    if isinstance(cover[0], dict):
                        img_url = cover[0].get("url", "")
                    else:
                        img_url = cover[0]
                else:
                    img_url = cover
                if img_url:
                    images.append({
                        "url": img_url,
                        "type": "cover"
                    })
        
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
    
    def _extract_stats(self, soup: BeautifulSoup, render_data: Dict) -> Dict:
        stats = {}
        
        # Try RENDER_DATA first
        if render_data:
            stats_info = render_data.get("aweme", {}).get("detail", {}).get("statistics", {})
            if stats_info:
                stats["likes"] = stats_info.get("digg_count", 0)
                stats["comments"] = stats_info.get("comment_count", 0)
                stats["shares"] = stats_info.get("share_count", 0)
                stats["plays"] = stats_info.get("play_count", 0)
        
        # Try from JSON data
        if not stats:
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
    
    def _extract_music(self, soup: BeautifulSoup, render_data: Dict) -> Dict:
        music = {}
        
        # Try RENDER_DATA first
        if render_data:
            music_info = render_data.get("aweme", {}).get("detail", {}).get("music", {})
            if music_info:
                music["title"] = music_info.get("title", "")
                music["author"] = music_info.get("author", "")
                music_url = music_info.get("play_url", {})
                if isinstance(music_url, dict):
                    music["url"] = music_url.get("url_list", [{}])[0].get("url", "")
                elif isinstance(music_url, list) and len(music_url) > 0:
                    if isinstance(music_url[0], dict):
                        music["url"] = music_url[0].get("url", "")
                    else:
                        music["url"] = music_url[0]
        
        # Try from JSON data
        if not music:
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
