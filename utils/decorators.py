"""
装饰器模块
包含性能监控、错误处理等装饰器
"""
import time
import functools
import asyncio
import logging
from typing import Any, Callable, TypeVar, ParamSpec

# 类型变量
T = TypeVar('T')
P = ParamSpec('P')

# 获取logger
logger = logging.getLogger(__name__)


def timing(func: Callable[P, T]) -> Callable[P, T]:
    """
    同步函数性能监控装饰器
    
    Args:
        func: 要装饰的函数
        
    Returns:
        装饰后的函数
    """
    @functools.wraps(func)
    def wrapper(*args: P.args, **kwargs: P.kwargs) -> T:
        start_time = time.time()
        logger.info(f"⏳ 开始执行函数：{func.__name__}")
        
        try:
            result = func(*args, **kwargs)
            end_time = time.time()
            duration = end_time - start_time
            logger.info(f"✅ 函数 {func.__name__} 执行完毕，用时：{duration:.2f} 秒")
            return result
        except Exception as e:
            end_time = time.time()
            duration = end_time - start_time
            logger.error(f"❌ 函数 {func.__name__} 执行失败，用时：{duration:.2f} 秒，错误：{e}")
            raise
    
    return wrapper


def async_timing(func: Callable[P, Any]) -> Callable[P, Any]:
    """
    异步函数性能监控装饰器
    
    Args:
        func: 要装饰的异步函数
        
    Returns:
        装饰后的异步函数
    """
    @functools.wraps(func)
    async def wrapper(*args: P.args, **kwargs: P.kwargs) -> Any:
        start_time = time.time()
        logger.info(f"⏳ 开始执行异步函数：{func.__name__}")
        
        try:
            result = await func(*args, **kwargs)
            end_time = time.time()
            duration = end_time - start_time
            logger.info(f"✅ 异步函数 {func.__name__} 执行完毕，用时：{duration:.2f} 秒")
            return result
        except Exception as e:
            end_time = time.time()
            duration = end_time - start_time
            logger.error(f"❌ 异步函数 {func.__name__} 执行失败，用时：{duration:.2f} 秒，错误：{e}")
            raise
    
    return wrapper


def retry(max_attempts: int = 3, delay: float = 1.0):
    """
    重试装饰器
    
    Args:
        max_attempts: 最大重试次数
        delay: 重试间隔(秒)
        
    Returns:
        装饰器函数
    """
    def decorator(func: Callable[P, T]) -> Callable[P, T]:
        @functools.wraps(func)
        def wrapper(*args: P.args, **kwargs: P.kwargs) -> T:
            last_exception = None
            
            for attempt in range(max_attempts):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    last_exception = e
                    if attempt < max_attempts - 1:
                        logger.warning(f"函数 {func.__name__} 第 {attempt + 1} 次尝试失败：{e}，{delay}秒后重试")
                        time.sleep(delay)
            
            logger.error(f"函数 {func.__name__} 在 {max_attempts} 次尝试后仍然失败")
            raise last_exception
        
        return wrapper
    return decorator


def async_retry(max_attempts: int = 3, delay: float = 1.0):
    """
    异步重试装饰器
    
    Args:
        max_attempts: 最大重试次数
        delay: 重试间隔(秒)
        
    Returns:
        装饰器函数
    """
    def decorator(func: Callable[P, Any]) -> Callable[P, Any]:
        @functools.wraps(func)
        async def wrapper(*args: P.args, **kwargs: P.kwargs) -> Any:
            last_exception = None
            
            for attempt in range(max_attempts):
                try:
                    return await func(*args, **kwargs)
                except Exception as e:
                    last_exception = e
                    if attempt < max_attempts - 1:
                        logger.warning(f"异步函数 {func.__name__} 第 {attempt + 1} 次尝试失败：{e}，{delay}秒后重试")
                        await asyncio.sleep(delay)
            
            logger.error(f"异步函数 {func.__name__} 在 {max_attempts} 次尝试后仍然失败")
            raise last_exception
        
        return wrapper
    return decorator
