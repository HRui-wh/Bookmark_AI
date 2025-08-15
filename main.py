"""
书签整理工具主程序
使用AI对书签进行智能分类和整理
"""
import asyncio
import logging
import sys
from pathlib import Path

from parsers.bookmark_parser import BookmarkParser
from classifiers.ai_classifier import AIClassifier
from exporters.html_exporter import HTMLExporter
from utils.logger import setup_logger
from config import config

# 设置日志
logger = setup_logger(
    name="bookmark_organizer",
    level=logging.INFO,
    log_file="logs/bookmark_organizer.log"
)


async def main():
    """
    主函数
    """
    try:
        logger.info("🚀 开始执行书签整理任务")
        
        # 书签文件路径
        html_path = r"C:/Users/QSYJC/Desktop/favorites_2025_8_5.html"
        
        # 验证输入文件
        if not Path(html_path).exists():
            logger.error(f"书签文件不存在: {html_path}")
            sys.exit(1)
        
        # 第一步：解析书签文件
        logger.info("📖 第一步：解析书签文件")
        parser = BookmarkParser(html_path, config.network.max_concurrency)
        bookmarks = await parser.parse()
        
        if not bookmarks:
            logger.warning("未找到有效的书签")
            return
        
        logger.info(f"✅ 成功解析 {len(bookmarks)} 个书签")
        
        # 第二步：AI分类
        logger.info("🤖 第二步：AI智能分类")
        classifier = AIClassifier(bookmarks, config.network.max_concurrency)
        await classifier.classify_all()
        
        # 获取分类结果
        result = classifier.get_result()
        items = classifier.get_items()
        stats = classifier.get_statistics()
        
        logger.info("📊 分类统计:")
        for category, count in stats.items():
            logger.info(f"  {category}: {count} 个")
        
        # 第三步：导出HTML
        logger.info("📤 第三步：导出HTML文件")
        exporter = HTMLExporter(result, items=items)
        
        # 验证数据
        if not exporter.validate_data():
            logger.error("数据验证失败")
            return
        
        # 导出文件
        exporter.export()
        
        # 显示导出统计
        export_stats = exporter.get_statistics()
        logger.info("📈 导出统计:")
        for category, count in export_stats.items():
            logger.info(f"  {category}: {count} 个")
        
        logger.info("🎉 书签整理任务完成！")
        
    except KeyboardInterrupt:
        logger.info("用户中断了程序执行")
    except Exception as e:
        logger.error(f"程序执行失败: {e}")
        raise


if __name__ == "__main__":
    # 创建日志目录
    Path("logs").mkdir(exist_ok=True)
    
    # 运行主程序
    asyncio.run(main())
