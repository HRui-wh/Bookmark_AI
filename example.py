"""
使用示例
展示如何使用重构后的书签整理工具
"""
import asyncio
import logging
from pathlib import Path

from parsers.bookmark_parser import BookmarkParser
from classifiers.ai_classifier import AIClassifier
from exporters.html_exporter import HTMLExporter
from utils.logger import setup_logger
from config import config

# 设置日志
logger = setup_logger(
    name="example",
    level=logging.INFO
)


async def example_usage():
    """
    使用示例
    """
    logger.info("🚀 开始书签整理示例")
    
    # 示例HTML文件路径（需要替换为实际路径）
    html_path = "example_bookmarks.html"
    
    # 检查文件是否存在
    if not Path(html_path).exists():
        logger.warning(f"示例文件不存在: {html_path}")
        logger.info("请将您的书签HTML文件重命名为 example_bookmarks.html 或修改此脚本中的路径")
        return
    
    try:
        # 1. 解析书签
        logger.info("📖 解析书签文件...")
        parser = BookmarkParser(html_path)
        bookmarks = await parser.parse()
        
        if not bookmarks:
            logger.warning("未找到书签")
            return
        
        logger.info(f"✅ 解析到 {len(bookmarks)} 个书签")
        
        # 2. AI分类
        logger.info("🤖 开始AI分类...")
        classifier = AIClassifier(bookmarks)
        await classifier.classify_all()
        
        result = classifier.get_result()
        stats = classifier.get_statistics()
        
        logger.info("📊 分类结果:")
        for category, count in stats.items():
            logger.info(f"  {category}: {count} 个")
        
        # 3. 导出HTML
        logger.info("📤 导出HTML文件...")
        exporter = HTMLExporter(result, "example_output.html", items=classifier.get_items())
        exporter.export()
        
        logger.info("🎉 示例完成！输出文件: example_output.html")
        
    except Exception as e:
        logger.error(f"示例执行失败: {e}")


def show_config():
    """
    显示当前配置
    """
    logger.info("📋 当前配置:")
    logger.info(f"  AI模型: {config.ai.model}")
    logger.info(f"  最大并发数: {config.network.max_concurrency}")
    logger.info(f"  超时时间: {config.network.timeout}秒")
    logger.info(f"  输出文件: {config.output.output_filename}")
    logger.info(f"  分类类别: {', '.join(config.categories)}")


if __name__ == "__main__":
    # 显示配置
    show_config()
    
    # 运行示例
    asyncio.run(example_usage())
