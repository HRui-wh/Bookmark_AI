"""
数据模型测试
"""
import pytest
from models.bookmark import Bookmark, BookmarkPydantic, ClassifiedBookmark


class TestBookmark:
    """书签模型测试"""
    
    def test_bookmark_creation(self):
        """测试书签创建"""
        bookmark = Bookmark(
            title="测试网站",
            url="https://example.com",
            description="这是一个测试网站",
            folder="测试文件夹"
        )
        
        assert bookmark.title == "测试网站"
        assert bookmark.url == "https://example.com"
        assert bookmark.description == "这是一个测试网站"
        assert bookmark.folder == "测试文件夹"
    
    def test_bookmark_rename(self):
        """测试书签重命名"""
        bookmark = Bookmark(title="旧标题", url="https://example.com")
        bookmark.rename("新标题")
        
        assert bookmark.title == "新标题"
    
    def test_bookmark_repr(self):
        """测试书签字符串表示"""
        bookmark = Bookmark(title="测试", url="https://example.com", folder="文件夹")
        repr_str = repr(bookmark)
        
        assert "Bookmark" in repr_str
        assert "测试" in repr_str
        assert "https://example.com" in repr_str
        assert "文件夹" in repr_str


class TestBookmarkPydantic:
    """Pydantic书签模型测试"""
    
    def test_bookmark_pydantic_creation(self):
        """测试Pydantic书签创建"""
        bookmark = BookmarkPydantic(
            title="测试网站",
            url="https://example.com",
            description="这是一个测试网站"
        )
        
        assert bookmark.title == "测试网站"
        assert bookmark.url == "https://example.com"
        assert bookmark.description == "这是一个测试网站"
    
    def test_bookmark_pydantic_defaults(self):
        """测试Pydantic书签默认值"""
        bookmark = BookmarkPydantic(
            title="测试网站",
            url="https://example.com"
        )
        
        assert bookmark.description == ""
        assert bookmark.folder == ""
        assert bookmark.add_date is None


class TestClassifiedBookmark:
    """分类书签模型测试"""
    
    def test_classified_bookmark_creation(self):
        """测试分类书签创建"""
        classified = ClassifiedBookmark(
            name="测试网站",
            description="这是一个测试网站",
            category="编程",
            url="https://example.com"
        )
        
        assert classified.name == "测试网站"
        assert classified.description == "这是一个测试网站"
        assert classified.category == "编程"
        assert classified.url == "https://example.com"
