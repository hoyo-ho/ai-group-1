# -*- coding: utf-8 -*-
"""
GitHub Extractor
"""
import re
from typing import Dict, List
from urllib.parse import urljoin, urlparse
from bs4 import BeautifulSoup

from .base import BaseExtractor


class GithubExtractor(BaseExtractor):
    """GitHub repository extractor"""
    
    priority = 80
    supported_domains = [
        "github.com",
        "githubusercontent.com"
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
        
        # Extract title (repo name)
        title = repo_name
        title_elem = soup.find("title")
        if title_elem:
            title_text = title_elem.get_text(strip=True)
            # Title format: repo-name/README.md at main · owner/repo
            title = title_text.split(" at ")[0].split(" · ")[0].strip()
        
        # Extract description
        description = ""
        desc_elem = soup.find("meta", attrs={"name": "description"})
        if desc_elem:
            description = desc_elem.get("content", "")
        
        # Extract readme content
        content = self._extract_readme(soup, html)
        
        # Extract stars, forks, etc.
        meta = self._extract_repo_meta(soup)
        
        # Extract primary language
        language = self._extract_language(soup)
        if language:
            meta["language"] = language
        
        # Extract topics
        topics = self._extract_topics(soup)
        
        return {
            "url": url,
            "title": title,
            "content": content,
            "description": description,
            "owner": owner,
            "repo_name": repo_name,
            "meta": meta,
            "topics": topics,
            "type": "repository"
        }
    
    def _extract_file(self, url: str, soup: BeautifulSoup, html: str) -> Dict:
        """Extract file content"""
        parsed = urlparse(url)
        path_parts = [p for p in parsed.path.split('/') if p]
        
        owner = path_parts[1] if len(path_parts) > 1 else ""
        repo = path_parts[2] if len(path_parts) > 2 else ""
        
        # File content is often in a blob-wrapper or we need to extract from script
        content = ""
        title = "/".join(path_parts[4:]) if len(path_parts) > 4 else "Unknown"
        
        # Try to find code in pre/code tags
        code_elem = soup.find("pre")
        if code_elem:
            content = code_elem.get_text(separator="\n", strip=True)
        
        # Try React rendered content
        for script in soup.find_all("script"):
            script_text = script.string or ""
            if "blob" in script_text and "content" in script_text:
                # Try to extract from JSON in script
                match = re.search(r'"content":"([^"]+)"', script_text)
                if match:
                    # Decode escape sequences
                    content = match.group(1).encode().decode('unicode_escape')
                    break
        
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
            title = title_text.split("·")[0].strip()
        
        # Bio/description
        bio = ""
        bio_elem = soup.find("meta", attrs={"name": "description"})
        if bio_elem:
            bio = bio_elem.get("content", "")
        
        # Followers, following
        meta = {}
        
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
        readme_div = soup.find("div", id="readme")
        if readme_div:
            return readme_div.get_text(separator="\n", strip=True)
        
        # Try article with markdown-body
        article = soup.find("article", class_="markdown-body")
        if article:
            return article.get_text(separator="\n", strip=True)
        
        # Try general markdown body
        md_body = soup.find("div", class_="markdown-body")
        if md_body:
            return md_body.get_text(separator="\n", strip=True)
        
        return ""
    
    def _extract_repo_meta(self, soup: BeautifulSoup) -> Dict:
        """Extract repository statistics"""
        meta = {}
        
        # Find all social counts
        for link in soup.find_all("a", href=re.compile(r"^/[^/]+/[^/]+/(stargazers|forks|watchers)")):
            span = link.find("span", class_=re.compile(r"Counter|num"))
            if span:
                text = span.get_text(strip=True)
                if "stargazers" in link.get("href", ""):
                    meta["stars"] = text
                elif "forks" in link.get("href", ""):
                    meta["forks"] = text
                elif "watchers" in link.get("href", ""):
                    meta["watchers"] = text
        
        # Try meta og:locale
        locale = soup.find("meta", property="og:locale")
        if locale:
            meta["locale"] = locale.get("content", "")
        
        return meta
    
    def _extract_language(self, soup: BeautifulSoup) -> str:
        """Extract primary programming language"""
        # Try list item with language class
        lang_item = soup.find("li", class_=re.compile(r"language"))
        if lang_item:
            span = lang_item.find("span", class_=re.compile(r"color"))
            if span:
                return span.get_text(strip=True)
        
        # Try meta itemprop
        lang_meta = soup.find("meta", itemprop="programmingLanguage")
        if lang_meta:
            return lang_meta.get("content", "")
        
        return ""
    
    def _extract_topics(self, soup: BeautifulSoup) -> List[str]:
        """Extract repository topics"""
        topics = []
        
        topic_section = soup.find("div", class_=re.compile(r"topics"))
        if topic_section:
            for a in topic_section.find_all("a", class_=re.compile(r"topic-tag")):
                topic = a.get_text(strip=True)
                if topic:
                    topics.append(topic)
        
        return topics
