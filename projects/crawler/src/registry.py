# -*- coding: utf-8 -*-
"""
Site Registry - 站点注册与管理
"""
from typing import Dict, List, Optional
from dataclasses import dataclass, field
from urllib.parse import urlparse


@dataclass
class SiteConfig:
    """站点配置"""
    name: str
    domains: List[str]
    requires_playwright: bool = False
    priority: int = 50
    cookies: Dict[str, str] = field(default_factory=dict)
    no_proxy: bool = False
    headers: Dict[str, str] = field(default_factory=dict)


class SiteRegistry:
    """站点注册表"""
    
    _sites: Dict[str, SiteConfig] = {}
    _initialized: bool = False
    
    @classmethod
    def initialize(cls, config_path=None):
        """从配置文件加载站点配置"""
        if cls._initialized:
            return
        cls._initialized = True
    
    @classmethod
    def register(cls, name: str, config: SiteConfig):
        """注册站点"""
        cls._sites[name] = config
    
    @classmethod
    def get(cls, name: str) -> Optional[SiteConfig]:
        """获取站点配置"""
        if not cls._initialized:
            cls.initialize()
        return cls._sites.get(name)
    
    @classmethod
    def get_by_domain(cls, domain: str) -> Optional[SiteConfig]:
        """通过域名获取站点配置"""
        if not cls._initialized:
            cls.initialize()
        
        domain = domain.lower()
        
        for site_config in cls._sites.values():
            for site_domain in site_config.domains:
                if site_domain in domain:
                    return site_config
        
        return None
    
    @classmethod
    def detect(cls, url: str) -> Optional[SiteConfig]:
        """通过 URL 检测站点"""
        parsed = urlparse(url)
        return cls.get_by_domain(parsed.netloc)
    
    @classmethod
    def requires_playwright(cls, url: str) -> bool:
        """检测 URL 是否需要 Playwright"""
        site_config = cls.detect(url)
        return site_config.requires_playwright if site_config else False
    
    @classmethod
    def should_use_proxy(cls, url: str, proxy_enabled: bool = True) -> bool:
        """检测 URL 是否应该使用代理"""
        if not proxy_enabled:
            return False
        
        site_config = cls.detect(url)
        if site_config and site_config.no_proxy:
            return False
        
        return True
    
    @classmethod
    def list_sites(cls) -> List[str]:
        """列出所有已注册的站点"""
        if not cls._initialized:
            cls.initialize()
        return list(cls._sites.keys())


# 注册默认站点
def _register_default_sites():
    SiteRegistry.register("zhihu", SiteConfig(
        name="知乎", domains=["zhihu.com", "zhihu.com.cn"],
        requires_playwright=False, priority=75))
    SiteRegistry.register("baidu", SiteConfig(
        name="百度", domains=["baidu.com"],
        requires_playwright=False, priority=70))
    SiteRegistry.register("csdn", SiteConfig(
        name="CSDN", domains=["csdn.net"],
        requires_playwright=True, priority=70, no_proxy=True))
    SiteRegistry.register("juejin", SiteConfig(
        name="稀土掘金", domains=["juejin.cn"],
        requires_playwright=True, priority=70, no_proxy=True))
    SiteRegistry.register("bilibili", SiteConfig(
        name="哔哩哔哩", domains=["bilibili.com"],
        requires_playwright=True, priority=80))
    SiteRegistry.register("douyin", SiteConfig(
        name="抖音", domains=["douyin.com"],
        requires_playwright=True, priority=85))
    SiteRegistry.register("github", SiteConfig(
        name="GitHub", domains=["github.com", "githubusercontent.com"],
        requires_playwright=False, priority=80))
    SiteRegistry.register("gitee", SiteConfig(
        name="Gitee", domains=["gitee.com"],
        requires_playwright=False, priority=80))
    SiteRegistry.register("stackoverflow", SiteConfig(
        name="Stack Overflow", domains=["stackoverflow.com", "stackexchange.com"],
        requires_playwright=False, priority=75))
    SiteRegistry.register("wiki", SiteConfig(
        name="维基百科", domains=["wikipedia.org", "wikidata.org", "baike.baidu.com"],
        requires_playwright=False, priority=90))

_register_default_sites()


__all__ = ['SiteConfig', 'SiteRegistry']
