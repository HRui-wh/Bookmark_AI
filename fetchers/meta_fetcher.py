"""
元数据获取器
负责从网站获取标题和描述等元数据
"""
import asyncio
import logging
import random
import time
from typing import Dict, Tuple, List
import requests
from bs4 import BeautifulSoup
import urllib3
from urllib3.util.retry import Retry
from requests.adapters import HTTPAdapter

from config import config
from utils.decorators import async_retry
from utils.logger import get_logger

# 禁用SSL警告
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

logger = get_logger("bookmark_organizer")

# 常用User-Agent列表，用于轮换
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/121.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1 Safari/605.1.15",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Edge/120.0.0.0",
]


class MetaFetcher:
    """
    元数据获取器类
    负责并发获取网站的标题和描述信息
    """
    
    def __init__(self, max_concurrency: int = None):
        """
        初始化元数据获取器
        
        Args:
            max_concurrency: 最大并发数，如果为None则使用配置中的默认值
        """
        self._cache: Dict[str, Tuple[str, str]] = {}
        self.max_concurrency = max_concurrency or config.network.max_concurrency
        self.semaphore = asyncio.Semaphore(self.max_concurrency)
        
        logger.info(f"初始化元数据获取器，最大并发数: {self.max_concurrency}")
    
    @async_retry(max_attempts=2, delay=1.0)
    async def get_meta_single(self, url: str) -> Tuple[str, str]:
        """
        获取单个URL的元数据
        
        Args:
            url: 目标URL
            
        Returns:
            (标题, 描述) 元组
        """
        async with self.semaphore:
            return await asyncio.to_thread(self._sync_get_meta, url)
    
    def _sync_get_meta(self, url: str) -> Tuple[str, str]:
        """
        同步获取元数据，包含防爬虫绕过机制
        
        Args:
            url: 目标URL
            
        Returns:
            (标题, 描述) 元组
        """
        # 检查缓存
        if url in self._cache:
            logger.debug(f"从缓存获取元数据: {url}")
            return self._cache[url]
        
        if not url or not url.startswith(('http', 'https')):
            logger.warning(f"无效的URL: {url}")
            return "无标题", "无描述"
        
        # 尝试多种策略获取元数据
        strategies = [
            self._try_normal_request,
            self._try_with_rotating_headers,
            self._try_with_delayed_request,
            self._try_with_alternative_headers
        ]
        
        for i, strategy in enumerate(strategies):
            try:
                result = strategy(url)
                if result and result[0] != "无标题":
                    logger.debug(f"策略 {i+1} 成功获取元数据: {url} -> {result[0]}")
                    self._cache[url] = result
                    return result
            except Exception as e:
                logger.debug(f"策略 {i+1} 失败 {url}: {e}")
                continue
        
        # 所有策略都失败，返回默认值
        logger.warning(f"所有获取策略都失败: {url}")
        result = ("无标题", "无描述")
        self._cache[url] = result
        return result
    
    def _try_normal_request(self, url: str) -> Tuple[str, str]:
        """标准请求策略"""
        session = requests.Session()
        retry_strategy = Retry(
            total=config.network.max_retries,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504],
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        session.mount("http://", adapter)
        session.mount("https://", adapter)
        
        headers = {"User-Agent": config.network.user_agent}
        response = session.get(
            url, 
            timeout=config.network.timeout, 
            headers=headers, 
            verify=False
        )
        response.raise_for_status()
        
        return self._extract_meta_from_html(response.text)
    
    def _try_with_rotating_headers(self, url: str) -> Tuple[str, str]:
        """轮换User-Agent策略"""
        session = requests.Session()
        retry_strategy = Retry(
            total=config.network.max_retries,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504],
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        session.mount("http://", adapter)
        session.mount("https://", adapter)
        
        # 随机选择User-Agent
        user_agent = random.choice(USER_AGENTS)
        headers = {
            "User-Agent": user_agent,
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
            "Accept-Encoding": "gzip, deflate, br",
            "DNT": "1",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1",
        }
        
        response = session.get(
            url, 
            timeout=config.network.timeout, 
            headers=headers, 
            verify=False
        )
        response.raise_for_status()
        
        return self._extract_meta_from_html(response.text)
    
    def _try_with_delayed_request(self, url: str) -> Tuple[str, str]:
        """延迟请求策略"""
        # 随机延迟0.5-2秒
        time.sleep(random.uniform(0.5, 2.0))
        
        session = requests.Session()
        retry_strategy = Retry(
            total=config.network.max_retries,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504],
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        session.mount("http://", adapter)
        session.mount("https://", adapter)
        
        headers = {
            "User-Agent": random.choice(USER_AGENTS),
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5",
            "Accept-Encoding": "gzip, deflate",
            "Connection": "keep-alive",
        }
        
        response = session.get(
            url, 
            timeout=config.network.timeout, 
            headers=headers, 
            verify=False
        )
        response.raise_for_status()
        
        return self._extract_meta_from_html(response.text)
    
    def _try_with_alternative_headers(self, url: str) -> Tuple[str, str]:
        """替代请求头策略"""
        session = requests.Session()
        retry_strategy = Retry(
            total=config.network.max_retries,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504],
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        session.mount("http://", adapter)
        session.mount("https://", adapter)
        
        # 模拟移动设备
        headers = {
            "User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 14_7_1 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.1.2 Mobile/15E148 Safari/604.1",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
            "Accept-Encoding": "gzip, deflate, br",
            "Cache-Control": "no-cache",
            "Pragma": "no-cache",
        }
        
        response = session.get(
            url, 
            timeout=config.network.timeout, 
            headers=headers, 
            verify=False
        )
        response.raise_for_status()
        
        return self._extract_meta_from_html(response.text)
    
    def _extract_meta_from_html(self, html_content: str) -> Tuple[str, str]:
        """从HTML内容中提取元数据"""
        soup = BeautifulSoup(html_content, "html.parser")
        
        # 提取标题 - 尝试多种方式
        title = "无标题"
        
        # 方法1: 从title标签提取
        if soup.title and soup.title.string:
            title = soup.title.string.strip()
        
        # 方法2: 从h1标签提取
        if title == "无标题":
            h1 = soup.find("h1")
            if h1 and h1.get_text().strip():
                title = h1.get_text().strip()
        
        # 方法3: 从og:title提取
        if title == "无标题":
            og_title = soup.find("meta", attrs={"property": "og:title"})
            if og_title and og_title.get("content"):
                title = og_title["content"].strip()
        
        # 方法4: 从网站名称相关标签提取
        if title == "无标题":
            # 尝试从各种可能的标题标签提取
            for tag in ["h1", "h2", "h3", ".site-title", ".brand", ".logo"]:
                element = soup.select_one(tag)
                if element and element.get_text().strip():
                    title = element.get_text().strip()
                    break
        
        # 清理标题
        if title != "无标题":
            # 移除常见的后缀
            suffixes = [" - 首页", " - Home", " | 首页", " | Home", " - 官网", " | 官网"]
            for suffix in suffixes:
                if title.endswith(suffix):
                    title = title[:-len(suffix)]
            
            # 限制标题长度
            if len(title) > 100:
                title = title[:100] + "..."
        
        # 提取描述 - 尝试多种方式
        description = "无描述"
        
        # 方法1: meta description
        desc_meta = soup.find("meta", attrs={"name": "description"})
        if desc_meta and desc_meta.get("content"):
            description = desc_meta["content"].strip()
        
        # 方法2: og:description
        if description == "无描述":
            og_desc = soup.find("meta", attrs={"property": "og:description"})
            if og_desc and og_desc.get("content"):
                description = og_desc["content"].strip()
        
        # 方法3: 从页面内容提取
        if description == "无描述":
            # 尝试从第一个段落提取
            first_p = soup.find("p")
            if first_p and first_p.get_text().strip():
                text = first_p.get_text().strip()
                description = text[:100] + "..." if len(text) > 100 else text
        
        # 方法4: 从其他可能的描述标签提取
        if description == "无描述":
            for selector in [".description", ".summary", ".intro", ".content"]:
                element = soup.select_one(selector)
                if element and element.get_text().strip():
                    text = element.get_text().strip()
                    description = text[:100] + "..." if len(text) > 100 else text
                    break
        
        return title, description
    
    async def get_all(self, urls: List[str]) -> Dict[str, Tuple[str, str]]:
        """
        并发获取多个URL的元数据
        
        Args:
            urls: URL列表
            
        Returns:
            URL到元数据的映射字典
        """
        logger.info(f"开始获取 {len(urls)} 个URL的元数据")
        
        # 创建任务
        tasks = [self.get_meta_single(url) for url in urls]
        
        # 并发执行
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # 处理结果
        url_to_meta = {}
        for url, result in zip(urls, results):
            if isinstance(result, Exception):
                logger.error(f"获取 {url} 元数据时发生异常: {result}")
                url_to_meta[url] = ("无标题", "无描述")
            else:
                url_to_meta[url] = result
        
        logger.info(f"成功获取 {len(url_to_meta)} 个URL的元数据")
        return url_to_meta
    
    def clear_cache(self) -> None:
        """清空缓存"""
        self._cache.clear()
        logger.info("元数据缓存已清空")
    
    def get_cache_size(self) -> int:
        """获取缓存大小"""
        return len(self._cache)
