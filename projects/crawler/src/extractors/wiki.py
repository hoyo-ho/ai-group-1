# -*- coding: utf-8 -*-
"""
Wiki/Baike Extractor - Handles encyclopedia content
"""
import re
from typing import Dict, List
from urllib.parse import urljoin
from bs4 import BeautifulSoup

from .base import BaseExtractor


class WikiExtractor(BaseExtractor):
    """Encyclopedia content extractor - handles Baidu Baike, Wikipedia, etc."""
    
    priority = 90  # High priority for encyclopedia sites
    supported_domains = [
        "baike.baidu.com",
        "wikipedia.org",
        "zh.wikipedia.org",
        "en.wikipedia.org",
        "wikidata.org",
        "baike.com"
    ]
    
    def extract(self, url: str, html: str) -> Dict:
        soup = BeautifulSoup(html, 'html.parser')
        
        # Extract title
        title = self._extract_title(soup, url)
        
        # Extract main content
        content = self._extract_content(soup)
        
        # Extract summary/abstract
        summary = self._extract_summary(soup)
        
        # Extract infobox
        infobox = self._extract_infobox(soup)
        
        # Extract images
        images = self._extract_images(soup, url)
        
        # Extract metadata
        meta = self._extract_meta(soup)
        
        # Extract references
        references = self._extract_references(soup)
        
        # Extract sections
        sections = self._extract_sections(soup)
        
        return {
            "url": url,
            "title": title,
            "summary": summary,
            "content": content,
            "infobox": infobox,
            "images": images,
            "meta": meta,
            "references": references,
            "sections": sections
        }
    
    def _extract_title(self, soup: BeautifulSoup, url: str) -> str:
        # Try og:title first
        og_title = soup.find("meta", property="og:title")
        if og_title:
            return og_title.get("content", "")
        
        # Try h1
        h1 = soup.find("h1")
        if h1:
            return h1.get_text(strip=True)
        
        # Try title tag
        title_tag = soup.find("title")
        if title_tag:
            title = title_tag.get_text(strip=True)
            # Clean common suffixes
            title = re.sub(r'[-_]百度百科.*$', '', title)
            title = re.sub(r'[-_]Wikipedia.*$', '', title)
            return title.strip()
        
        return ""
    
    def _extract_summary(self, soup: BeautifulSoup) -> str:
        # Baidu Baike: .lemma-summary
        summary_div = soup.find("div", class_="lemma-summary")
        if summary_div:
            return summary_div.get_text(separator="\n", strip=True)
        
        # Wikipedia: .mw-parser-output > p (first paragraph)
        mw_content = soup.find("div", class_="mw-parser-output")
        if mw_content:
            for p in mw_content.find_all("p", class_=None):
                text = p.get_text(strip=True)
                if text and len(text) > 50:  # Skip short/empty paragraphs
                    # Clean references [1], [2], etc.
                    text = re.sub(r'\[(\d+)\]', '', text)
                    return text
        
        return ""
    
    def _extract_content(self, soup: BeautifulSoup) -> str:
        # Try id first (newer Wikipedia)
        content_div = soup.find(id="mw-content-text")
        if content_div:
            # Only remove script and style, keep rest
            for elem in content_div(["script", "style"]):
                elem.decompose()
            text = content_div.get_text(separator="\n", strip=True)
            # Clean up excessive newlines
            import re
            text = re.sub(r'\n\n+', '\n', text)
            return text
        
        # Try class (older Wikipedia)
        mw_content = soup.find("div", class_="mw-parser-output")
        if mw_content:
            for elem in mw_content(["script", "style"]):
                elem.decompose()
            text = mw_content.get_text(separator="\n", strip=True)
            import re
            text = re.sub(r'\n\n+', '\n', text)
            return text
        
        # Baidu Baike: .lemma-content
        content_div = soup.find("div", class_="lemma-content")
        if content_div:
            for elem in content_div(["script", "style", "aside"]):
                elem.decompose()
            return content_div.get_text(separator="\n", strip=True)
        
        return ""
    
    def _extract_infobox(self, soup: BeautifulSoup) -> Dict:
        infobox = {}
        
        # Baidu Baike: .basic-info
        basic_info = soup.find("div", class_="basic-info")
        if basic_info:
            for dl in basic_info.find_all("dl"):
                dt = dl.find("dt")
                dd = dl.find("dd")
                if dt and dd:
                    key = dt.get_text(strip=True)
                    value = dd.get_text(strip=True)
                    if key and value:
                        infobox[key] = value
            return infobox
        
        # Wikipedia: .infobox
        infobox_table = soup.find("table", class_="infobox")
        if infobox_table:
            for row in infobox_table.find_all("tr"):
                th = row.find("th")
                td = row.find("td")
                if th and td:
                    key = th.get_text(strip=True)
                    value = td.get_text(strip=True)
                    if key and value:
                        infobox[key] = value
        
        return infobox
    
    def _extract_images(self, soup: BeautifulSoup, base_url: str) -> List[Dict]:
        images = []
        
        # Baidu Baike: .summary-pic
        summary_pic = soup.find("div", class_="summary-pic")
        if summary_pic:
            img = summary_pic.find("img")
            if img:
                src = img.get("src") or img.get("data-src")
                if src:
                    images.append({
                        "url": urljoin(base_url, src),
                        "type": "summary"
                    })
        
        # Wikipedia: .thumbinner
        for thumb in soup.find_all("div", class_="thumbinner"):
            img = thumb.find("img")
            if img:
                src = img.get("src") or img.get("data-file-width")
                if src and isinstance(src, str):
                    images.append({
                        "url": urljoin(base_url, src),
                        "type": "thumbnail"
                    })
        
        # Generic og:image
        og_image = soup.find("meta", property="og:image")
        if og_image:
            images.append({
                "url": og_image.get("content", ""),
                "type": "og:image"
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
    
    def _extract_references(self, soup: BeautifulSoup) -> List[str]:
        references = []
        
        # Wikipedia references
        ref_list = soup.find("ol", class_="references")
        if ref_list:
            for li in ref_list.find_all("li"):
                ref_text = li.get_text(strip=True)
                if ref_text:
                    references.append(ref_text)
        
        return references
    
    def _extract_sections(self, soup: BeautifulSoup) -> List[Dict]:
        sections = []
        
        # Wikipedia section structure
        for h2 in soup.find_all("h2"):
            section_title = h2.get_text(strip=True)
            # Remove [edit] links
            section_title = re.sub(r'\[edit\]', '', section_title)
            
            # Get content until next h2
            content_parts = []
            for sibling in h2.find_next_siblings():
                if sibling.name == "h2":
                    break
                if sibling.name in ["h3", "h4", "p", "ul", "ol"]:
                    text = sibling.get_text(strip=True)
                    if text:
                        content_parts.append(text)
            
            if section_title and content_parts:
                sections.append({
                    "title": section_title,
                    "content": "\n".join(content_parts)
                })
        
        return sections
