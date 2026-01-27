# 📦 SuperAgent v3.2 包分发与使用指南

> **版本**: v3.2.0
> **更新日期**: 2026-01-19
> **适用对象**: 开发者/包维护者

---

## 📑 目录

1. [使用方式概述](#使用方式概述)
2. [方式1：PYTHONPATH（推荐用于开发）](#方式1pythonpath推荐用于开发)
3. [方式2：本地安装](#方式2本地安装)
4. [方式3：打包发布到 PyPI](#方式3打包发布到-pypi)
5. [在其他项目中使用](#在其他项目中使用)
6. [常见问题](#常见问题)

---

## 使用方式概述

SuperAgent v3.2 可以通过以下方式使用：

| 方式 | 适用场景 | 复杂度 | 说明 |
|------|---------|--------|------|
| **PYTHONPATH** | 本地开发 | ⭐ | 最简单，适合自己使用 |
| **本地安装** | 团队协作 | ⭐⭐ | 可以 pip install |
| **PyPI 发布** | 公开分发 | ⭐⭐⭐ | 任何人都能 pip install |

---

## 方式1：PYTHONPATH（推荐用于开发）

### 配置环境变量

**Windows PowerShell**:
```powershell
# 临时生效（当前终端）
$env:PYTHONPATH = "E:\SuperAgent"

# 永久生效
[System.Environment]::SetEnvironmentVariable(
    "PYTHONPATH",
    "E:\SuperAgent",
    "User"
)
```

**Windows CMD**:
```cmd
# 永久生效
setx PYTHONPATH "E:\SuperAgent"
```

**Linux/macOS**:
```bash
# 临时生效
export PYTHONPATH="/path/to/SuperAgent"

# 永久生效（添加到 ~/.bashrc 或 ~/.zshrc）
echo 'export PYTHONPATH="/path/to/SuperAgent"' >> ~/.bashrc
```

### 使用方式

```python
# 直接导入，无需 sys.path.insert
from SuperAgent import Orchestrator, AgentFactory, AgentType

orchestrator = Orchestrator(Path("."))
```

---

## 方式2：本地安装

### 可编辑模式安装（推荐用于开发）

```bash
# 进入项目目录
cd E:\SuperAgent

# 可编辑模式安装（修改代码即时生效）
pip install -e E:\SuperAgent
```

### 离线安装

```bash
# 打包为 wheel
pip install build
python -m build

# 安装 wheel 文件
pip install dist\SuperAgent-3.2.0-py3-none-any.whl
```

### 验证安装

```python
# 验证安装是否成功
python -c "from SuperAgent import Orchestrator; print('安装成功!')"
```

---

## 方式3：打包发布到 PyPI

### 准备工作

1. **创建 pyproject.toml**（推荐现代方式）:

```toml
# pyproject.toml
[build-system]
requires = ["setuptools>=61.0", "wheel"]
build-backend = "setuptools.build_meta"

[project]
name = "superagent-ydwangypl"
version = "3.2.0"
description = "SuperAgent - Python AI Agent 任务编排库"
readme = "README.md"
license = {text = "MIT"}
authors = [
    {name = "SuperAgent Team", email = "superagent@example.com"}
]
classifiers = [
    "Development Status :: 4 - Beta",
    "Intended Audience :: Developers",
    "License :: OSI Approved :: MIT License",
    "Programming Language :: Python :: 3",
    "Programming Language :: Python :: 3.10",
    "Programming Language :: Python :: 3.11",
    "Programming Language :: Python :: 3.12",
]
dependencies = [
    "pydantic>=2.0",
    "pyyaml>=6.0",
    # ... 其他依赖
]

[project.optional-dependencies]
dev = [
    "pytest>=7.0",
    "pytest-asyncio>=0.21",
]

[project.urls]
Homepage = "https://github.com/ydwangypl/SuperAgent"
Repository = "https://github.com/ydwangypl/SuperAgent"
Issues = "https://github.com/ydwangypl/SuperAgent/issues"

[tool.setuptools.packages.find]
where = ["."]
include = ["SuperAgent*"]
```

2. **或者使用 setup.py**（传统方式）:

```python
# setup.py
from setuptools import setup, find_packages

setup(
    name="superagent-ydwangypl",
    version="3.2.0",
    packages=find_packages(),
    install_requires=[
        "pydantic>=2.0",
        "pyyaml>=6.0",
    ],
    extras_require={
        "dev": ["pytest>=7.0"],
    },
    author="SuperAgent Team",
    description="SuperAgent - Python AI Agent 任务编排库",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    url="https://github.com/ydwangypl/SuperAgent",
    classifiers=[
        "Development Status :: 4 - Beta",
        "Programming Language :: Python :: 3",
    ],
)
```

### 发布步骤

```bash
# 1. 安装构建工具
pip install build twine

# 2. 构建包
python -m build

# 3. 上传到 Test PyPI（测试）
twine upload --repository testpypi dist/*

# 4. 从 Test PyPI 安装测试
pip install --index-url https://test.pypi.org/simple/ superagent-ydwangypl

# 5. 测试通过后，上传到正式 PyPI
twine upload dist/*

# 6. 正式安装
pip install superagent-ydwangypl
```

---

## 在其他项目中使用

### 在 Python 项目中使用

```python
# my_project/main.py
from pathlib import Path
from SuperAgent import Orchestrator, AgentFactory, AgentType

async def main():
    orchestrator = Orchestrator(Path("."))
    agent = AgentFactory().create_agent(AgentType.FULL_STACK_DEV, "MyAgent")
    print("SuperAgent 已就绪!")

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
```

### 在 requirements.txt 中使用

```txt
# requirements.txt
# 使用 Git
git+https://github.com/ydwangypl/SuperAgent.git@v3.2.0

# 或使用 PyPI（发布后）
superagent-ydwangypl>=3.2.0
```

### 在 pyproject.toml 中使用

```toml
[project]
dependencies = [
    "superagent-ydwangypl>=3.2.0",
    # 其他依赖...
]
```

### 在 Docker 中使用

```dockerfile
# Dockerfile
FROM python:3.11-slim

# 安装 SuperAgent
RUN pip install superagent-ydwangypl

WORKDIR /app
COPY . .

CMD ["python", "main.py"]
```

---

## 常见问题

### Q1: 导入时提示 `ModuleNotFoundError: No module named 'SuperAgent'`

**原因**: PYTHONPATH 未配置或包未安装

**解决**:
```bash
# 检查 PYTHONPATH
echo %PYTHONPATH%  # Windows
echo $PYTHONPATH   # Linux/Mac

# 或安装包
pip install -e E:\SuperAgent
```

### Q2: 与 PyPI 上的 `superagent` 包冲突

**原因**: PyPI 上已有同名开源项目 `superagent-ai/superagent`

**解决**:
- 使用独立包名，如 `superagent-ydwangypl`
- 或在文档中说明这是自定义包

### Q3: 导入时遇到 Pydantic 兼容性问题

**原因**: Pydantic v1 和 v2 API 不兼容

**解决**: 使用 Pydantic v2
```bash
pip install pydantic>=2.0
```

### Q4: Windows 路径问题

**原因**: Windows 使用反斜杠 `\`

**解决**:
```python
# 使用原始字符串或正斜杠
path = Path(r"E:\SuperAgent")  # 原始字符串
path = Path("E:/SuperAgent")   # 正斜杠
```

### Q5: 想要在不修改代码的情况下使用不同版本

**解决**: 使用虚拟环境
```bash
# 创建虚拟环境
python -m venv venv

# 激活
venv\Scripts\activate  # Windows
source venv/bin/activate  # Linux/Mac

# 安装特定版本
pip install superagent-ydwangypl==3.2.0
```

---

## 相关文档

- [快速开始](QUICK_START_v3.2.md)
- [完整使用指南](COMPLETE_USER_GUIDE_v3.2.md)
- [API 参考](AGENT_API_REFERENCE.md)
- [架构文档](AGENT_ARCHITECTURE.md)

---

**版本**: v3.2.0
**更新**: 2026-01-19
**维护**: SuperAgent Team
