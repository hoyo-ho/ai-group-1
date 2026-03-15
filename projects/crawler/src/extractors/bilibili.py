# -*- coding: utf-8 -*-
"""
Bilibili Video Extractor
"""
import re
import json
from typing import Dict, List
from urllib.parse import urljoin
from bs4 import BeautifulSoup

from .base import BaseExtractor


class BilibiliExtractor(BaseExtractor):
    """Bilibili video extractor"""
    
    priority = 80
    supported_domains = ["bilibili.com"]
    
    def extract(self, url: str, html: str) -> Dict:
        soup = BeautifulSoup(html, 'html.parser')
        
        # Extract title
        title = self._extract_title(soup)
        
        # Extract video links
        videos = self._extract_video_links(soup, url)
        
        # Extract images (cover, thumbnails)
        images = self._extract_images(soup, url)
        
        # Extract meta info
        meta = self._extract_meta(soup)
        
        # Extract description
        description = self._extract_description(soup)
        
        return {
            "url": url,
            "title": title,
            "videos": videos,
            "images": images,
            "meta": meta,
            "description": description
        }
    
    def _extract_title(self, soup: BeautifulSoup) -> str:
        """Extract video title with improved logic"""
        # Try og:title first (usually has clean title)
        og_title = soup.find("meta", property="og:title")
        if og_title:
            title = og_title.get("content", "")
            # Clean common suffixes
            title = re.sub(r'[_-]哔哩哔哩.*$', '', title)
            title = re.sub(r'[_-]bilibili.*$', '', title, flags=re.IGNORECASE)
            if title:
                return title.strip()
        
        # Try __INITIAL_STATE__ title via script
        for script in soup.find_all("script"):
            script_text = script.string or ""
            if "__INITIAL_STATE__" in script_text:
                match = re.search(r'"title":"([^"]+)"', script_text)
                if match:
                    title = match.group(1)
                    title = title.replace('\\u0026', '&').replace('\\n', '')
                    if title and len(title) < 200:
                        return title
        
        # Try h1 with specific classes
        for h1 in soup.find_all("h1"):
            title = h1.get_text(strip=True)
            if title and len(title) < 200:
                return title
        
        # Try title tag
        title_tag = soup.find("title")
        if title_tag:
            title = title_tag.get_text(strip=True)
            title = re.sub(r'[_-]哔哩哔哩.*$', '', title)
            if title:
                return title.strip()
        
        return ""
    
    def _extract_video_links(self, soup: BeautifulSoup, base_url: str) -> List[Dict]:
        """Extract video links from Bilibili page"""
        videos = []
        
        # Extract current video BV from URL
        current_bvid = None
        match = re.search(r'/video/(BV[a-zA-Z0-9]{10})', base_url)
        if match:
            current_bvid = match.group(1)
        
        # Method 1: Extract from window.__INITIAL_STATE__ (most reliable)
        for script in soup.find_all("script"):
            script_text = script.string or ""
            
            if "__INITIAL_STATE__" in script_text:
                match = re.search(r'window\.__INITIAL_STATE__\s*=\s*({.*?});', script_text, re.DOTALL)
                if match:
                    try:
                        data = json.loads(match.group(1))
                        
                        # Navigate to video info - this is the CURRENT video
                        if "videoData" in data:
                            video_data = data["videoData"]
                            bvid = video_data.get("bvid", "")
                            title = video_data.get("title", "")
                            if bvid:
                                videos.append({
                                    "title": title,
                                    "url": f"https://www.bilibili.com/video/{bvid}",
                                    "bvid": bvid,
                                    "is_current": True,
                                    "type": "current"
                                })
                        
                        # Handle multi-part videos (playlist)
                        if "videoData" in data and "pages" in data["videoData"]:
                            for page in data["videoData"]["pages"]:
                                page_bvid = data["videoData"].get("bvid", bvid)
                                videos.append({
                                    "title": page.get("part", f"P{page.get('page','')}"),
                                    "url": f"https://www.bilibili.com/video/{page_bvid}?p={page.get('page','')}",
                                    "bvid": page_bvid,
                                    "page": page.get("page", ""),
                                    "is_current": True,
                                    "type": "playlist"
                                })
                                
                        # Handle season/series (番剧、课程等)
                        if "section" in data:
                            for section in data["section"]:
                                for page in section.get("pages", []):
                                    videos.append({
                                        "title": page.get("title", ""),
                                        "url": f"https://www.bilibili.com/video/{page.get('bvid','')}",
                                        "bvid": page.get("bvid", ""),
                                        "is_current": True,
                                        "type": "season"
                                    })
                    except Exception:
                        pass
        
        # Method 2: Extract from meta tags (og:url - current video)
        og_url = soup.find("meta", property="og:url")
        if og_url:
            og_url_content = og_url.get("content", "")
            if "bilibili.com/video/" in og_url_content:
                # Clean URL (remove query params)
                clean_url = re.sub(r'\?.*', '', og_url_content)
                if not any(v.get("url", "").startswith(clean_url) for v in videos):
                    videos.append({
                        "title": "",
                        "url": clean_url,
                        "is_current": True,
                        "type": "meta"
                    })
        
        # Method 3: Extract from page links, but FILTER OUT recommended videos
        # Recommended videos have query params like: ?spm_id_from=333.788...
        for a in soup.find_all("a", href=True):
            href = a.get("href", "")
            if "/video/" in href:
                # Skip if it's a recommended video (has spm_id_from parameter)
                if "spm_id_from=333.788" in href or "spm_id_from=333.1007" in href:
                    continue
                
                # Extract clean BV URL
                bv_match = re.search(r'(BV[a-zA-Z0-9]{10})', href)
                if bv_match:
                    bvid = bv_match.group(1)
                    # Skip if it's the current video (already extracted)
                    if current_bvid and bvid == current_bvid:
                        continue
                    
                    # Clean URL
                    clean_url = re.sub(r'\?.*', '', f"https://www.bilibili.com{href}")
                    
                    # Get title from the link text
                    title = a.get_text(strip=True)
                    if title and len(title) < 200:
                        # Check if not already added
                        if not any(v.get("url") == clean_url for v in videos):
                            videos.append({
                                "title": title,
                                "url": clean_url,
                                "bvid": bvid,
                                "is_current": False,
                                "type": "related"
                            })
        
        return videos
    
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
                # Try to find image URLs in JSON
                img_matches = re.findall(r'(https?://[^\s"\'<>]+\.(?:jpg|jpeg|png|gif|webp)[^\s"\'<>]*)', script_text)
                for img in set(img_matches):
                    if "bilibili" in img.lower() or "hdslb" in img:
                        images.append({
                            "url": img,
                            "type": "script"
                        })
                        break
        
        return images
    
    def _extract_meta(self, soup: BeautifulSoup) -> Dict:
        meta = {}
        
        # Description
        og_desc = soup.find("meta", property="og:description")
        if og_desc:
            meta["description"] = og_desc.get("content", "")
        
        # Author
        author = soup.find("meta", attrs={"name": "author"})
        if author:
            meta["author"] = author.get("content", "")
        
        # Published time
        pub_time = soup.find("meta", property="video:release_date")
        if pub_time:
            meta["published_time"] = pub_time.get("content", "")
        
        return meta
    
    def _extract_description(self, soup: BeautifulSoup) -> str:
        # Try og:description
        og_desc = soup.find("meta", property="og:description")
        if og_desc:
            return og_desc.get("content", "")
        
        # Try description div
        desc_div = soup.find("div", class_="desc")
        if desc_div:
            return desc_div.get_text(strip=True)
        
        return ""
