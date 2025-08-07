"""
书签数据模型
定义书签相关的数据结构
"""
from dataclasses import dataclass, field
from typing import Optional
from pydantic import BaseModel, HttpUrl, Field


@dataclass
class Bookmark:
    """
    书签数据类
    
    Attributes:
        title: 书签标题
        url: 书签URL
        description: 书签描述
        folder: 所属文件夹
        add_date: 添加日期
    """
    title: str
    url: str
    description: str = ""
    folder: str = ""
    add_date: Optional[str] = None
    
    def rename(self, new_title: str) -> None:
        """
        重命名书签
        
        Args:
            new_title: 新的标题
        """
        self.title = new_title
    
    def __repr__(self) -> str:
        return f"<Bookmark: {self.title} ({self.url}) in '{self.folder}'>"
    
    def __str__(self) -> str:
        return f"{self.title} ({self.url}) - {self.description}"


class BookmarkPydantic(BaseModel):
    """
    书签Pydantic模型
    用于数据验证和序列化
    """
    title: str = Field(..., description="书签标题")
    url: str = Field(..., description="书签URL")
    description: str = Field(default="", description="书签描述")
    folder: str = Field(default="", description="所属文件夹")
    add_date: Optional[str] = Field(default=None, description="添加日期")
    
    class Config:
        """Pydantic配置"""
        validate_assignment = True
        extra = "forbid"


class ClassifiedBookmark(BaseModel):
    """
    分类后的书签模型
    """
    name: str = Field(..., description="网站名称")
    description: str = Field(..., description="网站描述")
    category: str = Field(..., description="网站分类")
    url: str = Field(..., description="网站链接")
    
    class Config:
        """Pydantic配置"""
        validate_assignment = True
        extra = "forbid"
