# 书签整理工具 (Bookmark Organizer)

一个基于AI的智能书签分类和整理工具，可以自动对浏览器书签进行智能分类。

## 功能特性

- 🔍 **智能解析**: 自动解析HTML格式的书签文件
- 🤖 **AI分类**: 使用DeepSeek AI模型对书签进行智能分类
- 📊 **多分类**: 支持编程、AI、VPN、在线工具、娱乐、电子商务、供应厂商、社交、资讯、专业设计等分类
- ⚡ **高性能**: 异步并发处理，支持大量书签的快速处理
- 📤 **标准输出**: 导出标准格式的HTML书签文件
- 📝 **详细日志**: 完整的执行日志和错误处理

## 项目结构

```
Collect_Organize/
├── main.py                 # 主程序入口
├── config.py              # 配置管理
├── requirements.txt       # 依赖包列表
├── README.md             # 项目文档
├── .env                  # 环境变量配置
├── .gitignore           # Git忽略文件
├── models/              # 数据模型
│   ├── __init__.py
│   └── bookmark.py      # 书签数据模型
├── parsers/             # 解析器
│   ├── __init__.py
│   └── bookmark_parser.py  # 书签解析器
├── fetchers/            # 数据获取器
│   ├── __init__.py
│   └── meta_fetcher.py  # 元数据获取器
├── classifiers/         # 分类器
│   ├── __init__.py
│   └── ai_classifier.py # AI分类器
├── exporters/           # 导出器
│   ├── __init__.py
│   └── html_exporter.py # HTML导出器
├── utils/               # 工具模块
│   ├── __init__.py
│   ├── decorators.py    # 装饰器
│   └── logger.py        # 日志配置
└── logs/                # 日志文件目录
```

## 安装和配置

### 1. 克隆项目

```bash
git clone <repository-url>
cd Collect_Organize
```

### 2. 创建虚拟环境

```bash
python -m venv .venv
source .venv/bin/activate  # Linux/Mac
# 或
.venv\Scripts\activate     # Windows
```

### 3. 安装依赖

```bash
pip install -r requirements.txt
```

### 4. 配置环境变量

创建 `.env` 文件并添加你的DeepSeek API密钥：

```env
DEEPSEEK_API_KEY=your_api_key_here
```

### 5. 准备书签文件

将你的浏览器书签导出为HTML格式，并更新 `main.py` 中的文件路径：

```python
html_path = r"path/to/your/bookmarks.html"
```

## 使用方法

### 基本使用

```bash
python main.py
```

### 配置选项

可以通过修改 `config.py` 来调整各种配置：

- **AI模型配置**: 模型名称、温度、最大token数等
- **网络配置**: 并发数、超时时间、重试次数等
- **输出配置**: 输出文件名、编码格式等
- **分类类别**: 可自定义分类类别

## 分类类别

默认支持以下分类：

- 编程
- AI
- VPN
- 在线工具
- 娱乐
- 电子商务
- 供应厂商
- 社交
- 资讯
- 专业设计

## 输出格式

程序会生成标准格式的HTML书签文件，可以直接导入到浏览器中使用。

## 日志系统

程序会生成详细的执行日志，包括：

- 执行时间统计
- 错误和警告信息
- 分类统计
- 性能监控

日志文件保存在 `logs/` 目录下。

## 开发指南

### 代码风格

项目使用以下工具进行代码质量控制：

- **Black**: 代码格式化
- **Flake8**: 代码检查
- **MyPy**: 类型检查

### 运行测试

```bash
pytest
```

### 代码格式化

```bash
black .
```

### 类型检查

```bash
mypy .
```

## 故障排除

### 常见问题

1. **API密钥错误**: 确保在 `.env` 文件中正确设置了 `DEEPSEEK_API_KEY`
2. **文件路径错误**: 检查书签文件路径是否正确
3. **网络连接问题**: 检查网络连接和防火墙设置
4. **依赖包问题**: 确保所有依赖包都已正确安装

### 日志查看

查看 `logs/bookmark_organizer.log` 文件获取详细的错误信息。

## 贡献指南

欢迎提交Issue和Pull Request来改进这个项目。

## 许可证

本项目采用MIT许可证。

## 更新日志

### v2.0.0
- 重构整个项目架构
- 添加完整的日志系统
- 改进错误处理
- 添加配置管理
- 优化性能和并发处理
