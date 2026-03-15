# -*- coding: utf-8 -*-
"""
Content Extractors
"""
import re
from typing import Dict, List, Optional
from urllib.parse import urljoin, urlparse
import requests
from bs4 import BeautifulSoup


class BaseExtractor:
    """Base content extractor"""
    
    def __init__(self, timeout: int = 30):
        self.timeout = timeout
    
    def extract(self, url: str, html: str) -> Dict:
        """Extract content from HTML"""
        raise NotImplementedError


class GeneralExtractor(BaseExtractor):
    """General web page extractor"""
    
    def extract(self, url: str, html: str) -> Dict:
        soup = BeautifulSoup(html, 'html.parser')
        
        # Remove script and style elements
        for script in soup(["script", "style", "nav", "footer", "header"]):
            script.decompose()
        
        # Extract title
        title = self._extract_title(soup)
        
        # Extract main content
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
            "meta": meta
        }
    
    def _extract_title(self, soup: BeautifulSoup) -> str:
        # Try og:title first
        og_title = soup.find("meta", property="og:title")
        if og_title:
            return og_title.get("content", "")
        
        # Try h1
        h1 = soup.find("h1")
        if h1:
            return h1.get_text(strip=True)
        
        # Try title tag
        title = soup.find("title")
        if title:
            return title.get_text(strip=True)
        
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
        for cls in ["content", "article", "post", "entry", "main-content"]:
            elem = soup.find(class_=cls)
            if elem:
                return elem.get_text(separator="\n", strip=True)
        
        # Fallback to body
        body = soup.find("body")
        if body:
            return body.get_text(separator="\n", strip=True)
        
        return ""
    
    def _extract_images(self, soup: BeautifulSoup, base_url: str) -> List[Dict]:
        images = []
        for img in soup.find_all("img"):
            src = img.get("src") or img.get("data-src") or img.get("data-lazy")
            if src:
                full_url = urljoin(base_url, src)
                alt = img.get("alt", "")
                images.append({
                    "url": full_url,
                    "alt": alt
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
        
        # Author
        author = soup.find("meta", attrs={"name": "author"})
        if author:
            meta["author"] = author.get("content", "")
        
        # Published time
        pub_time = soup.find("meta", property="article:published_time")
        if pub_time:
            meta["published_time"] = pub_time.get("content", "")
        
        return meta


class GitHubExtractor(BaseExtractor):
    """GitHub repository/page extractor"""
    
    def extract(self, url: str, html: str) -> Dict:
        soup = BeautifulSoup(html, 'html.parser')
        
        # Extract repo name
        repo_name = self._extract_repo_name(soup, url)
        
        # Extract description
        description = self._extract_description(soup)
        
        # Extract stars, forks, etc.
        stats = self._extract_stats(soup)
        
        # Extract readme content
        readme = self._extract_readme(soup)
        
        # Extract programming language
        language = self._extract_language(soup)
        
        return {
            "url": url,
            "repo_name": repo_name,
            "description": description,
            "stats": stats,
            "readme": readme,
            "language": language
        }
    
    def _extract_repo_name(self, soup: BeautifulSoup, url: str) -> str:
        # Try og:title
        og_title = soup.find("meta", property="og:title")
        if og_title:
            return og_title.get("content", "")
        
        # Extract from URL
        parsed = urlparse(url)
        path_parts = [p for p in parsed.path.split("/") if p]
        if len(path_parts) >= 2:
            return "/".join(path_parts[:2])
        
        return ""
    
    def _extract_description(self, soup: BeautifulSoup) -> str:
        og_desc = soup.find("meta", property="og:description")
        if og_desc:
            return og_desc.get("content", "")
        
        # Try repository description
        desc_elem = soup.find("span", itemprop="description")
        if desc_elem:
            return desc_elem.get_text(strip=True)
        
        return ""
    
    def _extract_stats(self, soup: BeautifulSoup) -> Dict:
        stats = {}
        
        # Find all anchor tags with aria-label
        for a in soup.find_all("a", href=True):
            aria_label = a.get("aria-label", "")
            if "star" in aria_label.lower():
                stats["stars"] = aria_label.strip()
            elif "fork" in aria_label.lower():
                stats["forks"] = aria_label.strip()
            elif "watch" in aria_label.lower():
                stats["watchers"] = aria_label.strip()
        
        return stats
    
    def _extract_readme(self, soup: BeautifulSoup) -> str:
        # Readme is usually rendered in markdown
        readme_div = soup.find("article", class_="markdown-body")
        if readme_div:
            return readme_div.get_text(separator="\n", strip=True)
        
        return ""
    
    def _extract_language(self, soup: BeautifulSoup) -> str:
        # Find language itemprop
        lang = soup.find(itemprop="programmingLanguage")
        if lang:
            return lang.get_text(strip=True)
        
        # Find language span
        lang_span = soup.find("span", itemprop="programmingLanguage")
        if lang_span:
            return lang_span.get_text(strip=True)
        
        return ""


class ImageExtractor(BaseExtractor):
    """Image website extractor"""
    
    def extract(self, url: str, html: str) -> Dict:
        soup = BeautifulSoup(html, 'html.parser')
        
        # Extract image URLs
        images = self._extract_images(soup, url)
        
        # Extract title
        title = self._extract_title(soup)
        
        # Extract author info
        author = self._extract_author(soup)
        
        # Extract license info
        license_info = self._extract_license(soup)
        
        return {
            "url": url,
            "title": title,
            "images": images,
            "author": author,
            "license": license_info
        }
    
    def _extract_images(self, soup: BeautifulSoup, base_url: str) -> List[Dict]:
        images = []
        
        # Find image containers
        for img in soup.find_all("img"):
            src = img.get("src") or img.get("data-src") or img.get("data-lazy")
            if src:
                full_url = urljoin(base_url, src)
                alt = img.get("alt", "")
                images.append({
                    "url": full_url,
                    "alt": alt,
                    "type": "img"
                })
        
        # Find anchor links to images
        for a in soup.find_all("a", href=True):
            href = a.get("href", "")
            if any(href.lower().endswith(ext) for ext in [".jpg", ".jpeg", ".png", ".gif", ".webp"]):
                full_url = urljoin(base_url, href)
                images.append({
                    "url": full_url,
                    "alt": a.get("title", ""),
                    "type": "link"
                })
        
        return images
    
    def _extract_title(self, soup: BeautifulSoup) -> str:
        og_title = soup.find("meta", property="og:title")
        if og_title:
            return og_title.get("content", "")
        
        h1 = soup.find("h1")
        if h1:
            return h1.get_text(strip=True)
        
        return ""
    
    def _extract_author(self, soup: BeautifulSoup) -> str:
        # Try meta author
        author = soup.find("meta", attrs={"name": "author"})
        if author:
            return author.get("content", "")
        
        # Try link to author
        author_link = soup.find("a", rel="author")
        if author_link:
            return author_link.get_text(strip=True)
        
        return ""
    
    def _extract_license(self, soup: BeautifulSoup) -> str:
        # Try meta
        license_elem = soup.find("meta", attrs={"name": "license"})
        if license_elem:
            return license_elem.get("content", "")
        
        return ""


class BilibiliExtractor(BaseExtractor):
    """Bilibili video extractor"""
    
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
                        import json
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


def get_extractor(url: str) -> BaseExtractor:
    """Get appropriate extractor based on URL"""
    parsed = urlparse(url)
    hostname = parsed.netloc.lower()
    
    if "github.com" in hostname or "githubusercontent.com" in hostname:
        return GitHubExtractor()
    elif "bilibili.com" in hostname:
        return BilibiliExtractor()
    elif any(site in hostname for site in ["unsplash.com", "pexels.com", "pixabay.com", "flickr.com", "imgur.com"]):
        return ImageExtractor()
    else:
        return GeneralExtractor()
