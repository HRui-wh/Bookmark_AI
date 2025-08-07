"""
书签解析器
负责解析HTML书签文件并提取书签信息
"""
import logging
from pathlib import Path
from typing import List
from bs4 import BeautifulSoup

from models.bookmark import Bookmark
from fetchers.meta_fetcher import MetaFetcher
from config import config
from utils.logger import get_logger

logger = get_logger("bookmark_organizer")


class BookmarkParser:
    """
    书签解析器类
    负责解析HTML书签文件并获取书签元数据
    """
    
    def __init__(self, html_path: str, max_concurrency: int = None):
        """
        初始化书签解析器
        
        Args:
            html_path: HTML书签文件路径
            max_concurrency: 最大并发数，如果为None则使用配置中的默认值
        """
        self.html_path = Path(html_path)
        self.max_concurrency = max_concurrency or config.network.max_concurrency
        
        if not self.html_path.exists():
            raise FileNotFoundError(f"书签文件不存在: {self.html_path}")
        
        logger.info(f"初始化书签解析器，文件路径: {self.html_path}")
    
    async def parse(self) -> List[Bookmark]:
        """
        解析书签文件
        
        Returns:
            书签列表
        """
        logger.info("开始解析书签文件")
        
        # 读取HTML文件
        try:
            with open(self.html_path, 'r', encoding='utf-8') as f:
                content = f.read()
        except Exception as e:
            logger.error(f"读取书签文件失败: {e}")
            raise
        
        # 解析HTML
        soup = BeautifulSoup(content, 'html.parser')
        links = soup.find_all('a')
        
        # 提取URL列表
        url_list = []
        for link in links:
            href = link.get('href', '').strip()
            if href.startswith(('http', 'https')):
                url_list.append(href)
        
        logger.info(f"从HTML文件中提取到 {len(url_list)} 个有效URL")
        
        if not url_list:
            logger.warning("未找到有效的URL")
            return []
        
        # 获取元数据
        fetcher = MetaFetcher(self.max_concurrency)
        url_to_meta = await fetcher.get_all(url_list)
        
        # 创建书签对象
        bookmarks = []
        failed_bookmarks = []
        
        for url in url_list:
            title, desc = url_to_meta.get(url, ("无标题", "无描述"))
            bookmark = Bookmark(title=title, url=url, description=desc)
            bookmarks.append(bookmark)
            
            # 检查是否获取元数据失败
            if title == "无标题" and desc == "无描述":
                failed_bookmarks.append(bookmark)
        
        if failed_bookmarks:
            logger.warning(f"有 {len(failed_bookmarks)} 个书签获取元数据失败，将使用备用分类")
        
        logger.info(f"成功解析 {len(bookmarks)} 个书签")
        return bookmarks
    
    def get_urls_only(self) -> List[str]:
        """
        仅提取URL列表，不获取元数据
        
        Returns:
            URL列表
        """
        logger.info("开始提取URL列表")
        
        try:
            with open(self.html_path, 'r', encoding='utf-8') as f:
                content = f.read()
        except Exception as e:
            logger.error(f"读取书签文件失败: {e}")
            raise
        
        soup = BeautifulSoup(content, 'html.parser')
        links = soup.find_all('a')
        
        url_list = []
        for link in links:
            href = link.get('href', '').strip()
            if href.startswith(('http', 'https')):
                url_list.append(href)
        
        logger.info(f"提取到 {len(url_list)} 个有效URL")
        return url_list
