# -*- coding: utf-8 -*-
"""
Gitee Extractor
"""
import re
from typing import Dict, List
from urllib.parse import urljoin, urlparse
from bs4 import BeautifulSoup

from .base import BaseExtractor


class GiteeExtractor(BaseExtractor):
    """Gitee repository extractor"""
    
    priority = 80
    supported_domains = [
        "gitee.com",
        "gitee.io"
    ]
    
    def extract(self, url: str, html: str) -> Dict:
        soup = BeautifulSoup(html, 'html.parser')
        
        # Determine if it's a repo or user page
        if "/blob/" in url or "/tree/" in url:
            return self._extract_file(url, soup, html)
        elif self._is_user_page(url):
            return self._extract_user(url, soup)
        else:
            return self._extract_repo(url, soup, html)
    
    def _is_user_page(self, url: str) -> bool:
        """Check if URL is a user/organization page (not a repo)"""
        parsed = urlparse(url)
        path_parts = [p for p in parsed.path.split('/') if p]
        # If only 1 path segment, it's a user/org
        return len(path_parts) == 1
    
    def _extract_repo(self, url: str, soup: BeautifulSoup, html: str) -> Dict:
        """Extract repository information"""
        # Extract repo name and owner
        parsed = urlparse(url)
        path_parts = [p for p in parsed.path.split('/') if p]
        
        owner = path_parts[0] if len(path_parts) > 0 else ""
        repo_name = path_parts[1] if len(path_parts) > 1 else ""
        
        # Extract title
        title = repo_name
        title_elem = soup.find("title")
        if title_elem:
            title_text = title_elem.get_text(strip=True)
            title = title_text.split("—")[0].split("-")[0].strip()
        
        # Extract description
        description = ""
        desc_elem = soup.find("meta", attrs={"name": "description"})
        if desc_elem:
            description = desc_elem.get("content", "")
        
        # Description also in og:description
        og_desc = soup.find("meta", property="og:description")
        if og_desc and not description:
            description = og_desc.get("content", "")
        
        # Extract readme content
        content = self._extract_readme(soup, html)
        
        # Extract meta info (stars, forks, etc.)
        meta = self._extract_repo_meta(soup)
        
        # Extract primary language
        language = self._extract_language(soup)
        if language:
            meta["language"] = language
        
        return {
            "url": url,
            "title": title,
            "content": content,
            "description": description,
            "owner": owner,
            "repo_name": repo_name,
            "meta": meta,
            "type": "repository"
        }
    
    def _extract_file(self, url: str, soup: BeautifulSoup, html: str) -> Dict:
        """Extract file content"""
        parsed = urlparse(url)
        path_parts = [p for p in parsed.path.split('/') if p]
        
        owner = path_parts[0] if len(path_parts) > 0 else ""
        repo = path_parts[1] if len(path_parts) > 1 else ""
        
        # File name
        title = "/".join(path_parts[3:]) if len(path_parts) > 3 else "Unknown"
        
        # Try to find code in pre/code tags
        content = ""
        code_elem = soup.find("pre", class_="code-viewer")
        if code_elem:
            content = code_elem.get_text(separator="\n", strip=True)
        else:
            code_elem = soup.find("code")
            if code_elem:
                content = code_elem.get_text(separator="\n", strip=True)
        
        return {
            "url": url,
            "title": title,
            "content": content,
            "owner": owner,
            "repo_name": repo,
            "type": "file"
        }
    
    def _extract_user(self, url: str, soup: BeautifulSoup) -> Dict:
        """Extract user/organization information"""
        parsed = urlparse(url)
        username = parsed.path.strip('/')
        
        # Title
        title = username
        title_elem = soup.find("title")
        if title_elem:
            title_text = title_elem.get_text(strip=True)
            title = title_text.split("—")[0].split("-")[0].strip()
        
        # Bio/description
        bio = ""
        bio_elem = soup.find("meta", attrs={"name": "description"})
        if bio_elem:
            bio = bio_elem.get("content", "")
        
        # Extract profile info
        meta = self._extract_user_meta(soup)
        
        return {
            "url": url,
            "title": title,
            "content": bio,
            "username": username,
            "meta": meta,
            "type": "user"
        }
    
    def _extract_readme(self, soup: BeautifulSoup, html: str) -> str:
        """Extract README content"""
        # Try to find readme in the repository
        readme_div = soup.find("div", class_="readme")
        if readme_div:
            return readme_div.get_text(separator="\n", strip=True)
        
        # Try markdown content
        md_div = soup.find("div", class_=re.compile(r"markdown|readme-view"))
        if md_div:
            return md_div.get_text(separator="\n", strip=True)
        
        # Try article
        article = soup.find("article")
        if article:
            return article.get_text(separator="\n", strip=True)
        
        return ""
    
    def _extract_repo_meta(self, soup: BeautifulSoup) -> Dict:
        """Extract repository statistics"""
        meta = {}
        
        # Stars, forks, watches
        stats_div = soup.find("div", class_=re.compile(r"statistic|stats"))
        if stats_div:
            for item in stats_div.find_all("li") + stats_div.find_all("span"):
                text = item.get_text(strip=True)
                if "星" in text or "star" in text.lower():
                    match = re.search(r'(\d+)', text)
                    if match:
                        meta["stars"] = match.group(1)
                elif "Fork" in text or "叉" in text:
                    match = re.search(r'(\d+)', text)
                    if match:
                        meta["forks"] = match.group(1)
                elif "Watch" in text or "关" in text:
                    match = re.search(r'(\d+)', text)
                    if match:
                        meta["watches"] = match.group(1)
        
        # Try meta tags
        og_image = soup.find("meta", property="og:image")
        if og_image:
            meta["og_image"] = og_image.get("content", "")
        
        return meta
    
    def _extract_user_meta(self, soup: BeautifulSoup) -> Dict:
        """Extract user profile information"""
        meta = {}
        
        # Location
        location_elem = soup.find("span", class_=re.compile(r"location|地区"))
        if location_elem:
            meta["location"] = location_elem.get_text(strip=True)
        
        # Company
        company_elem = soup.find("span", class_=re.compile(r"company|公司"))
        if company_elem:
            meta["company"] = company_elem.get_text(strip=True)
        
        # Followers
        followers_elem = soup.find("a", href=re.compile(r"followers|粉丝"))
        if followers_elem:
            meta["followers"] = followers_elem.get_text(strip=True)
        
        return meta
    
    def _extract_language(self, soup: BeautifulSoup) -> str:
        """Extract primary programming language"""
        # Try language bar
        lang_bar = soup.find("div", class_=re.compile(r"language|编程语言"))
        if lang_bar:
            span = lang_bar.find("span")
            if span:
                return span.get_text(strip=True)
        
        return ""
