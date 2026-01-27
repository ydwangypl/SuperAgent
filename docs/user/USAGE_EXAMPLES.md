# SuperAgent v3.2 使用示例

> **实战案例** - 了解如何在不同场景下使用 SuperAgent

本文档提供了 SuperAgent v3.2 的实际使用示例,展示如何在 Claude Code 中集成和使用 SuperAgent。

---

## 🚀 快速开始

### 1. 基本使用流程

```python
# 在 Claude Code 中使用 SuperAgent
from pathlib import Path
from orchestration import Orchestrator
from planning import ProjectPlanner
from config import load_config

# 1. 加载配置(可选)
config = load_config()

# 2. 初始化 Orchestrator
orchestrator = Orchestrator(
    project_root=Path("."),
    config=config.orchestration
)

# 3. 创建计划
planner = ProjectPlanner()
plan = await planner.generate_plan("开发一个博客系统")

# 4. 执行计划
result = await orchestrator.execute_plan(plan)

# 5. 查看结果
print(f"完成: {result.completed_tasks}/{result.total_tasks}")
print(f"质量评分: {result.code_review_summary['overall_score']}")
```

---

## 💡 实际场景示例

### 场景 1: 开发用户管理 API

**用户请求**: "开发一个用户管理 API"

#### Step 1: SuperAgent 生成计划

```python
plan = planner.generate_plan("开发一个用户管理 API")

# 生成的计划:
# Step 1: 数据库设计 (database-design)
#   - 设计用户表结构
#   - 定义索引和约束
#
# Step 2: API 设计 (api-design) [依赖: Step 1]
#   - 定义 API 端点
#   - 设计请求/响应格式
#
# Step 3: 后端开发 (backend-dev) [依赖: Step 2]
#   - 实现 API 端点
#   - 实现业务逻辑
#
# Step 4: 测试 (testing) [依赖: Step 3]
#   - 编写单元测试
#   - 编写集成测试
#
# Step 5: 文档 (documentation) [依赖: Step 3]
#   - 生成 API 文档
#   - 编写使用指南
```

#### Step 2: Agent 执行并返回需求

**数据库设计 Agent** 返回:
```markdown
# DATABASE_SCHEMA.md

## 用户表 (users)

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| id | UUID | PRIMARY KEY | 用户 ID |
| username | VARCHAR(50) | UNIQUE, NOT NULL | 用户名 |
| email | VARCHAR(100) | UNIQUE, NOT NULL | 邮箱 |
| password_hash | VARCHAR(255) | NOT NULL | 密码哈希 |
| created_at | TIMESTAMP | NOT NULL | 创建时间 |
| updated_at | TIMESTAMP | NOT NULL | 更新时间 |

## 索引
- idx_users_email (email)
- idx_users_username (username)
```

**API 设计 Agent** 返回:
```markdown
# API_SPEC.md

## 认证端点

### POST /api/auth/register
注册新用户

**请求体**:
```json
{
  "username": "string",
  "email": "string",
  "password": "string"
}
```

**响应**: 201 Created
```json
{
  "user_id": "uuid",
  "username": "string",
  "email": "string"
}
```

### POST /api/auth/login
用户登录

**请求体**:
```json
{
  "email": "string",
  "password": "string"
}
```

**响应**: 200 OK
```json
{
  "access_token": "string",
  "token_type": "bearer"
}
```
```

**后端开发 Agent** 返回:
```markdown
# REQUIREMENTS.md

## 功能需求

1. 用户注册
   - 验证邮箱格式
   - 验证密码强度(至少 8 位)
   - 密码使用 bcrypt 加密
   - 返回用户 ID 和 JWT Token

2. 用户登录
   - 验证邮箱和密码
   - 生成 JWT Token
   - Token 有效期 24 小时

## 技术栈
- Web 框架: FastAPI
- ORM: SQLAlchemy
- 数据验证: Pydantic
- 认证: JWT (python-jose)

## 项目结构
```
src/
├── models/
│   └── user.py          # 用户模型
├── schemas/
│   └── user.py          # Pydantic schemas
├── api/
│   └── auth.py          # 认证路由
├── services/
│   └── auth_service.py  # 认证服务
└── core/
    ├── security.py      # JWT 工具
    └── database.py      # 数据库连接
```
```

#### Step 3: Claude Code 生成实际代码

**Claude Code** 根据需求生成:

```python
# src/models/user.py
from sqlalchemy import Column, String, DateTime
from sqlalchemy.dialects.postgresql import UUID
import uuid
from datetime import datetime

class User(Base):
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    username = Column(String(50), unique=True, nullable=False, index=True)
    email = Column(String(100), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

# src/api/auth.py
from fastapi import APIRouter, HTTPException, Depends
from src.schemas.user import UserRegister, UserLogin
from src.services.auth_service import AuthService

router = APIRouter(prefix="/api/auth", tags=["auth"])

@router.post("/register", status_code=201)
async def register(user_data: UserRegister, auth_service: AuthService = Depends()):
    """注册新用户"""
    # Claude Code 实现注册逻辑
    pass

@router.post("/login")
async def login(user_data: UserLogin, auth_service: AuthService = Depends()):
    """用户登录"""
    # Claude Code 实现登录逻辑
    pass
```

#### Step 4: 自动代码审查

SuperAgent 自动审查生成的代码:

```python
# 审查结果
{
  "overall_score": 85.0,
  "total_issues": 3,
  "critical_count": 0,
  "major_count": 1,
  "minor_count": 2,
  "recommendations": [
    "添加输入验证",
    "使用依赖注入",
    "添加错误处理"
  ]
}
```

#### Step 5: 保存到记忆系统

```python
# SuperAgent 自动保存
await memory_manager.save_episodic_memory(
    event="任务执行: 开发用户管理 API\n状态: completed",
    task_id="task-1",
    agent_type="backend-dev"
)

await memory_manager.save_semantic_memory(
    knowledge="用户认证最佳实践:\n1. 使用 bcrypt 加密密码\n2. JWT Token 有效期 24 小时\n3. 邮箱唯一性约束",
    category="authentication",
    tags=["security", "jwt", "bcrypt"]
)
```

---

### 场景 2: 使用 CLI 工具

```bash
# 启动 SuperAgent CLI
python -m cli.main

# 查看帮助
SuperAgent> help

# 生成计划
SuperAgent> 开发一个博客系统

# 查看生成的计划
SuperAgent> execute plan

# 执行计划
SuperAgent> execute

# 查看结果
SuperAgent> result tasks

# 查看记忆统计
SuperAgent> memory stats

# 查看代码审查结果
SuperAgent> review history

# 查看配置
SuperAgent> config show
```

---

## 📊 完整工作流示例

### 开发任务管理应用

```python
from pathlib import Path
from orchestration import Orchestrator
from planning import ProjectPlanner

async def main():
    # 1. 初始化
    orchestrator = Orchestrator(Path("."))
    planner = ProjectPlanner()

    # 2. 生成计划
    description = """
    开发一个任务管理应用,包含以下功能:
    1. 用户可以创建任务
    2. 任务可以有标签和优先级
    3. 用户可以查看和编辑任务
    4. 支持任务搜索和过滤
    """

    plan = await planner.generate_plan(description)

    # 3. 查看计划
    print("生成的计划:")
    for i, step in enumerate(plan.steps, 1):
        deps = f" (依赖: {step.dependencies})" if step.dependencies else ""
        print(f"{i}. {step.name} ({step.agent_type.value}){deps}")

    # 4. 执行计划
    print("\n开始执行...")
    result = await orchestrator.execute_plan(plan)

    # 5. 查看结果
    print(f"\n执行结果:")
    print(f"  成功: {result.success}")
    print(f"  完成: {result.completed_tasks}/{result.total_tasks}")
    print(f"  耗时: {result.duration_seconds}秒")

    if result.code_review_summary:
        review = result.code_review_summary
        print(f"\n代码审查:")
        print(f"  评分: {review['overall_score']:.1f}/100")
        print(f"  问题: {review['total_issues']}个")

    # 6. 查看记忆
    stats = orchestrator.get_task_statistics()
    if 'memory_stats' in stats:
        memory_stats = stats['memory_stats']
        print(f"\n记忆系统:")
        print(f"  总记忆: {memory_stats['total']}")
        print(f"  - 情节: {memory_stats['episodic']}")
        print(f"  - 语义: {memory_stats['semantic']}")

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
```

---

## 🛠️ 高级用法

### 1. 自定义配置

```python
from config import SuperAgentConfig, MemoryConfig, CodeReviewConfig

# 创建自定义配置
config = SuperAgentConfig(
    project_root=Path("."),
    memory=MemoryConfig(
        enabled=True,
        retention_days=30,
        max_episodic_memories=500
    ),
    code_review=CodeReviewConfig(
        enabled=True,
        min_overall_score=80.0,
        enable_ralph_wiggum=True
    )
)

# 使用自定义配置
orchestrator = Orchestrator(Path("."), config=config.orchestration)
```

### 2. 查询记忆避免重复错误

```python
# 在执行前查询相关记忆
relevant = await orchestrator.memory_manager.query_relevant_memory(
    task="开发用户管理 API",
    agent_type="backend-dev"
)

# 显示相关记忆
if relevant['mistakes']:
    print("⚠️  注意到历史错误:")
    for mistake in relevant['mistakes'][:3]:
        print(f"  - {mistake['learning']}")

if relevant['best_practices']:
    print("✓ 推荐的最佳实践:")
    for practice in relevant['best_practices'][:3]:
        print(f"  - {practice['content']}")
```

### 3. 手动触发代码审查

```python
from review import CodeReviewer, ReviewConfig

# 创建审查器
reviewer = CodeReviewer(ReviewConfig(min_overall_score=80.0))

# 审查代码文件
result = reviewer.review_code(
    task_id="manual-review",
    files=["src/api/user.py", "src/services/auth.py"],
    code_content={
        "user.py": open("src/api/user.py").read(),
        "auth.py": open("src/services/auth.py").read()
    }
)

# 查看结果
print(f"评分: {result.metrics.overall_score}/100")
print(f"问题: {result.metrics.issue_count}个")
```

---

## 🔍 调试和监控

### 1. 查看执行状态

```python
# 获取当前状态
state = orchestrator.get_status()

print(f"项目 ID: {state.project_id}")
print(f"总任务: {state.total_tasks}")
print(f"已完成: {state.completed_tasks}")
print(f"失败: {state.failed_tasks}")
print(f"运行中: {state.running_tasks}")
print(f"待执行: {state.pending_tasks}")
```

### 2. 查看详细统计

```python
# 获取详细统计
stats = orchestrator.get_task_statistics()

print("Agent 统计:")
for agent_type, agent_stats in stats['agent_stats'].items():
    print(f"\n{agent_type}:")
    print(f"  负载: {agent_stats['current_load']}/{agent_stats['max_concurrent']}")
    print(f"  利用率: {agent_stats['utilization']}")
    print(f"  执行次数: {agent_stats['total_executions']}")

if 'memory_stats' in stats:
    memory_stats = stats['memory_stats']
    print("\n记忆统计:")
    print(f"  总计: {memory_stats['total']}")
    print(f"  - 情节: {memory_stats['episodic']}")
    print(f"  - 语义: {memory_stats['semantic']}")
    print(f"  - 程序: {memory_stats['procedural']}")
```

---

## 📝 最佳实践

### 1. 项目初始化

```python
# 初始化新项目时
# 1. 创建配置文件
from config import save_config, SuperAgentConfig

config = SuperAgentConfig(project_root=Path("."))
save_config(config)

# 2. 初始化 Orchestrator
orchestrator = Orchestrator(Path("."))

# 3. 创建第一个计划
plan = await planner.generate_plan("项目初始化")
result = await orchestrator.execute_plan(plan)
```

### 2. 定期维护

```python
# 定期查看和清理记忆
stats = memory_manager.get_statistics()

if stats['episodic'] > 1000:
    # 导出旧记忆
    memory_data = memory_manager.export_memories()
    # 清理旧记忆
    memory_manager.cleanup_old_memories(days=90)
```

### 3. 错误处理

```python
try:
    result = await orchestrator.execute_plan(plan)
except Exception as e:
    # 查看错误详情
    print(f"执行失败: {e}")

    # 查看保存的错误教训
    relevant = await memory_manager.query_relevant_memory(
        task=str(e),
        agent_type=None
    )

    if relevant['mistakes']:
        print("\n相关的错误教训:")
        for mistake in relevant['mistakes']:
            print(f"  - {mistake['learning']}")
            print(f"    修复: {mistake['fix']}")
```

---

## 🎯 常见问题

### Q1: 如何查看 Agent 返回的详细需求?

```python
# 查看特定任务的执行结果
for task in result.task_executions:
    if task.task_id == "task-1":
        print(f"任务: {task.task_id}")
        print(f"状态: {task.status}")
        if task.result:
            print(f"结果: {task.result}")
```

### Q2: 如何导出记忆数据?

```bash
# 使用 CLI
SuperAgent> memory export backup.json

# 或使用 Python
import asyncio
from pathlib import Path
from memory import MemoryManager

async def export_memory():
    mm = MemoryManager(Path("."))

    episodic = await mm.get_episodic_memories(limit=1000)
    semantic = await mm.query_semantic_memory()
    procedural = await mm.get_procedural_memories()

    import json
    with open("backup.json", "w") as f:
        json.dump({
            "episodic": episodic,
            "semantic": semantic,
            "procedural": procedural
        }, f, indent=2)

asyncio.run(export_memory())
```

### Q3: 如何自定义 Agent 输出?

参考 [AGENT_OUTPUT_FORMAT.md](AGENT_OUTPUT_FORMAT.md) 了解标准格式,然后在 Agent 实现中遵循该格式。

---

## 🔗 相关文档

- [AGENT_OUTPUT_FORMAT.md](AGENT_OUTPUT_FORMAT.md) - Agent 输出格式规范
- [MEMORY_SYSTEM_GUIDE.md](MEMORY_SYSTEM_GUIDE.md) - 记忆系统指南
- [ARCHITECTURE_V3_FINAL.md](../ARCHITECTURE_V3_FINAL.md) - 架构文档
- [README.md](../README.md) - 项目总览

---

**SuperAgent v3.2 - 让开发更高效!** 🚀

---
**版本**: v3.2.0
**最后更新**: 2026-01-14
