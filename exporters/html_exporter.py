"""
HTML导出器
将分类结果导出为HTML格式
"""
import logging
import time
from pathlib import Path
from typing import Dict

from config import config
from utils.logger import get_logger

logger = get_logger("bookmark_organizer")


class HTMLExporter:
    """
    HTML导出器类
    将分类结果导出为标准格式的HTML书签文件
    """
    
    def __init__(self, data: Dict[str, Dict[str, str]], filename: str = None):
        """
        初始化HTML导出器
        
        Args:
            data: 分类结果数据
            filename: 输出文件名，如果为None则使用配置中的默认值
        """
        self.data = data
        self.filename = filename or config.output.output_filename
        
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
    
    def get_statistics(self) -> Dict[str, int]:
        """
        获取导出统计信息
        
        Returns:
            各分类的数量统计
        """
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
        if not self.data:
            logger.warning("数据为空")
            return False
        
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
        
        logger.info("数据验证通过")
        return True
