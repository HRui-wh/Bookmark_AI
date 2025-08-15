"""
HTML导出器
将分类结果导出为HTML格式
"""
import logging
import time
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from urllib.parse import urlparse, urlunparse

from models.bookmark import ClassifiedBookmark

from config import config
from utils.logger import get_logger

logger = get_logger("bookmark_organizer")


class HTMLExporter:
    """
    HTML导出器类
    将分类结果导出为标准格式的HTML书签文件
    """
    
    def __init__(self, data: Optional[Dict[str, Dict[str, str]]] = None, filename: str = None, items: Optional[List[ClassifiedBookmark]] = None):
        """
        初始化HTML导出器
        
        Args:
            data: 分类结果数据
            filename: 输出文件名，如果为None则使用配置中的默认值
        """
        self.data = data or {}
        self.filename = filename or config.output.output_filename
        self.items = items or []
        
        logger.info(f"初始化HTML导出器，输出文件: {self.filename}")
    
    def export(self) -> None:
        """
        导出HTML文件
        """
        logger.info("开始导出HTML文件")
        
        try:
            # 生成HTML内容
            html_content = self._generate_html()
            
            # 确保输出目录存在
            output_path = Path(self.filename)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            
            # 写入文件
            with open(output_path, "w", encoding=config.output.output_encoding) as f:
                f.write(html_content)
            
            logger.info(f"✅ HTML文件已成功导出: {self.filename}")
            
        except Exception as e:
            logger.error(f"导出HTML文件失败: {e}")
            raise
    
    def _generate_html(self) -> str:
        """
        生成HTML内容
        
        Returns:
            HTML字符串
        """
        timestamp = str(int(time.time()))
        
        # HTML头部
        html_lines = [
            '<!DOCTYPE NETSCAPE-Bookmark-file-1>',
            '<META HTTP-EQUIV="Content-Type" CONTENT="text/html; charset=UTF-8">',
            '<TITLE>Bookmarks</TITLE>',
            '<H1>Bookmarks</H1>',
            '<DL><p>',
            f'    <DT><H3 ADD_DATE="{timestamp}" PERSONAL_TOOLBAR_FOLDER="true">书签栏</H3>',
            '    <DL><p>'
        ]
        
        # 生成分类和书签
        if self.items:
            grouped = self._group_by_category_and_homepage(self.items)
            for category, home_map in grouped.items():
                if not home_map:
                    continue
                html_lines.append(f'        <DT><H3 ADD_DATE="{timestamp}">{category}</H3>')
                html_lines.append('        <DL><p>')

                for base_url, group in home_map.items():
                    home_item, children = group
                    if home_item is not None:
                        name = f"{home_item.name} - {home_item.description}".strip(' -')
                        html_lines.append(f'            <DT><A HREF="{home_item.url}" ADD_DATE="{timestamp}">{name}</A>')
                    else:
                        display_name = self._extract_domain_from_url(base_url)
                        html_lines.append(f'            <DT><A HREF="{base_url}" ADD_DATE="{timestamp}">{display_name}</A>')

                    if children:
                        html_lines.append('            <DL><p>')
                        for child in children:
                            child_name = f"{child.name} - {child.description}".strip(' -')
                            html_lines.append(f'                <DT><A HREF="{child.url}" ADD_DATE="{timestamp}">{child_name}</A>')
                        html_lines.append('            </DL><p>')

                html_lines.append('        </DL><p>')
        else:
            for category, sites in self.data.items():
                if not sites:  # 跳过空分类
                    continue
                
                html_lines.append(f'        <DT><H3 ADD_DATE="{timestamp}">{category}</H3>')
                html_lines.append('        <DL><p>')
                
                for name, url in sites.items():
                    html_lines.append(f'            <DT><A HREF="{url}" ADD_DATE="{timestamp}">{name}</A>')
                
                html_lines.append('        </DL><p>')
        
        # HTML尾部
        html_lines.extend([
            '    </DL><p>',
            '</DL><p>'
        ])
        
        return '\n'.join(html_lines)

    def _group_by_category_and_homepage(self, items: List[ClassifiedBookmark]) -> Dict[str, Dict[str, Tuple[Optional[ClassifiedBookmark], List[ClassifiedBookmark]]]]:
        """
        将条目先按 base_url 汇总，再决定其归属分类：
        - 若存在主页(home_item)，使用主页的分类；
        - 若不存在主页，则使用出现次数最多的分类；
        最终返回结构: {category: {base_url: (home_item, [children...])}}
        """
        # 第一步：按 base_url 汇总
        by_domain: Dict[str, Dict[str, object]] = {}
        for item in items:
            base_url = self._get_base_url(item.url)
            domain_bucket = by_domain.setdefault(base_url, {"home": None, "items": [], "cat_count": {}})
            # 主页识别
            if self._is_homepage(item.url) and domain_bucket["home"] is None:
                domain_bucket["home"] = item  # type: ignore[assignment]
            # 全量条目
            domain_bucket["items"].append(item)  # type: ignore[assignment]
            # 统计分类
            cat_count: Dict[str, int] = domain_bucket["cat_count"]  # type: ignore[assignment]
            cat_count[item.category] = cat_count.get(item.category, 0) + 1

        # 第二步：将域名桶分配到分类
        grouped: Dict[str, Dict[str, Tuple[Optional[ClassifiedBookmark], List[ClassifiedBookmark]]]] = {}
        for base_url, bucket in by_domain.items():
            home_item: Optional[ClassifiedBookmark] = bucket["home"]  # type: ignore[assignment]
            children: List[ClassifiedBookmark] = []
            # children 不包括 home 本身
            for it in bucket["items"]:  # type: ignore[assignment]
                if home_item is not None and it.url == home_item.url:
                    continue
                children.append(it)

            if home_item is not None:
                category = home_item.category
            else:
                # 选择出现次数最多的分类
                cat_count = bucket["cat_count"]  # type: ignore[assignment]
                if cat_count:
                    category = max(cat_count.items(), key=lambda kv: kv[1])[0]
                else:
                    category = "未分类"

            if category not in grouped:
                grouped[category] = {}
            grouped[category][base_url] = (home_item, children)

        return grouped

    def _get_base_url(self, url: str) -> str:
        parsed = urlparse(url)
        return urlunparse((parsed.scheme, parsed.netloc, '/', '', '', ''))

    def _is_homepage(self, url: str) -> bool:
        parsed = urlparse(url)
        if parsed.query or parsed.fragment:
            return False
        path = (parsed.path or '/').lower()
        home_like = {'/', '', '/index.html', '/index.htm', '/home', '/home/'}
        return path in home_like

    def _extract_domain_from_url(self, url: str) -> str:
        try:
            return urlparse(url).netloc or url
        except Exception:
            return url
    
    def get_statistics(self) -> Dict[str, int]:
        """
        获取导出统计信息
        
        Returns:
            各分类的数量统计
        """
        # 新结构：按分组统计主页+子页数量
        if self.items:
            grouped = self._group_by_category_and_homepage(self.items)
            stats: Dict[str, int] = {}
            total = 0
            for category, home_map in grouped.items():
                count = 0
                for _, (home_item, children) in home_map.items():
                    count += (1 if home_item is not None else 1)  # 至少一个占位主页
                    count += len(children)
                stats[category] = count
                total += count
            stats["总计"] = total
            return stats
        # 旧结构：按原有逻辑
        else:
            stats = {}
            total_sites = 0
            for category, sites in self.data.items():
                count = len(sites)
                stats[category] = count
                total_sites += count
            stats['总计'] = total_sites
            return stats
    
    def validate_data(self) -> bool:
        """
        验证数据有效性
        
        Returns:
            数据是否有效
        """
        if not self.data and not self.items:
            logger.warning("数据为空")
            return False
        
        # 验证旧结构
        if self.data:
            for category, sites in self.data.items():
                if not isinstance(sites, dict):
                    logger.error(f"分类 '{category}' 的数据格式错误")
                    return False
                for name, url in sites.items():
                    if not isinstance(name, str) or not isinstance(url, str):
                        logger.error(f"书签数据格式错误: {name} -> {url}")
                        return False
                    if not url.startswith(('http://', 'https://')):
                        logger.warning(f"书签URL格式可能不正确: {url}")
        # 验证新结构
        if self.items:
            for item in self.items:
                if not item.url.startswith(('http://', 'https://')):
                    logger.warning(f"书签URL格式可能不正确: {item.url}")
        
        logger.info("数据验证通过")
        return True
