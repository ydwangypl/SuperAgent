# SuperAgent v3.1 全局配置指南

**在任何项目中使用 SuperAgent v3.1**

---

## 🎯 您的需求

- ✅ 不一定要在 SuperAgent 项目目录下开发
- ✅ 可以在任何项目中使用 SuperAgent v3.1
- ✅ 通过环境变量配置 SuperAgent 路径
- ✅ 使用新的统一接口 (UnifiedAdapter)

**v3.1 新架构**: 核心抽象层 + 适配器层 + 扩展层

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
python -c "from adapters import UnifiedAdapter; print('✅ SuperAgent v3.1 导入成功!')"
```

#### Windows (CMD)

```cmd
REM 临时设置
set SUPERAGENT_ROOT=E:\SuperAgent

REM 验证配置
python -c "from adapters import UnifiedAdapter; print('Success!')"
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
python -c "from adapters import UnifiedAdapter; print('✅ Success!')"
```

---

### 方式 2: 在代码中动态配置

在任何项目的 Python 脚本中:

```python
# your_project/any_script.py

import sys
from pathlib import Path

# 添加 SuperAgent 到路径
superagent_root = Path("E:/SuperAgent")
sys.path.insert(0, str(superagent_root))

# ✅ v3.1 新方式: 使用统一接口
from adapters import UnifiedAdapter
from core.executor import Task

async def main():
    # 初始化适配器
    adapter = UnifiedAdapter(Path("/your/project"))

    # 执行任务并自动审查
    result = await adapter.execute_and_review(
        task_type="code",
        task_data={
            "description": "开发用户登录功能",
            "context": {
                "language": "python",
                "framework": "FastAPI"
            }
        },
        review_config={
            "enable_iterative": True  # 启用Ralph Wiggum循环改进
        }
    )

    # 查看结果
    print(result['summary'])

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
```

---

### 方式 3: 创建便捷导入模块

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

# ✅ v3.1 新架构: 导入核心模块
from adapters import UnifiedAdapter
from core.executor import Executor, Task, ExecutionResult
from core.reviewer import Reviewer, Artifact, ReviewResult
from extensions.writing_executor import WritingExecutor
from extensions.content_reviewer import ContentReviewer

__all__ = [
    'UnifiedAdapter',
    'Executor',
    'Reviewer',
    'Task',
    'ExecutionResult',
    'Artifact',
    'ReviewResult',
    'WritingExecutor',
    'ContentReviewer'
]
```

然后在任何脚本中使用:

```python
# your_project/app.py

from superagent_import import UnifiedAdapter
from pathlib import Path
import asyncio

async def main():
    # 直接使用,无需配置路径
    adapter = UnifiedAdapter(Path("."))

    result = await adapter.execute_and_review(
        task_type="code",
        task_data={"description": "创建用户API"}
    )

asyncio.run(main())
```

---

## 💡 在 Claude Code 中使用

### 在任何项目中使用 SA v3.1

**配置好环境变量后**,您可以在任何项目中使用:

```
您: 使用 SA 开发一个用户登录功能

我 (Claude Code):
  # ✅ v3.1 新方式: 使用统一适配器
  from adapters import UnifiedAdapter
  from pathlib import Path

  adapter = UnifiedAdapter(Path("/your/project"))

  result = await adapter.execute_and_review(
      task_type="code",
      task_data={
          "description": "开发用户登录功能",
          "requirements": [
              "用户注册",
              "用户登录",
              "JWT认证",
              "密码加密"
          ]
      },
      review_config={"enable_iterative": True}
  )

  # 查看结果
  print(result['summary'])
```

**v3.1 优势**:
- ✅ 更简洁的API (一行代码完成执行+审查)
- ✅ 自动集成Ralph Wiggum循环改进
- ✅ 支持多领域 (代码 + 内容 + 未来扩展)
- ✅ 100%向后兼容旧代码

---

## 📝 实际使用示例

### 示例 1: 开发用户登录功能

假设您有一个项目在 `D:\MyProjects\blog`:

```python
# D:\MyProjects\blog\develop_login.py

import sys
from pathlib import Path

# 配置 SuperAgent (如果环境变量未设置)
superagent_root = Path("E:/SuperAgent")
if str(superagent_root) not in sys.path:
    sys.path.insert(0, str(superagent_root))

# ✅ 导入 v3.1 统一接口
from adapters import UnifiedAdapter
import asyncio

async def main():
    # 初始化适配器
    adapter = UnifiedAdapter(Path("."))  # 当前项目目录

    # 开发用户登录功能
    result = await adapter.execute_and_review(
        task_type="code",
        task_data={
            "description": "开发用户登录功能",
            "requirements": [
                "用户注册 (POST /api/register)",
                "用户登录 (POST /api/login)",
                "JWT Token生成",
                "密码哈希存储 (bcrypt)",
                "登录状态验证"
            ],
            "context": {
                "language": "python",
                "framework": "FastAPI",
                "database": "PostgreSQL",
                "security": ["JWT", "bcrypt"]
            }
        },
        review_config={
            "enable_iterative": True,
            "max_iterations": 3,
            "target_score": 85.0
        }
    )

    # 输出结果
    print(f"✅ 执行状态: {result['execution']['success']}")
    print(f"📊 审查评分: {result['review']['overall_score']:.1f}")
    print(f"\n📝 总结:\n{result['summary']}")

if __name__ == "__main__":
    asyncio.run(main())
```

**输出示例**:
```
✅ 执行状态: True
📊 审查评分: 87.5

📝 总结:
✅ 任务执行成功
   执行时间: 2.50秒
   生成产物: 5个

✅ 代码审查通过 (评分: 87.5)
   发现问题: 1个
   - 重要: 建议添加登录失败次数限制

生成文件:
- models/user.py (用户模型)
- api/auth.py (认证API)
- services/auth_service.py (认证服务)
- utils/jwt.py (JWT工具)
- tests/test_auth.py (测试文件)
```

### 示例 2: 批量开发多个功能

```python
# D:\MyProjects\blog\develop_features.py

from adapters import UnifiedAdapter
from pathlib import Path
import asyncio

async def develop_features():
    adapter = UnifiedAdapter(Path("."))

    features = [
        ("用户管理", "创建用户CRUD API"),
        ("文章管理", "创建文章发布和管理功能"),
        ("评论系统", "实现文章评论功能")
    ]

    for feature_name, description in features:
        print(f"\n{'='*50}")
        print(f"开始开发: {feature_name}")
        print(f"{'='*50}\n")

        result = await adapter.execute_and_review(
            task_type="code",
            task_data={"description": description},
            review_config={"enable_iterative": True}
        )

        print(f"✅ {feature_name} - 完成!")
        print(f"评分: {result['review']['overall_score']:.1f}\n")

if __name__ == "__main__":
    asyncio.run(develop_features())
```

### 示例 3: 内容生成 (新功能 ✨)

```python
# 使用 SuperAgent v3.1 生成技术文章

from adapters import UnifiedAdapter
from pathlib import Path
import asyncio

async def main():
    adapter = UnifiedAdapter(Path("."))

    # 生成技术文章
    result = await adapter.execute_and_review(
        task_type="article",
        task_data={
            "description": "如何使用FastAPI构建RESTful API",
            "context": {
                "tone": "professional",
                "length": 1500,
                "audience": "Python开发者",
                "keywords": ["FastAPI", "RESTful", "Python", "API"]
            }
        }
    )

    # 查看生成的内容
    if result['execution']['success']:
        content = result['execution']['content']
        print(content)

        # 内容质量评分
        review = result['review']
        print(f"\n内容质量: {review['overall_score']:.1f}/100")
        print(f"是否通过: {'✅' if review['approved'] else '❌'}")

asyncio.run(main())
```

---

## 🔧 验证配置

### 检查配置是否成功

```python
# 在任何目录下运行
python -c "
import sys
from pathlib import Path

# 设置路径
sys.path.insert(0, 'E:/SuperAgent')

# ✅ 测试 v3.1 新架构导入
from adapters import UnifiedAdapter
from core.executor import Executor
from core.reviewer import Reviewer
from extensions.writing_executor import WritingExecutor
from extensions.content_reviewer import ContentReviewer

print('✅ SuperAgent v3.1 导入成功!')
print('✅ 核心抽象层可用')
print('✅ 适配器层可用')
print('✅ 扩展层可用')
"
```

**预期输出**:
```
✅ SuperAgent v3.1 导入成功!
✅ 核心抽象层可用
✅ 适配器层可用
✅ 扩展层可用
```

---

## 🎯 最佳实践

### ✅ 推荐 (v3.1)

1. **使用 UnifiedAdapter** - 简洁的统一接口
2. **启用循环改进** - 重要任务使用 `enable_iterative=True`
3. **提供详细上下文** - 提高生成质量
4. **设置环境变量** - 一次配置,全局使用
5. **查看快速参考** - [QUICK_REFERENCE.md](QUICK_REFERENCE.md)

### ❌ 避免

1. ❌ 直接使用 Orchestrator (除非需要高级功能)
2. ❌ 忽略 review_config (总是启用代码审查)
3. ❌ 不提供 context (降低生成质量)
4. ❌ 硬编码路径 (使用环境变量)

---

## 📊 v2.0 vs v3.1 对比

| 特性 | v2.0 (旧) | v3.1 (新) |
|------|-----------|-----------|
| **导入方式** | `from orchestration import Orchestrator` | `from adapters import UnifiedAdapter` |
| **代码行数** | ~10行 | ~3行 |
| **自动审查** | 需要手动调用 | 自动集成 |
| **循环改进** | 手动配置 | 一行启用 |
| **多领域支持** | ❌ 仅代码 | ✅ 代码+内容+扩展 |
| **向后兼容** | N/A | ✅ 100% |

**v3.1 示例**:
```python
# ✅ v3.1 - 简洁!
adapter = UnifiedAdapter(project_path)
result = await adapter.execute_and_review(
    task_type="code",
    task_data={"description": "..."},
    review_config={"enable_iterative": True}
)
```

**v2.0 示例**:
```python
# ❌ v2.0 - 复杂
orchestrator = Orchestrator(project_path)
planner = ProjectPlanner()
plan = await planner.create_plan("...")
result = await orchestrator.execute_plan(plan)
reviewer = CodeReviewer()
review = reviewer.review_code(...)
```

---

## 🚀 快速开始 (3步)

### Windows 用户

```powershell
# Step 1: 设置环境变量
[System.Environment]::SetEnvironmentVariable('SUPERAGENT_ROOT', 'E:\SuperAgent', 'User')

# Step 2: 重启 PowerShell

# Step 3: 验证 v3.1
python -c "from adapters import UnifiedAdapter; print('✅ v3.1 Ready!')"
```

### Linux/macOS 用户

```bash
# Step 1: 添加到配置文件
echo 'export SUPERAGENT_ROOT="/path/to/SuperAgent"' >> ~/.bashrc

# Step 2: 重新加载
source ~/.bashrc

# Step 3: 验证 v3.1
python -c "from adapters import UnifiedAdapter; print('✅ v3.1 Ready!')"
```

---

## 💬 使用示例

配置完成后,在任何项目中:

```
您: 使用 SA 开发一个博客系统

我 (Claude Code):
  # ✅ v3.1 新架构
  from adapters import UnifiedAdapter
  from pathlib import Path

  adapter = UnifiedAdapter(Path("/your/project"))

  result = await adapter.execute_and_review(
      task_type="code",
      task_data={
          "description": "开发博客系统",
          "requirements": [
              "文章发布",
              "文章编辑",
              "评论系统",
              "用户管理"
          ]
      },
      review_config={"enable_iterative": True}
  )

  print(result['summary'])
```

**就这么简单!** 🎉

---

## 📚 相关文件

- [QUICK_REFERENCE.md](../../QUICK_REFERENCE.md) - v3.1 完整快速参考
- [COMMANDS_CHEATSHEET.md](../../COMMANDS_CHEATSHEET.md) - 命令行速查
- [docs/USAGE_GUIDE.md](../USAGE_GUIDE.md) - 完整使用指南
- [docs/ARCHITECTURE_COMPARISON.md](../ARCHITECTURE_COMPARISON.md) - 架构对比

---

## 🎓 学习路径

1. **新手上路**: [QUICK_REFERENCE.md](../../QUICK_REFERENCE.md)
2. **深入学习**: [docs/USAGE_GUIDE.md](../USAGE_GUIDE.md)
3. **架构理解**: [docs/ARCHITECTURE_COMPARISON.md](../ARCHITECTURE_COMPARISON.md)
4. **实战示例**: 本文档中的所有代码示例

---

**总结**: 配置一次,在任何项目中使用 SuperAgent v3.1! 🚀

**版本**: v3.1.0
**更新**: 2026-01-11
