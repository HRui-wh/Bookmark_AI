"""
配置管理模块
集中管理项目的所有配置项
"""
import os
from typing import Optional
from pydantic import BaseModel, Field
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()


class AIConfig(BaseModel):
    """AI模型配置"""
    model: str = Field(default="deepseek-chat", description="AI模型名称")
    temperature: float = Field(default=0.3, ge=0.0, le=2.0, description="温度参数")
    max_tokens: int = Field(default=1024, gt=0, description="最大token数")
    top_p: float = Field(default=0.9, ge=0.0, le=1.0, description="Top-p参数")
    presence_penalty: float = Field(default=0.0, ge=-2.0, le=2.0, description="存在惩罚")
    frequency_penalty: float = Field(default=0.0, ge=-2.0, le=2.0, description="频率惩罚")


class NetworkConfig(BaseModel):
    """网络请求配置"""
    max_concurrency: int = Field(default=100, gt=0, description="最大并发数")
    timeout: int = Field(default=8, gt=0, description="请求超时时间(秒)")
    max_retries: int = Field(default=2, ge=0, description="最大重试次数")
    user_agent: str = Field(
        default="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        description="User-Agent"
    )


class OutputConfig(BaseModel):
    """输出配置"""
    output_filename: str = Field(default="sorted_bookmarks.html", description="输出文件名")
    output_encoding: str = Field(default="utf-8", description="输出文件编码")


class Config(BaseModel):
    """主配置类"""
    # API配置
    api_key: str = Field(..., description="DeepSeek API密钥")
    api_base_url: str = Field(default="https://api.deepseek.com/v1", description="API基础URL")
    
    # 功能配置
    ai: AIConfig = Field(default_factory=AIConfig, description="AI配置")
    network: NetworkConfig = Field(default_factory=NetworkConfig, description="网络配置")
    output: OutputConfig = Field(default_factory=OutputConfig, description="输出配置")
    
    # 分类类别
    categories: list[str] = Field(
        default=[
            "编程", "AI", "VPN", "在线工具", "娱乐", 
            "电子商务", "供应厂商", "社交", "资讯", "专业设计"
        ],
        description="网站分类类别"
    )

    @classmethod
    def from_env(cls) -> "Config":
        """从环境变量创建配置"""
        api_key = os.getenv("DEEPSEEK_API_KEY")
        if not api_key:
            raise ValueError("请设置环境变量 DEEPSEEK_API_KEY")
        
        return cls(api_key=api_key)


# 全局配置实例
config = Config.from_env()
