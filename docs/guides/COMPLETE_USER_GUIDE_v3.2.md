# 📖 SuperAgent v3.2 完整使用指南

> **版本**: v3.2.0
> **更新日期**: 2026-01-14
> **适用对象**: 所有用户

---

## 📑 目录

1. [快速开始](#快速开始)
2. [核心概念](#核心概念)
3. [执行模式选择](#执行模式选择)
4. [功能详解](#功能详解)
5. [完整使用实例](#完整使用实例)
6. [最佳实践](#最佳实践)
7. [故障排查](#故障排查)
8. [API 参考](#api-参考)

---

## 🚀 快速开始

### 安装

```bash
# 克隆仓库
git clone https://github.com/ydwangypl/SuperAgent.git
cd SuperAgent

# 检出 v3.2.0 版本
git checkout v3.2.0

# 安装依赖
pip install -r requirements.txt
```

### 基础配置

```python
from pathlib import Path
from orchestration.orchestrator import Orchestrator
from orchestration.models import OrchestrationConfig

# 项目路径
project_root = Path("/path/to/your/project")

# 创建编排器
orchestrator = Orchestrator(
    project_root=project_root,
    config=OrchestrationConfig()  # 使用默认配置
)
```

### 第一个任务

```python
from planning.models import ExecutionPlan, Step

# 创建简单计划
plan = ExecutionPlan(
    description="创建用户管理功能",
    steps=[
        Step(
            id="step-1",
            description="创建用户模型",
            agent_type="coding",
            inputs={"file_path": "models/user.py"}
        ),
        Step(
            id="step-2",
            description="创建用户API",
            agent_type="coding",
            dependencies=["step-1"],
            inputs={"file_path": "api/user.py"}
        )
    ]
)

# 执行计划
result = await orchestrator.execute_plan(plan)
print(f"完成: {result.completed_tasks}/{result.total_tasks}")
```

---

## 🎯 核心概念

### 架构层次

```
┌─────────────────────────────────────┐
│  Orchestrator (编排层)               │
│  ├─ 任务调度                         │
│  ├─ Agent分发                       │
│  └─ 结果收集                         │
└────────────┬────────────────────────┘
             │
    ┌────────┴────────┐
    │                 │
┌───▼────┐      ┌───▼─────┐
│Planning│      │Execution│
│ 规划层  │      │ 执行层   │
└────────┘      └─────────┘
```

### 核心组件

| 组件 | 职责 | 文件位置 |
|------|------|---------|
| **Orchestrator** | 任务编排和调度 | `orchestration/orchestrator.py` |
| **TaskListManager** | 任务持久化和断点续传 | `core/task_list_manager.py` |
| **GitAutoCommitManager** | 增量版本控制 | `orchestration/git_manager.py` |
| **AgentDispatcher** | Agent分发和调度 | `orchestration/agent_dispatcher.py` |
| **WorktreeOrchestrator** | 隔离工作区管理 | `orchestration/worktree_orchestrator.py` |
| **ReviewOrchestrator** | 代码审查 | `orchestration/review_orchestrator.py` |
| **MemoryManager** | 记忆系统 | `memory/memory_manager.py` |

---

## 🔄 执行模式选择

SuperAgent v3.2 提供**两种执行模式**,可根据任务规模灵活选择:

### 模式对比

| 特性 | 一次性批量执行 | 双代理增量执行 |
|------|---------------|---------------|
| **执行方式** | 一次性执行所有任务 | 每次执行一个任务 |
| **状态保存** | 仅在内存中 | 保存到 `tasks.json` |
| **中断恢复** | ❌ 不支持 | ✅ 支持断点续传 |
| **进度可见** | ❌ 执行完才看到结果 | ✅ 实时进度显示 |
| **Git提交** | 手动或最终提交 | ✅ 每个任务自动提交 |
| **适用场景** | 小任务 (< 1小时) | 大任务 (> 1小时) |
| **配置复杂度** | 简单 | 中等 |

### 模式1: 一次性批量执行

**适用场景**:
- ✅ 小型项目 (< 10个任务)
- ✅ 快速原型开发
- ✅ 测试和验证

**使用方法**:

```python
from orchestration.orchestrator import Orchestrator
from orchestration.models import OrchestrationConfig

# 配置 (使用默认配置即可)
config = OrchestrationConfig(
    # 不需要特殊配置
)

orchestrator = Orchestrator(project_root, config=config)

# 执行计划 (一次性完成所有任务)
result = await orchestrator.execute_plan(plan)

# 检查结果
if result.success:
    print("✅ 所有任务完成")
else:
    print(f"❌ 失败: {result.failed_tasks} 个任务")
```

**特点**:
- ✅ 简单直接,无需额外配置
- ✅ 自动处理依赖关系
- ✅ 并行执行无依赖任务
- ❌ 中断后无法恢复

### 模式2: 双代理增量执行

**适用场景**:
- ✅ 大型项目 (> 10个任务)
- ✅ 需要长时间运行的任务
- ✅ 需要频繁中断/恢复的场景
- ✅ 需要 Git 版本控制的项目

**使用方法**:

```python
from pathlib import Path
from core.task_list_manager import TaskListManager
from orchestration.git_manager import GitAutoCommitManager
from orchestration.orchestrator import Orchestrator
from orchestration.models import OrchestrationConfig, SingleTaskConfig, GitAutoCommitConfig

# 配置
config = OrchestrationConfig(
    # 启用单任务焦点模式
    single_task_mode=SingleTaskConfig(
        enabled=True,
        max_files_per_task=5,        # 每个任务最多修改5个文件
        max_file_size_kb=500,         # 单个文件最大500KB
        enable_auto_split=True        # 自动拆分超范围任务
    ),
    # 启用 Git 自动提交
    git_auto_commit=GitAutoCommitConfig(
        enabled=True,
        commit_message_template="[Task {task_id}] {description}",
        auto_push=False  # 不自动推送到远程
    )
)

# 初始化组件
project_root = Path("/path/to/project")
task_manager = TaskListManager(project_root)
git_manager = GitAutoCommitManager(
    project_root=project_root,
    enabled=True
)

# ===== 阶段1: 初始化 (只运行一次) =====
task_list = task_manager.create_from_plan(plan)
print(f"✅ 已创建 {task_list.total_tasks} 个任务")

# ===== 阶段2: 增量执行 (可多次运行) =====
while True:
    # 1. 获取下一个任务
    task_item = task_manager.get_next_task()
    if not task_item:
        print("✅ 所有任务已完成!")
        break

    print(f"\n📋 执行任务 {task_item.id}: {task_item.description}")

    # 2. 执行任务 (使用 Orchestrator 执行单个任务)
    # 这里需要转换为 ExecutionPlan
    single_plan = ExecutionPlan(
        description=task_item.description,
        steps=[
            Step(
                id=task_item.id,
                description=task_item.description,
                agent_type=task_item.agent_type,
                inputs=task_item.inputs
            )
        ]
    )

    result = await orchestrator.execute_plan(single_plan)

    # 3. 更新任务状态
    if result.success:
        task_manager.update_task(task_item.id, "completed")
        print(f"✅ 任务 {task_item.id} 完成")

        # 4. 自动 Git 提交
        changed_files = result.outputs.get("modified_files", [])
        if changed_files:
            await git_manager.commit_task(
                task_id=task_item.id,
                description=task_item.description,
                changed_files=changed_files
            )
    else:
        task_manager.update_task(task_item.id, "failed")
        print(f"❌ 任务 {task_item.id} 失败")

    # 5. 显示进度
    task_manager.print_progress()

    # 6. 等待3秒后继续 (可选)
    import asyncio
    await asyncio.sleep(3)
```

**特点**:
- ✅ 任务状态持久化到 `tasks.json`
- ✅ 程序中断后可从上次位置继续
- ✅ 实时进度显示
- ✅ 每个任务自动 Git 提交
- ✅ 防止上下文爆炸

### 模式选择决策树

```
开始
  │
  ├─ 任务数量 < 10?
  │    ├─ 是 → 使用【一次性批量执行】
  │    └─ 否 → 继续
  │
  ├─ 预计运行时间 < 1小时?
  │    ├─ 是 → 使用【一次性批量执行】
  │    └─ 否 → 继续
  │
  ├─ 需要频繁中断/恢复?
  │    ├─ 是 → 使用【双代理增量执行】
  │    └─ 否 → 继续
  │
  ├─ 需要 Git 版本控制?
  │    ├─ 是 → 使用【双代理增量执行】
  │    └─ 否 → 使用【一次性批量执行】
```

---

## 🛠️ 功能详解

### 1. TaskListManager - 任务持久化管理

**功能**: 任务列表持久化、断点续传、进度可视化

**核心方法**:

```python
from core.task_list_manager import TaskListManager
from planning.models import ExecutionPlan

manager = TaskListManager(project_root)

# 1. 从计划创建任务列表
task_list = manager.create_from_plan(
    plan=ExecutionPlan(...),
    save_to_file=True  # 保存到 tasks.json
)

# 2. 加载或创建任务列表
loaded_list = manager.load_or_create()

# 3. 获取下一个待执行任务
task = manager.get_next_task()
if task:
    print(f"下一个任务: {task.id} - {task.description}")

# 4. 更新任务状态
manager.update_task(
    task_id="task-001",
    status="running",  # "pending" | "running" | "completed" | "failed"
    output={"result": "成功"}
)

# 5. 显示进度
manager.print_progress()
# 输出: [======>....] 60% (6/10) | 待处理: 4 | 完成: 6 | 失败: 0

# 6. 获取统计信息
stats = manager.get_statistics()
print(f"完成率: {stats['completion_rate']}%")
print(f"平均耗时: {stats['average_duration']}s")

# 7. 重置所有任务状态
manager.reset_all_tasks()

# 8. 删除任务列表文件
manager.delete_task_list()
```

**tasks.json 格式**:

```json
{
  "metadata": {
    "created_at": "2026-01-11T10:00:00",
    "updated_at": "2026-01-11T12:30:00",
    "total_tasks": 10,
    "completed_tasks": 6,
    "failed_tasks": 1
  },
  "tasks": [
    {
      "id": "task-001",
      "description": "创建用户模型",
      "status": "completed",
      "agent_type": "coding",
      "dependencies": [],
      "inputs": {},
      "outputs": {},
      "error": null,
      "started_at": "2026-01-11T10:05:00",
      "completed_at": "2026-01-11T10:15:00",
      "duration_seconds": 600
    }
  ]
}
```

### 2. GitAutoCommitManager - 增量版本控制

**功能**: 自动 Git 提交、提交历史管理

**核心方法**:

```python
from orchestration.git_manager import GitAutoCommitManager

git_manager = GitAutoCommitManager(
    project_root=project_root,
    enabled=True,
    commit_message_template="[Task {task_id}] {description}",
    auto_push=False
)

# 1. 提交单个任务
await git_manager.commit_task(
    task_id="task-001",
    description="实现用户登录功能",
    changed_files=["login.py", "auth.py"],
    summary="添加了登录和认证逻辑"
)

# 2. 提交 tasks.json 更新
await git_manager.commit_tasks_json(
    message="Update task progress: 6/10 completed"
)

# 3. 创建里程碑提交
await git_manager.commit_milestone(
    milestone_name="phase-1-complete",
    description="第一阶段完成: 用户认证系统",
    task_ids=["task-001", "task-002", "task-003"]
)

# 4. 获取提交历史
history = git_manager.get_commit_history(limit=10)
for commit in history:
    print(f"{commit['hash'][:8]}: {commit['message']}")

# 5. 获取任务提交记录
task_commits = git_manager.get_task_commits("task-001")
print(f"任务 task-001 有 {len(task_commits)} 个提交")

# 6. 推送到远程
if git_manager.config.auto_push:
    await git_manager.push_to_remote()
```

**Commit Message 格式**:

```
[Task task-001] 实现用户登录功能

添加了以下功能:
- 用户登录接口
- JWT 认证
- 密码加密

文件变更:
- login.py (新增)
- auth.py (新增)
- models/user.py (修改)

任务摘要: 添加了登录和认证逻辑
```

### 3. SingleTaskMode - 单任务焦点模式

**功能**: 任务范围验证、自动任务拆分

**配置**:

```python
from orchestration.models import OrchestrationConfig, SingleTaskConfig

config = OrchestrationConfig(
    single_task_mode=SingleTaskConfig(
        enabled=True,                  # 启用单任务模式
        max_files_per_task=5,          # 最多修改5个文件
        max_file_size_kb=500,          # 单文件最大500KB
        enable_auto_split=True         # 超限自动拆分
    )
)
```

**验证逻辑**:

```python
# Orchestrator 内部自动验证
def _validate_task_scope(self, task: TaskExecution) -> tuple[bool, str]:
    """验证任务范围"""
    modified_files = task.outputs.get("modified_files", [])

    # 检查文件数量
    if len(modified_files) > config.max_files_per_task:
        return False, f"文件数量超限: {len(modified_files)} > {config.max_files_per_task}"

    # 检查文件大小
    for file_path in modified_files:
        size_kb = file_path.stat().st_size / 1024
        if size_kb > config.max_file_size_kb:
            return False, f"文件大小超限: {file_path} ({size_kb:.1f}KB)"

    return True, None
```

**自动拆分**:

```python
# 超限任务自动拆分为多个子任务
split_task = await orchestrator._split_task(
    task=large_task,
    reason="修改了15个文件,超过限制(5个)"
)

# 返回拆分后的任务
# [
#   Task(id="task-001-1", files=[file1, file2, file3]),
#   Task(id="task-001-2", files=[file4, file5, file6]),
#   ...
# ]
```

### 4. Worktree 隔离

**功能**: 为敏感任务创建隔离工作区

**配置**:

```python
from orchestration.models import WorktreeConfig

config = OrchestrationConfig(
    worktree=WorktreeConfig(
        enabled=True,              # 启用 worktree
        worktree_root="../.superagent-worktrees",  # worktree 根目录
        auto_cleanup=True,         # 任务完成后自动清理
        cleanup_delay=300          # 5分钟后清理
    )
)
```

**使用场景**:

```python
# 任务需要隔离执行时自动创建 worktree
# 例如:
# - 实验性功能开发
# - 重构操作
# - 并行开发多个功能

# Orchestrator 自动处理
async def _execute_by_dependencies(self, tasks, plan):
    for task_batch in ready_tasks:
        # 为每个任务创建 worktree
        await self.worktree_orchestrator.create_for_task(task, agent_type)

        # 执行任务
        await self.scheduler.execute_batch(task_batch)

        # 同步回主分支
        await self.worktree_orchestrator.sync_to_root(task)
```

### 5. 代码审查

**功能**: 自动代码审查和质量检查

**配置**:

```python
from orchestration.models import ReviewConfig

config = OrchestrationConfig(
    review=ReviewConfig(
        enabled=True,               # 启用自动审查
        review_after_each_task=False,  # 每个任务后审查
        review_at_end=True,         # 最后统一审查
        reviewers=["code_quality", "security", "performance"]
    )
)
```

**审查流程**:

```python
# Orchestrator 自动触发审查
result = await orchestrator.execute_plan(plan)

# 审查结果
if result.code_review_summary:
    print(f"审查评分: {result.code_review_summary.score}/100")
    print(f"问题数量: {len(result.code_review_summary.issues)}")

    for issue in result.code_review_summary.issues:
        print(f"[{issue.severity}] {issue.message}")
        print(f"  位置: {issue.file}:{issue.line}")
```

### 6. 记忆系统

**功能**: 从经验中学习,避免重复错误

**配置**:

```python
from memory import MemoryManager

memory_manager = MemoryManager(project_root)

# 查询相关记忆
await memory_manager.query_relevant_memory(
    task="实现用户登录",
    agent_type="coding"
)

# 保存错误教训
await memory_manager.save_mistake(
    error=Exception("数据库连接失败"),
    context="实现用户登录时",
    fix="检查数据库连接字符串",
    learning="需要在启动时验证数据库连接"
)

# 保存成功经验
await memory_manager.save_success(
    context="使用 JWT 实现认证",
    lesson="JWT 密钥需要定期轮换",
    confidence=0.9
)
```

---

## 💻 完整使用实例

### 实例1: 小型项目 - 一次性执行

**场景**: 创建一个简单的博客系统 (5个任务)

```python
import asyncio
from pathlib import Path
from planning.models import ExecutionPlan, Step
from orchestration.orchestrator import Orchestrator
from orchestration.models import OrchestrationConfig
from common.models import AgentType

async def main():
    # 项目路径
    project_root = Path("/path/to/blog")

    # 创建执行计划
    plan = ExecutionPlan(
        description="创建简单博客系统",
        steps=[
            Step(
                id="step-1",
                description="创建文章模型",
                agent_type=AgentType.CODING,
                inputs={
                    "file_path": "models/post.py",
                    "content": """
class Post:
    def __init__(self, title, content, author):
        self.title = title
        self.content = content
        self.author = author
        self.created_at = datetime.now()
                    """
                }
            ),
            Step(
                id="step-2",
                description="创建文章API",
                agent_type=AgentType.CODING,
                dependencies=["step-1"],
                inputs={
                    "file_path": "api/posts.py",
                    "endpoints": ["/posts", "/posts/<id>"]
                }
            ),
            Step(
                id="step-3",
                description="创建前端页面",
                agent_type=AgentType.CODING,
                dependencies=["step-1"],
                inputs={
                    "pages": ["index.html", "post.html"]
                }
            ),
            Step(
                id="step-4",
                description="添加评论功能",
                agent_type=AgentType.CODING,
                dependencies=["step-1", "step-2"],
                inputs={
                    "file_path": "models/comment.py"
                }
            ),
            Step(
                id="step-5",
                description="添加测试",
                agent_type=AgentType.CODING,
                dependencies=["step-1", "step-2", "step-3", "step-4"],
                inputs={
                    "test_file": "tests/test_blog.py"
                }
            )
        ]
    )

    # 创建编排器 (使用默认配置)
    orchestrator = Orchestrator(
        project_root=project_root,
        config=OrchestrationConfig()
    )

    # 执行计划 (一次性完成)
    print("🚀 开始执行博客系统开发...")
    result = await orchestrator.execute_plan(plan)

    # 检查结果
    if result.success:
        print(f"✅ 博客系统开发完成!")
        print(f"   完成任务: {result.completed_tasks}/{result.total_tasks}")
        print(f"   耗时: {result.duration_seconds:.1f}秒")
    else:
        print(f"❌ 开发失败!")
        print(f"   完成任务: {result.completed_tasks}")
        print(f"   失败任务: {result.failed_tasks}")
        if result.errors:
            print(f"   错误: {result.errors}")

if __name__ == "__main__":
    asyncio.run(main())
```

**运行结果**:
```
🚀 开始执行博客系统开发...
INFO: 开始执行项目计划: project-20260111-100000 (步骤数: 5)
INFO: 执行批次: 1 个任务
INFO: 执行批次: 2 个任务
INFO: 执行批次: 1 个任务
INFO: 执行批次: 1 个任务
INFO: 计划执行完成: 5/5 成功, 耗时 180.5s
✅ 博客系统开发完成!
   完成任务: 5/5
   耗时: 180.5秒
```

---

### 实例2: 大型项目 - 双代理增量执行

**场景**: 电商系统开发 (50个任务,预计运行5小时)

```python
import asyncio
from pathlib import Path
from datetime import datetime
from planning.models import ExecutionPlan, Step
from orchestration.orchestrator import Orchestrator
from orchestration.models import (
    OrchestrationConfig,
    SingleTaskConfig,
    GitAutoCommitConfig
)
from core.task_list_manager import TaskListManager
from orchestration.git_manager import GitAutoCommitManager
from common.models import AgentType

class EcommerceProject:
    """电商项目双代理执行示例"""

    def __init__(self, project_root: Path):
        self.project_root = project_root

        # 配置
        self.config = OrchestrationConfig(
            single_task_mode=SingleTaskConfig(
                enabled=True,
                max_files_per_task=5,
                enable_auto_split=True
            ),
            git_auto_commit=GitAutoCommitConfig(
                enabled=True,
                commit_message_template="[Task {task_id}] {description}"
            )
        )

        # 组件
        self.orchestrator = Orchestrator(project_root, config=self.config)
        self.task_manager = TaskListManager(project_root)
        self.git_manager = GitAutoCommitManager(project_root, enabled=True)

    async def run(self, plan: ExecutionPlan):
        # 1. 初始化任务列表
        task_list = self.task_manager.create_from_plan(plan)
        print(f"🚀 电商项目启动: {task_list.total_tasks} 个任务")

        # 2. 循环执行任务
        while True:
            task = self.task_manager.get_next_task()
            if not task:
                break

            print(f"\n📋 [{task.id}] {task.description}")

            # 转换为单任务计划
            single_plan = ExecutionPlan(
                description=task.description,
                steps=[Step(
                    id=task.id,
                    description=task.description,
                    agent_type=task.agent_type,
                    inputs=task.inputs
                )]
            )

            # 执行
            result = await self.orchestrator.execute_plan(single_plan)

            # 更新和提交
            if result.success:
                self.task_manager.update_task(task.id, "completed")
                await self.git_manager.commit_task(
                    task_id=task.id,
                    description=task.description,
                    changed_files=result.outputs.get("modified_files", [])
                )
            else:
                self.task_manager.update_task(task.id, "failed", error=str(result.errors))
                print(f"⚠️ 任务失败: {result.errors}")
                # 策略: 失败后重试或跳过
                # break

            # 显示进度
            self.task_manager.print_progress()

        print("\n✅ 电商项目开发阶段性完成!")

async def main():
    # 假设已有 plan
    project = EcommerceProject(Path("/path/to/ecommerce"))
    # await project.run(large_plan)

if __name__ == "__main__":
    asyncio.run(main())
```

---

## 💡 最佳实践

1. **小步快跑**: 尽量将任务拆分为 30 分钟内可完成的粒度。
2. **启用单任务模式**: 防止 LLM 一次性修改过多文件导致上下文混乱。
3. **利用 Git 自动提交**: 方便在出错时快速回滚到任何一个任务完成的状态。
4. **定期保存 tasks.json**: `TaskListManager` 自动处理，确保进度不丢失。
5. **在隔离区执行**: 对于重构等风险操作，启用 `WorktreeConfig`。

---

## ❓ 故障排查

- **任务执行卡住**: 检查网络连接或 API Key 额度。
- **Git 提交失败**: 确保 `SUPERAGENT_ROOT` 环境变量设置正确，且当前目录是 Git 仓库。
- **任务状态不正确**: 可以手动编辑 `tasks.json` 或调用 `manager.reset_all_tasks()`。
- **上下文超限**: 减小 `max_files_per_task` 或使用更细粒度的任务拆分。

---

## 📚 API 参考

详细的 API 文档请参考: [AGENT_API_REFERENCE.md](AGENT_API_REFERENCE.md)

---

**版本**: v3.2.0
**更新**: 2026-01-14
**维护**: SuperAgent Team
