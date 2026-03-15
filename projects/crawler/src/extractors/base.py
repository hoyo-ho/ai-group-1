# -*- coding: utf-8 -*-
"""
Base Extractor Classes
"""
from typing import Dict, List, Optional
from dataclasses import dataclass, field


@dataclass
class ExtractionResult:
    """Result of content extraction"""
    url: str
    title: str = ""
    content: str = ""
    images: List[Dict] = field(default_factory=list)
    videos: List[Dict] = field(default_factory=list)
    meta: Dict = field(default_factory=dict)
    raw_data: Dict = field(default_factory=dict)
    
    def to_dict(self) -> Dict:
        """Convert to dictionary"""
        return {
            "url": self.url,
            "title": self.title,
            "content": self.content,
            "images": self.images,
            "videos": self.videos,
            "meta": self.meta,
            "raw_data": self.raw_data
        }


class BaseExtractor:
    """Base content extractor"""
    
    # Priority for URL matching (higher = more specific)
    priority: int = 0
    
    # Supported domains (list of domain patterns)
    supported_domains: List[str] = []
    
    def __init__(self, timeout: int = 30):
        self.timeout = timeout
    
    def extract(self, url: str, html: str) -> Dict:
        """Extract content from HTML"""
        raise NotImplementedError
    
    def supports_url(self, url: str) -> bool:
        """Check if this extractor supports the given URL"""
        if not self.supported_domains:
            return False
        
        url_lower = url.lower()
        return any(domain in url_lower for domain in self.supported_domains)


def get_priority(extractor_class) -> int:
    """Get priority from extractor class"""
    return getattr(extractor_class, 'priority', 0)
