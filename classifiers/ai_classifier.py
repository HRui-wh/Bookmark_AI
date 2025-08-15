"""
AI分类器
使用AI模型对书签进行分类
"""
import asyncio
import logging
import re
from typing import Dict, List, Optional
from openai import OpenAI

from models.bookmark import Bookmark, ClassifiedBookmark
from config import config
from utils.decorators import async_timing, async_retry
from utils.logger import get_logger
from classifiers.ai_backup_classifier import AIBackupClassifier

logger = get_logger("bookmark_organizer")


class AIClassifier:
    """
    AI分类器类
    使用AI模型对书签进行智能分类
    """
    
    def __init__(self, bookmarks: List[Bookmark], max_concurrency: int = None):
        """
        初始化AI分类器
        
        Args:
            bookmarks: 书签列表
            max_concurrency: 最大并发数，如果为None则使用配置中的默认值
        """
        self.bookmarks = bookmarks
        self.result: Dict[str, Dict[str, str]] = {}
        # 结构化的分类结果列表（用于更丰富的导出场景，如主页/子页面分组）
        self.classified_items: List[ClassifiedBookmark] = []
        self.max_concurrency = max_concurrency or config.network.max_concurrency
        self.semaphore = asyncio.Semaphore(self.max_concurrency)
        
        # 初始化OpenAI客户端
        self.client = OpenAI(
            api_key=config.api_key,
            base_url=config.api_base_url,
        )
        
        # 初始化备用分类器
        self.backup_classifier = AIBackupClassifier(self.max_concurrency)
        
        logger.info(f"初始化AI分类器，书签数量: {len(bookmarks)}")
    
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
            # 构建提示词
            prompt = self._build_prompt(bookmark)
            
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
                logger.warning(f"AI返回空内容: {bookmark.title}")
                return None
            
            # 解析AI响应
            classified = self._parse_ai_response(content, bookmark)
            if classified:
                # 添加到结果中
                key = f"{classified.name} - {classified.description}"
                if classified.category not in self.result:
                    self.result[classified.category] = {}
                self.result[classified.category][key] = classified.url
                # 保存结构化条目
                self.classified_items.append(classified)
                
                logger.debug(f"成功分类: {bookmark.title} -> {classified.category}")
                return classified
            
        except Exception as e:
            logger.error(f"分类书签 {bookmark.title} 时失败: {e}")
        
        return None
    
    def _build_prompt(self, bookmark: Bookmark) -> str:
        """
        构建AI提示词
        
        Args:
            bookmark: 书签对象
            
        Returns:
            提示词字符串
        """
        categories_str = "、".join(config.categories)
        
        prompt = f"""
你是一个高效的中文网站分类助手。根据给定信息输出精炼结果。

网站信息：
- 标题：{bookmark.title}
- 描述：{bookmark.description}
- 链接：{bookmark.url}

分类范围（必须从以下中文类别中二选一）：
编程、AI、VPN、在线工具、娱乐、电子商务、供应厂商、社交、资讯、专业设计

要求：
1) 网站名称：提取真实名称，避免“无标题”；
2) 网站描述：不超过50字，突出主要功能；
3) 网站分类：严格从上述中文类别中选择；
4) 网站链接：保持原样；

注意：识别知名站点；标题乱码时结合URL推断；尽量避免滥用“在线工具”。

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
    async def classify_all(self) -> None:
        """
        分类所有书签，包含备用分类机制
        """
        logger.info(f"开始分类 {len(self.bookmarks)} 个书签")
        
        # 创建任务
        tasks = [self.classify_single(bookmark) for bookmark in self.bookmarks]
        
        # 并发执行
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # 统计结果和收集失败的书签
        success_count = 0
        failed_bookmarks = []
        
        for bookmark, result in zip(self.bookmarks, results):
            if isinstance(result, Exception):
                logger.error(f"分类任务执行异常: {result}")
                failed_bookmarks.append(bookmark)
            elif result is not None:
                success_count += 1
            else:
                # 分类失败的书签
                failed_bookmarks.append(bookmark)
        
        logger.info(f"主分类完成，成功分类 {success_count}/{len(self.bookmarks)} 个书签")
        
        # 如果有失败的书签，使用备用分类器
        if failed_bookmarks:
            logger.info(f"开始备用分类 {len(failed_bookmarks)} 个失败的书签")
            backup_results = await self.backup_classifier.classify_failed_bookmarks(failed_bookmarks)
            
            # 将备用分类结果添加到主结果中
            for classified in backup_results:
                key = f"{classified.name} - {classified.description}"
                if classified.category not in self.result:
                    self.result[classified.category] = {}
                self.result[classified.category][key] = classified.url
                # 保存结构化条目
                self.classified_items.append(classified)
            
            logger.info(f"备用分类完成，成功分类 {len(backup_results)}/{len(failed_bookmarks)} 个书签")
        
        total_success = success_count + len([r for r in results if r is not None and not isinstance(r, Exception)])
        logger.info(f"总分类完成，成功分类 {total_success}/{len(self.bookmarks)} 个书签")
    
    def get_result(self) -> Dict[str, Dict[str, str]]:
        """
        获取分类结果
        
        Returns:
            分类结果字典
        """
        return self.result

    def get_items(self) -> List[ClassifiedBookmark]:
        """
        获取结构化分类条目列表

        Returns:
            分类后的结构化条目列表
        """
        return list(self.classified_items)
    
    def get_statistics(self) -> Dict[str, int]:
        """
        获取分类统计信息
        
        Returns:
            各分类的数量统计
        """
        stats = {}
        for category, sites in self.result.items():
            stats[category] = len(sites)
        return stats
