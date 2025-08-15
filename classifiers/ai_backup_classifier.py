"""
AI备用分类器
当无法获取网站元数据时，基于URL和域名信息使用AI知识库进行分类
"""
import asyncio
import logging
import re
from typing import Dict, List, Optional
from urllib.parse import urlparse
from openai import OpenAI

from models.bookmark import Bookmark, ClassifiedBookmark
from config import config
from utils.decorators import async_timing, async_retry
from utils.logger import get_logger

logger = get_logger("bookmark_organizer")


class AIBackupClassifier:
    """
    AI备用分类器类
    当无法获取网站元数据时，基于URL和域名信息进行分类
    """
    
    def __init__(self, max_concurrency: int = None):
        """
        初始化AI备用分类器
        
        Args:
            max_concurrency: 最大并发数，如果为None则使用配置中的默认值
        """
        self.max_concurrency = max_concurrency or config.network.max_concurrency
        self.semaphore = asyncio.Semaphore(self.max_concurrency)
        
        # 初始化OpenAI客户端
        self.client = OpenAI(
            api_key=config.api_key,
            base_url=config.api_base_url,
        )
        
        logger.info(f"初始化AI备用分类器，最大并发数: {self.max_concurrency}")
    
    @async_retry(max_attempts=2, delay=1.0)
    async def classify_single(self, bookmark: Bookmark) -> Optional[ClassifiedBookmark]:
        """
        分类单个书签
        
        Args:
            bookmark: 要分类的书签
            
        Returns:
            分类后的书签，如果失败则返回None
        """
        async with self.semaphore:
            return await asyncio.to_thread(self._sync_classify_single, bookmark)
    
    def _sync_classify_single(self, bookmark: Bookmark) -> Optional[ClassifiedBookmark]:
        """
        同步分类单个书签
        
        Args:
            bookmark: 要分类的书签
            
        Returns:
            分类后的书签，如果失败则返回None
        """
        try:
            # 提取URL信息
            url_info = self._extract_url_info(bookmark.url)
            
            # 构建提示词
            prompt = self._build_prompt(bookmark, url_info)
            
            # 调用AI API
            response = self.client.chat.completions.create(
                model=config.ai.model,
                messages=[{"role": "user", "content": prompt}],
                temperature=config.ai.temperature,
                max_tokens=config.ai.max_tokens,
                top_p=config.ai.top_p,
                presence_penalty=config.ai.presence_penalty,
                frequency_penalty=config.ai.frequency_penalty,
            )
            
            content = response.choices[0].message.content
            if not content:
                logger.warning(f"AI返回空内容: {bookmark.url}")
                return None
            
            # 解析AI响应
            classified = self._parse_ai_response(content, bookmark)
            if classified:
                logger.debug(f"备用分类成功: {bookmark.url} -> {classified.category}")
                return classified
            
        except Exception as e:
            logger.error(f"备用分类书签 {bookmark.url} 时失败: {e}")
        
        return None
    
    def _extract_url_info(self, url: str) -> Dict[str, str]:
        """
        从URL中提取有用信息
        
        Args:
            url: 目标URL
            
        Returns:
            包含域名、路径等信息的字典
        """
        try:
            parsed = urlparse(url)
            domain = parsed.netloc.lower()
            path = parsed.path.lower()
            query = parsed.query.lower()
            
            # 提取子域名和主域名
            domain_parts = domain.split('.')
            if len(domain_parts) >= 2:
                main_domain = '.'.join(domain_parts[-2:])
                subdomain = '.'.join(domain_parts[:-2]) if len(domain_parts) > 2 else ""
            else:
                main_domain = domain
                subdomain = ""
            
            # 提取关键词
            keywords = []
            if subdomain:
                keywords.append(subdomain)
            
            # 从路径中提取关键词
            path_keywords = [part for part in path.split('/') if part and len(part) > 2]
            keywords.extend(path_keywords)
            
            # 从查询参数中提取关键词
            if query:
                query_keywords = [part for part in query.split('&') if part and '=' in part]
                keywords.extend(query_keywords)
            
            return {
                "domain": domain,
                "main_domain": main_domain,
                "subdomain": subdomain,
                "path": path,
                "keywords": keywords,
                "full_url": url
            }
            
        except Exception as e:
            logger.warning(f"解析URL失败 {url}: {e}")
            return {
                "domain": "",
                "main_domain": "",
                "subdomain": "",
                "path": "",
                "keywords": [],
                "full_url": url
            }
    
    def _build_prompt(self, bookmark: Bookmark, url_info: Dict[str, str]) -> str:
        """
        构建AI提示词
        
        Args:
            bookmark: 书签对象
            url_info: URL信息字典
            
        Returns:
            提示词字符串
        """
        categories_str = "、".join(config.categories)
        
        # 构建URL分析信息
        url_analysis = f"""
URL分析信息：
- 完整URL: {url_info['full_url']}
- 域名: {url_info['domain']}
- 主域名: {url_info['main_domain']}
- 子域名: {url_info['subdomain']}
- 路径: {url_info['path']}
- 关键词: {', '.join(url_info['keywords']) if url_info['keywords'] else '无'}
"""
        
        prompt = f"""
你是一个快速分类助手。在无法读取网页内容时，请依据 URL 结构和常识完成分类。

{url_analysis}

基础信息：
- 标题：{bookmark.title}
- 描述：{bookmark.description}

分类范围（只能从以下中文类别中选择）：
编程、AI、VPN、在线工具、娱乐、电子商务、供应厂商、社交、资讯、专业设计

输出要求：
1) 网站名称：由域名/路径推断，避免“无标题”；
2) 网站描述：≤50字，依据URL关键词归纳主要用途；
3) 网站分类：严格在上述中文类别中；
4) 网站链接：保持原样；

只按以下四行原样输出：
网站名称：xxx
网站描述：xxx
网站分类：xxx
网站链接：xxx
"""
        return prompt.strip()
    
    def _parse_ai_response(self, content: str, bookmark: Bookmark) -> Optional[ClassifiedBookmark]:
        """
        解析AI响应
        
        Args:
            content: AI返回的内容
            bookmark: 原始书签对象
            
        Returns:
            解析后的分类书签，如果解析失败则返回None
        """
        try:
            # 使用正则表达式提取信息
            match_name = re.search(r"网站名称：(.+)", content)
            match_desc = re.search(r"网站描述：(.+)", content)
            match_type = re.search(r"网站分类：(.+)", content)
            match_url = re.search(r"网站链接：(.+)", content)
            
            if match_name and match_desc and match_type and match_url:
                name = match_name.group(1).strip()
                description = match_desc.group(1).strip()
                category = match_type.group(1).strip()
                url = match_url.group(1).strip()
                
                # 验证分类是否在允许的类别中
                if category not in config.categories:
                    logger.warning(f"AI返回的分类 '{category}' 不在允许的类别中，使用默认分类")
                    category = "在线工具"
                
                return ClassifiedBookmark(
                    name=name,
                    description=description,
                    category=category,
                    url=url
                )
            else:
                logger.warning(f"无法解析AI响应: {content}")
                return None
                
        except Exception as e:
            logger.error(f"解析AI响应时发生错误: {e}")
            return None
    
    @async_timing
    async def classify_failed_bookmarks(self, failed_bookmarks: List[Bookmark]) -> List[ClassifiedBookmark]:
        """
        分类获取元数据失败的书签
        
        Args:
            failed_bookmarks: 获取元数据失败的书签列表
            
        Returns:
            分类后的书签列表
        """
        if not failed_bookmarks:
            logger.info("没有需要备用分类的书签")
            return []
        
        logger.info(f"开始备用分类 {len(failed_bookmarks)} 个书签")
        
        # 创建任务
        tasks = [self.classify_single(bookmark) for bookmark in failed_bookmarks]
        
        # 并发执行
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # 处理结果
        classified_bookmarks = []
        success_count = 0
        
        for result in results:
            if isinstance(result, Exception):
                logger.error(f"备用分类任务执行异常: {result}")
            elif result is not None:
                classified_bookmarks.append(result)
                success_count += 1
        
        logger.info(f"备用分类完成，成功分类 {success_count}/{len(failed_bookmarks)} 个书签")
        return classified_bookmarks
