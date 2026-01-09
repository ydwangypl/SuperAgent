# SuperAgent v3.0 正确使用指南

**在 Claude Code 环境中使用 SuperAgent**

---

## 🎯 核心理解 (重要!)

### SuperAgent 是什么?

**SuperAgent v3.0** 是一个 **Python 库/模块**,不是独立的 CLI 工具!

```
┌─────────────────────────────────────────────────────────┐
│                  Claude Code 环境                        │
│                                                          │
│  你在这里! ← 正在使用 Claude Code                         │
│                                                          │
│  在 Claude Code 中导入 SuperAgent:                       │
│                                                          │
│  from orchestration import Orchestrator                  │
│  from planning import ProjectPlanner                     │
│                                                          │
│  orchestrator = Orchestrator(Path("."))                  │
│  plan = await planner.create_plan("开发博客系统")        │
│  result = await orchestrator.execute_plan(plan)          │
│                                                          │
└─────────────────────────────────────────────────────────┘
```

### ❌ 错误理解

```bash
# ❌ 这不是 SuperAgent 的正确使用方式!
python -m superagent
# 这只是一个演示/测试 CLI,不是主要使用方式
```

### ✅ 正确理解

**SuperAgent 是一个 Python 库,你在 Claude Code 中导入并使用它!**

---

## 🚀 正确使用方式

### 方式 1: 在 Claude Code 中直接使用 (推荐)

#### Step 1: 在 Claude Code 对话中使用

**你直接对我说**:

```
请使用 SuperAgent 开发一个用户登录功能
```

**我会**:
1. 导入 SuperAgent 模块
2. 初始化 Orchestrator 和 Planner
3. 生成执行计划
4. 执行计划
5. 返回 Agent 生成的需求文档
6. 根据需求文档生成实际代码

#### Step 2: 完整对话示例

**你**: 使用 SuperAgent 开发一个用户登录功能

**我 (Claude Code)**:
```python
# 我会在后台执行这些代码:

from pathlib import Path
from orchestration import Orchestrator
from planning import ProjectPlanner

# 1. 初始化
orchestrator = Orchestrator(Path("."))
planner = ProjectPlanner()

# 2. 生成计划
plan = await planner.create_plan("开发一个用户登录功能")

# 输出计划:
# Step 1: 数据库设计 (database-design)
# Step 2: API 设计 (api-design)
# Step 3: 后端开发 (backend-dev)
# Step 4: 测试 (testing)

# 3. 执行计划
result = await orchestrator.execute_plan(plan)

# 4. Agent 返回需求文档:
# - DATABASE_SCHEMA.md
# - API_SPEC.md
# - REQUIREMENTS.md

# 5. 我会读取这些需求文档,然后生成实际代码
```

**然后我继续**: 根据需求文档生成代码...

---

### 方式 2: Python 脚本中使用

#### 创建脚本文件

```python
# your_project/use_superagent.py

from pathlib import Path
from orchestration import Orchestrator
from planning import ProjectPlanner
import asyncio

async def main():
    # 1. 初始化
    orchestrator = Orchestrator(Path("./my-project"))
    planner = ProjectPlanner()

    # 2. 生成计划
    plan = await planner.create_plan("开发一个用户登录功能")

    # 3. 查看计划
    print("执行计划:")
    for step in plan.steps:
        print(f"  - {step.name} ({step.agent_type})")

    # 4. 执行计划
    result = await orchestrator.execute_plan(plan)

    # 5. 查看结果
    print(f"\n完成: {result.completed_tasks}/{result.total_tasks}")
    print(f"质量评分: {result.code_review_summary['overall_score']}")

    # 6. Agent 返回的需求文档路径
    for task in result.task_executions:
        if task.result and 'artifacts' in task.result:
            print(f"\n需求文档:")
            for name, path in task.result['artifacts'].items():
                print(f"  - {name}: {path}")

if __name__ == "__main__":
    asyncio.run(main())
```

#### 在 Claude Code 中运行

**你**: 运行 use_superagent.py

**我 (Claude Code)**:
```bash
python use_superagent.py
```

**输出**:
```
执行计划:
  - 数据库设计 (database-design)
  - API 设计 (api-design)
  - 后端开发 (backend-dev)
  - 测试 (testing)

完成: 4/4
质量评分: 85.0

需求文档:
  - DATABASE_SCHEMA.md: .superagent/artifacts/DATABASE_SCHEMA.md
  - API_SPEC.md: .superagent/artifacts/API_SPEC.md
  - REQUIREMENTS.md: .superagent/artifacts/REQUIREMENTS.md
```

**然后你继续**: 现在根据这些需求文档生成代码...

---

### 方式 3: 交互式 Python (REPL)

```bash
# 在终端中打开 Python REPL
python

# 或使用 ipython
ipython
```

```python
# 在 REPL 中
from pathlib import Path
from orchestration import Orchestrator
from planning import ProjectPlanner
import asyncio

async def develop():
    orchestrator = Orchestrator(Path("."))
    planner = ProjectPlanner()
    plan = await planner.create_plan("开发博客系统")
    result = await orchestrator.execute_plan(plan)
    return result

# 执行
result = asyncio.run(develop())

# 查看结果
result.task_executions
```

---

## 💡 实际使用场景

### 场景 1: 快速原型开发

**你**: 使用 SuperAgent 规划并开发一个待办事项应用

**我 (Claude Code)**:

```python
# Step 1: 使用 SuperAgent 生成计划
from pathlib import Path
from orchestration import Orchestrator
from planning import ProjectPlanner

orchestrator = Orchestrator(Path("."))
planner = ProjectPlanner()

plan = await planner.create_plan("开发一个待办事项应用")

# 计划内容:
# 1. 数据库设计
# 2. API 设计
# 3. 后端开发
# 4. 前端开发
# 5. 测试
```

```python
# Step 2: 执行计划
result = await orchestrator.execute_plan(plan)
```

```python
# Step 3: 查看需求文档
# 读取 Agent 返回的需求
import json
artifacts = result.task_executions[0].result['artifacts']
```

```python
# Step 4: 根据需求生成实际代码
# (我会根据需求文档生成完整的待办事项应用)
```

---

### 场景 2: 复杂系统开发

**你**: 使用 SuperAgent 开发一个电商系统

**我 (Claude Code)**:

```python
# 1. SuperAgent 生成详细计划
plan = await planner.create_plan("""
开发一个完整的电商系统,包含:
1. 用户管理 (注册、登录、个人中心)
2. 商品管理 (商品列表、详情、搜索)
3. 订单管理 (创建订单、支付、物流)
4. 后台管理 (商品管理、订单管理、用户管理)
""")

# 2. SuperAgent 自动分解为 15-20 个步骤
# 3. 按依赖关系并行执行
# 4. 每个步骤返回需求文档
# 5. 我根据每个需求文档生成代码
```

---

### 场景 3: 查询记忆系统

**你**: 使用 SuperAgent 查询之前遇到的 Token 验证问题

**我 (Claude Code)**:

```python
from pathlib import Path
from memory import MemoryManager

mm = MemoryManager(Path("."))

# 查询相关记忆
relevant = await mm.query_relevant_memory(
    task="Token验证失败",
    agent_type="backend-dev"
)

# 显示历史错误和修复方案
print("历史相关错误:")
for mistake in relevant['mistakes']:
    print(f"错误: {mistake['learning']}")
    print(f"修复: {mistake['fix']}")
```

**输出**:
```
历史相关错误:
错误: JWT Token 时区问题
修复: 使用 datetime.utcnow() 而不是 datetime.now()

错误: Token 过期验证顺序错误
修复: 先验证过期,再验证签名
```

---

## 🛠️ 高级功能

### 1. 自定义配置

```python
from orchestration.models import OrchestrationConfig
from config import SuperAgentConfig

config = SuperAgentConfig(
    project_root=Path("."),
    orchestration=OrchestrationConfig(
        enable_review=True,
        enable_memory=True,
        max_parallel_tasks=5
    )
)

orchestrator = Orchestrator(Path("."), config=config.orchestration)
```

### 2. 手动触发代码审查

```python
from review import CodeReviewer

reviewer = CodeReviewer()

result = reviewer.review_code(
    task_id="review-task",
    files=["src/api/user.py"],
    code_content={
        "user.py": open("src/api/user.py").read()
    }
)

print(f"评分: {result.metrics.overall_score}/100")
print(f"问题: {result.metrics.issue_count}个")
```

### 3. 查看记忆统计

```python
from memory import MemoryManager

mm = MemoryManager(Path("."))

# 获取统计信息
stats = mm.get_statistics()

print(f"总记忆: {stats['total']}")
print(f"  - 情节: {stats['episodic']}")
print(f"  - 语义: {stats['semantic']}")
print(f"  - 程序: {stats['procedural']}")
```

---

## 📝 常见问题修正

### ❓ Q: 如何启动 SuperAgent?

**❌ 错误**: `python -m superagent`

**✅ 正确**:
```python
# 在 Claude Code 中直接使用
from orchestration import Orchestrator
orchestrator = Orchestrator(Path("."))
```

---

### ❓ Q: SuperAgent 和 Claude Code 如何配合?

**A**:
```
你在 Claude Code 中 → 导入 SuperAgent → 使用 SuperAgent 的功能

SuperAgent 负责:
  - 任务规划
  - Agent 管理
  - 记忆系统
  - 代码审查

Claude Code 负责:
  - 执行 Python 代码
  - 生成实际代码
  - 理解需求文档
```

---

### ❓ Q: 我需要单独安装 SuperAgent 吗?

**A**:
**不需要!** SuperAgent 就是当前项目,你已经在使用它了!

直接在 Claude Code 中导入:
```python
from orchestration import Orchestrator
```

---

## 🎯 正确的工作流程

### 开发新功能的完整流程

```
1. 你对我说:
   "使用 SuperAgent 开发一个用户登录功能"

2. 我 (Claude Code) 执行:
   from orchestration import Orchestrator
   from planning import ProjectPlanner

   orchestrator = Orchestrator(Path("."))
   planner = ProjectPlanner()

   plan = await planner.create_plan("开发一个用户登录功能")
   result = await orchestrator.execute_plan(plan)

3. SuperAgent 返回需求文档:
   - DATABASE_SCHEMA.md
   - API_SPEC.md
   - REQUIREMENTS.md

4. 我读取需求文档并生成代码:
   生成 models/user.py
   生成 api/auth.py
   生成 services/auth_service.py
   生成 tests/test_auth.py

5. SuperAgent 自动审查代码:
   质量评分: 85/100
   发现问题: 3个
   改进建议: [...]

6. 保存到记忆系统:
   情节记忆: "任务执行成功"
   语义记忆: "用户认证最佳实践"
   程序记忆: "登录流程步骤"
```

---

## 🚀 快速开始

### 💡 便捷用法

**您可以直接使用 "SA" 或 "sa" 作为 SuperAgent 的简称!**

### 示例 1: 最简单的使用

**您**: 使用 SA 规划一个博客系统

**或者**: 使用 sa 规划一个博客系统

**我**:
```python
from orchestration import Orchestrator
from planning import ProjectPlanner

orchestrator = Orchestrator(Path("."))
planner = ProjectPlanner()

plan = await planner.create_plan("开发一个博客系统")

# 显示计划
for step in plan.steps:
    print(f"{step.name}: {step.agent_type}")
```

### 示例 2: 完整执行

**您**: 使用 SA 开发博客系统并生成代码

**或者**: 使用 sa 开发博客系统并生成代码

**我**:
```python
# 1. 规划和执行
result = await orchestrator.execute_plan(plan)

# 2. 查看需求文档
for task in result.task_executions:
    if task.result and 'artifacts' in task.result:
        artifacts = task.result['artifacts']
        # 读取需求文档
        for name, path in artifacts.items():
            with open(path, 'r') as f:
                requirements = f.read()
            print(f"需求文档 {name}:\n{requirements}\n")

# 3. 根据需求生成代码
# (我会自动根据需求生成代码)
```

---

## 📚 总结

### ✅ 正确理解

1. **SuperAgent 是 Python 库**,不是独立工具
2. **在 Claude Code 中导入使用**
3. **我 (Claude Code) 会帮你调用 SuperAgent**
4. **SuperAgent 返回需求文档**
5. **我根据需求文档生成实际代码**

### 🎯 简单记忆

```
SuperAgent = 任务规划器 + 记忆系统 + 代码审查器
Claude Code = 代码生成器

你 → 对我说 → 我调用 SuperAgent → 返回需求 → 我生成代码
```

### 💡 最佳实践

1. **直接对我说**: "使用 SuperAgent 开发..."
2. **我会自动处理**: 导入、初始化、执行
3. **查看结果**: 需求文档 + 实际代码 + 审查报告

---

**开始使用**:
- 完整说法: "使用 SuperAgent 开发..."
- 简洁说法: "使用 SA 开发..." 或 "使用 sa 开发..."

**无需安装**: SuperAgent 就是当前项目!

**祝使用愉快!** 🎉

---

## 📝 快速参考

### 常用命令 (您可以直接对我说)

| 完整说法 | 简洁说法 | 说明 |
|---------|---------|------|
| 使用 SuperAgent 规划... | 使用 SA 规划... | 生成执行计划 |
| 使用 SuperAgent 开发... | 使用 sa 开发... | 规划并生成代码 |
| 使用 SuperAgent 分析... | 使用 SA 分析... | 分析代码库 |
| 使用 SA 查询记忆... | 使用 sa 查询记忆... | 查询历史经验 |
| 使用 SA 审查代码... | 使用 sa 审查代码... | 代码质量检查 |
