# SuperAgent 全局配置指南

**在任何项目中使用 SuperAgent**

---

## 🎯 您的需求

- ✅ 不一定要在 SuperAgent 项目目录下开发
- ✅ 可以在任何项目中使用 SuperAgent
- ✅ 通过环境变量配置 SuperAgent 路径

---

## 🚀 解决方案

### 方式 1: 设置环境变量 (推荐)

#### Windows (PowerShell)

```powershell
# 1. 临时设置 (当前会话)
$env:SUPERAGENT_ROOT = "E:\SuperAgent"

# 2. 永久设置 (添加到系统环境变量)
[System.Environment]::SetEnvironmentVariable('SUPERAGENT_ROOT', 'E:\SuperAgent', 'User')

# 3. 验证配置
python -c "from orchestration import Orchestrator; print('✅ SuperAgent 导入成功!')"
```

#### Windows (CMD)

```cmd
REM 临时设置
set SUPERAGENT_ROOT=E:\SuperAgent

REM 验证配置
python -c "from orchestration import Orchestrator; print('Success!')"
```

#### Linux/macOS (bash/zsh)

```bash
# 1. 编辑 shell 配置文件
nano ~/.bashrc  # 或 ~/.zshrc

# 2. 添加以下内容
export SUPERAGENT_ROOT="/path/to/SuperAgent"

# 3. 重新加载配置
source ~/.bashrc  # 或 source ~/.zshrc

# 4. 验证配置
python -c "from orchestration import Orchestrator; print('✅ Success!')"
```

---

### 方式 2: 使用自动设置脚本

我已经为您创建了一个自动设置脚本:

```bash
# 运行设置脚本
python e:\SuperAgent\setup_superagent.py
```

这个脚本会:
- ✅ 自动检测 SuperAgent 目录
- ✅ 设置环境变量
- ✅ 验证安装
- ✅ 提供使用说明

---

### 方式 3: 在代码中动态配置

在任何项目的 Python 脚本中:

```python
# your_project/any_script.py

import sys
from pathlib import Path

# 添加 SuperAgent 到路径
superagent_root = Path("E:/SuperAgent")
sys.path.insert(0, str(superagent_root))

# 现在可以导入 SuperAgent
from orchestration import Orchestrator
from planning import ProjectPlanner

# 使用 SuperAgent
orchestrator = Orchestrator(Path("."))
planner = ProjectPlanner()

plan = await planner.create_plan("开发用户登录功能")
result = await orchestrator.execute_plan(plan)
```

---

### 方式 4: 创建便捷导入模块

在任何项目中创建一个便捷导入文件:

```python
# your_project/superagent_import.py

import sys
from pathlib import Path

# 配置 SuperAgent 路径
SUPERAGENT_ROOT = Path("E:/SuperAgent")

# 添加到路径
if str(SUPERAGENT_ROOT) not in sys.path:
    sys.path.insert(0, str(SUPERAGENT_ROOT))

# 导入并重新导出核心模块
from orchestration import Orchestrator
from planning import ProjectPlanner
from config import load_config
from memory import MemoryManager

__all__ = [
    'Orchestrator',
    'ProjectPlanner',
    'load_config',
    'MemoryManager'
]
```

然后在任何脚本中使用:

```python
# your_project/app.py

from superagent_import import Orchestrator, ProjectPlanner

# 直接使用,无需配置路径
orchestrator = Orchestrator(Path("."))
```

---

## 💡 在 Claude Code 中使用

### 在任何项目中使用 SA

**配置好环境变量后**,您可以在任何项目中使用:

```
您: 使用 SA 开发一个用户登录功能

我 (Claude Code):
  # 自动导入 SuperAgent
  from orchestration import Orchestrator

  # 在您的项目中使用
  orchestrator = Orchestrator(Path("/your/project/path"))

  # 生成计划并执行
  plan = await planner.create_plan("...")
  result = await orchestrator.execute_plan(plan)
```

---

## 📝 实际使用示例

### 示例 1: 在其他项目中使用

假设您有一个项目在 `D:\MyProjects\blog`:

```bash
# 1. 进入项目目录
cd D:\MyProjects\blog

# 2. 设置环境变量 (如果还没设置)
# Windows PowerShell
$env:SUPERAGENT_ROOT = "E:\SuperAgent"

# 3. 创建 Python 脚本
# develop.py
```

```python
# D:\MyProjects\blog\develop.py

import sys
from pathlib import Path

# 配置 SuperAgent (如果环境变量未设置)
superagent_root = Path("E:/SuperAgent")
if str(superagent_root) not in sys.path:
    sys.path.insert(0, str(superagent_root))

# 导入 SuperAgent
from orchestration import Orchestrator
from planning import ProjectPlanner
import asyncio

async def main():
    # 初始化 (在当前项目中)
    orchestrator = Orchestrator(Path("."))  # 当前项目目录
    planner = ProjectPlanner()

    # 开发功能
    plan = await planner.create_plan("开发博客系统")
    result = await orchestrator.execute_plan(plan)

    print(f"完成: {result.completed_tasks}/{result.total_tasks}")

if __name__ == "__main__":
    asyncio.run(main())
```

### 示例 2: 配置后在任何地方使用

**配置好环境变量后**,创建全局配置文件:

```python
# ~/.superagent_config.py (或 C:\Users\YourName\.superagent_config.py)

import sys
from pathlib import Path
import os

# 从环境变量读取
SUPERAGENT_ROOT = Path(os.environ.get("SUPERAGENT_ROOT", "E:/SuperAgent"))

# 添加到路径
if str(SUPERAGENT_ROOT) not in sys.path:
    sys.path.insert(0, str(SUPERAGENT_ROOT))

# 导入核心模块
from orchestration import Orchestrator
from planning import ProjectPlanner
from config import load_config
from memory import MemoryManager

# 提供便捷函数
def create_orchestrator(project_path="."):
    """创建 Orchestrator 实例"""
    return Orchestrator(Path(project_path))

def create_planner():
    """创建 Planner 实例"""
    return ProjectPlanner()
```

然后在任何项目中:

```python
# your_project/app.py

# 导入全局配置
import sys
from pathlib import Path

# 加载全局配置
config_path = Path.home() / ".superagent_config.py"
if config_path.exists():
    with open(config_path) as f:
        exec(f.read())

# 直接使用
orchestrator = create_orchestrator(".")
planner = create_planner()
```

---

## 🔧 验证配置

### 检查配置是否成功

```bash
# 运行验证脚本
python e:\SuperAgent\setup_superagent.py
```

预期输出:
```
============================================================
SuperAgent 全局设置向导
============================================================

检测到 SuperAgent 目录: E:\SuperAgent

验证安装...
✅ SuperAgent 安装验证成功!
   SuperAgent 根目录: E:\SuperAgent
   Python 版本: 3.11.0

============================================================
🎉 设置完成!
============================================================

您现在可以在任何项目中使用 SuperAgent:
...
```

### 手动验证

```python
# 在任何目录下运行
python -c "
import sys
from pathlib import Path

# 设置路径
sys.path.insert(0, 'E:/SuperAgent')

# 测试导入
from orchestration import Orchestrator
print('✅ SuperAgent 导入成功!')
"
```

---

## 🎯 最佳实践

### ✅ 推荐

1. **设置环境变量** (一次配置,全局使用)
2. **创建全局配置文件** (~/.superagent_config.py)
3. **在每个项目中创建本地配置** (superagent_import.py)

### ❌ 避免

1. ❌ 在每个脚本中硬编码路径
2. ❌ 复制 SuperAgent 代码到每个项目
3. ❌ 修改 SuperAgent 源码以适应特定项目

---

## 📊 配置对比

| 方式 | 优点 | 缺点 | 推荐度 |
|------|------|------|--------|
| 环境变量 | 一次配置,全局使用 | 需要系统设置 | ⭐⭐⭐⭐⭐ |
| 自动设置脚本 | 简单快速 | 需要运行脚本 | ⭐⭐⭐⭐ |
| 代码中动态配置 | 灵活 | 每个脚本都要写 | ⭐⭐⭐ |
| 全局配置文件 | 便捷导入 | 需要维护文件 | ⭐⭐⭐⭐ |

---

## 🚀 快速开始 (3步)

### Windows 用户

```powershell
# Step 1: 设置环境变量
[System.Environment]::SetEnvironmentVariable('SUPERAGENT_ROOT', 'E:\SuperAgent', 'User')

# Step 2: 重启 PowerShell

# Step 3: 验证
python -c "from orchestration import Orchestrator; print('✅ Success!')"
```

### Linux/macOS 用户

```bash
# Step 1: 添加到配置文件
echo 'export SUPERAGENT_ROOT="/path/to/SuperAgent"' >> ~/.bashrc

# Step 2: 重新加载
source ~/.bashrc

# Step 3: 验证
python -c "from orchestration import Orchestrator; print('✅ Success!')"
```

---

## 💬 使用示例

配置完成后,在任何项目中:

```
您: 使用 SA 开发一个博客系统

我 (Claude Code):
  # 自动导入 SuperAgent (从环境变量)
  from orchestration import Orchestrator

  # 在您的项目中使用
  orchestrator = Orchestrator(Path("/your/project"))

  # 继续正常流程...
```

---

## 📚 相关文件

- [setup_superagent.py](e:\SuperAgent\setup_superagent.py) - 自动设置脚本
- [HOW_TO_USE_CORRECT.md](e:\SuperAgent\HOW_TO_USE_CORRECT.md) - 使用指南
- [QUICK_REFERENCE.md](e:\SuperAgent\QUICK_REFERENCE.md) - 快速参考

---

**总结**: 配置一次,在任何项目中使用 SuperAgent! 🎉
