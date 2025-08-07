.PHONY: help install install-dev test lint format type-check clean run example

# 默认目标
help:
	@echo "可用的命令:"
	@echo "  install      - 安装生产依赖"
	@echo "  install-dev  - 安装开发依赖"
	@echo "  test         - 运行测试"
	@echo "  lint         - 代码检查"
	@echo "  format       - 代码格式化"
	@echo "  type-check   - 类型检查"
	@echo "  clean        - 清理缓存文件"
	@echo "  run          - 运行主程序"
	@echo "  example      - 运行示例程序"

# 安装生产依赖
install:
	pip install -r requirements.txt

# 安装开发依赖
install-dev:
	pip install -r requirements.txt
	pip install -e ".[dev]"

# 运行测试
test:
	pytest tests/ -v

# 代码检查
lint:
	flake8 . --count --select=E9,F63,F7,F82 --show-source --statistics
	flake8 . --count --exit-zero --max-complexity=10 --max-line-length=88 --statistics

# 代码格式化
format:
	black .

# 类型检查
type-check:
	mypy .

# 清理缓存文件
clean:
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	find . -type f -name "*.pyd" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} +
	find . -type d -name ".pytest_cache" -exec rm -rf {} +
	find . -type d -name ".mypy_cache" -exec rm -rf {} +
	rm -rf build/
	rm -rf dist/
	rm -rf logs/*.log

# 运行主程序
run:
	python main.py

# 运行示例程序
example:
	python example.py

# 检查代码质量
check: lint type-check test
	@echo "✅ 代码质量检查完成"

# 完整开发流程
dev: install-dev format lint type-check test
	@echo "✅ 开发环境设置完成"
