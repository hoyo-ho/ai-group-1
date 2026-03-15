# -*- coding: utf-8 -*-
"""
Extractors Package - URL-based Content Extractors

This module provides extractors for various website types with priority-based selection.
"""
from typing import Dict, List, Type, Optional
from urllib.parse import urlparse

# Import all extractors
from .base import BaseExtractor, get_priority
from .general import GeneralExtractor
from .bilibili import BilibiliExtractor
from .douyin import DouyinExtractor
from .baidu import BaiduExtractor
from .wiki import WikiExtractor
from .sohu import SohuExtractor
from .quark import QuarkExtractor
from .csdn import CsdnExtractor
from .cnblogs import CnblogsExtractor
from .juejin import JuejinExtractor
from .segmentfault import SegmentfaultExtractor
from .github import GithubExtractor
from .gitee import GiteeExtractor
from .zhihu import ZhihuExtractor
from .stackoverflow import StackoverflowExtractor


# Registry of all extractors with their priorities
# Higher priority = more specific to that site
EXTRACTOR_REGISTRY: List[Type[BaseExtractor]] = [
    # High priority: specific site extractors
    WikiExtractor,      # Priority 90 - handles baike.baidu.com, wikipedia.org
    DouyinExtractor,   # Priority 85 - Douyin/TikTok China (must use Playwright)
    BilibiliExtractor, # Priority 80 - Bilibili video
    GithubExtractor,   # Priority 80 - GitHub repository
    GiteeExtractor,    # Priority 80 - Gitee repository
    StackoverflowExtractor, # Priority 75 - Stack Overflow Q&A
    ZhihuExtractor,    # Priority 75 - Zhihu Q&A
    BaiduExtractor,    # Priority 70 - Baidu search results
    QuarkExtractor,    # Priority 65 - Quark search/cloud
    SohuExtractor,     # Priority 60 - Sohu search/article
    CsdnExtractor,     # Priority 70 - CSDN blog
    CnblogsExtractor,  # Priority 70 - 博客园
    JuejinExtractor,   # Priority 70 - 稀土掘金
    SegmentfaultExtractor, # Priority 70 - SegmentFault
    
    # Low priority: general fallback
    GeneralExtractor,   # Priority 10 - general web pages
]


def get_extractor(url: str, site_type: str = None) -> BaseExtractor:
    """
    Get the appropriate extractor based on URL and optional site type hint.
    
    Args:
        url: The URL to extract content from
        site_type: Optional site type hint (e.g., 'wiki', 'baidu', 'douyin')
    
    Returns:
        An instance of the appropriate BaseExtractor subclass
    """
    # If site_type is explicitly provided, try to find matching extractor
    if site_type:
        extractor_class = _get_extractor_by_type(site_type)
        if extractor_class:
            return extractor_class()
    
    # Otherwise, auto-detect based on URL
    extractor_class = _get_extractor_by_url(url)
    if extractor_class:
        return extractor_class()
    
    # Fallback to general extractor
    return GeneralExtractor()


def _get_extractor_by_type(site_type: str) -> Optional[Type[BaseExtractor]]:
    """Get extractor class by site type name"""
    type_map = {
        "wiki": WikiExtractor,
        "baike": WikiExtractor,
        "baidu": BaiduExtractor,
        "bilibili": BilibiliExtractor,
        "douyin": DouyinExtractor,
        "sohu": SohuExtractor,
        "quark": QuarkExtractor,
        "csdn": CsdnExtractor,
        "cnblogs": CnblogsExtractor,
        "juejin": JuejinExtractor,
        "segmentfault": SegmentfaultExtractor,
        "github": GithubExtractor,
        "gitee": GiteeExtractor,
        "zhihu": ZhihuExtractor,
        "stackoverflow": StackoverflowExtractor,
        "general": GeneralExtractor,
    }
    
    site_type_lower = site_type.lower().strip()
    return type_map.get(site_type_lower)


def _get_extractor_by_url(url: str) -> Optional[Type[BaseExtractor]]:
    """
    Auto-detect the best extractor based on URL using priority matching.
    
    Higher priority extractors are checked first. Returns the first matching extractor.
    """
    url_lower = url.lower()
    
    # Sort extractors by priority (highest first)
    sorted_extractors = sorted(
        [e for e in EXTRACTOR_REGISTRY if hasattr(e, 'supported_domains')],
        key=get_priority,
        reverse=True
    )
    
    for extractor_class in sorted_extractors:
        # Check if any supported domain matches the URL
        for domain in extractor_class.supported_domains:
            if domain in url_lower:
                return extractor_class
    
    return None


def get_extractor_for_playwright(url: str) -> bool:
    """
    Check if a URL requires Playwright for proper content extraction.
    
    Returns True if the site is known to need JavaScript rendering.
    """
    playwright_domains = [
        "douyin.com",
        "bilibili.com",
        "weibo.com",
        "twitter.com",
        "x.com",
        "facebook.com",
        "instagram.com",
        "reddit.com",
        "taobao.com",
        "jd.com",
        "tmall.com",
        "csdn.net",
        "juejin.cn",
        "segmentfault.com",
    ]
    
    url_lower = url.lower()
    return any(domain in url_lower for domain in playwright_domains)


# Export all extractor classes for convenience
__all__ = [
    "BaseExtractor",
    "GeneralExtractor",
    "BilibiliExtractor",
    "DouyinExtractor",
    "BaiduExtractor",
    "WikiExtractor",
    "SohuExtractor",
    "QuarkExtractor",
    "CsdnExtractor",
    "CnblogsExtractor",
    "JuejinExtractor",
    "SegmentfaultExtractor",
    "GithubExtractor",
    "GiteeExtractor",
    "ZhihuExtractor",
    "StackoverflowExtractor",
    "get_extractor",
    "get_extractor_for_playwright",
    "EXTRACTOR_REGISTRY",
]
