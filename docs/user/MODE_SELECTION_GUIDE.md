# 🎯 SuperAgent v3.2 执行模式选择指南

> **如何选择适合的执行模式?** - 详细的决策指南和对比分析

---

## 📋 目录

1. [模式概览](#模式概览)
2. [详细对比](#详细对比)
3. [决策树](#决策树)
4. [场景分析](#场景分析)
5. [迁移指南](#迁移指南)

---

## 🔍 模式概览

SuperAgent v3.2 提供**两种执行模式**,可根据项目特点灵活选择:

### 模式1: 一次性批量执行 (Batch Execution)

**定义**: 一次性执行整个计划的所有任务

**核心特点**:
- ✅ 简单直接,开箱即用
- ✅ 自动处理依赖关系
- ✅ 并行执行无依赖任务
- ❌ 状态仅在内存中
- ❌ 中断后无法恢复
- ❌ 无实时进度显示

**代码入口**: `Orchestrator.execute_plan()`

### 模式2: 双代理增量执行 (Incremental Execution)

**定义**: 每次执行一个任务,状态持久化到文件

**核心特点**:
- ✅ 任务状态持久化到 `tasks.json`
- ✅ 支持断点续传
- ✅ 实时进度显示
- ✅ 每个任务自动 Git 提交
- ✅ 防止上下文爆炸
- ⚠️ 配置稍复杂
- ⚠️ 需要管理持久化文件

**核心组件**: `TaskListManager`, `GitAutoCommitManager`, `SingleTaskMode`

---

## 📊 详细对比

### 功能对比表

| 维度 | 一次性批量执行 | 双代理增量执行 |
|------|---------------|---------------|
| **执行方式** | 一次性执行所有任务 | 每次执行一个任务 |
| **状态存储** | 内存 | `tasks.json` 文件 |
| **中断恢复** | ❌ 不支持 | ✅ 完全支持 |
| **进度显示** | ❌ 执行完才显示 | ✅ 实时进度条 |
| **Git集成** | 手动/最终提交 | ✅ 每任务自动提交 |
| **依赖处理** | ✅ 自动处理 | ✅ 自动处理 |
| **并行执行** | ✅ 支持 | ⚠️ 串行执行 |
| **配置复杂度** | ⭐ 简单 | ⭐⭐⭐ 中等 |
| **适合任务数** | < 10 | ≥ 10 |
| **适合时长** | < 1小时 | ≥ 1小时 |
| **代码量** | ~5行 | ~30行 |
| **学习曲线** | 平缓 | 中等 |

### 性能对比

| 指标 | 一次性批量执行 | 双代理增量执行 |
|------|---------------|---------------|
| **启动时间** | 快 (~1秒) | 中等 (~2秒) |
| **执行速度** | 快 (并行) | 中等 (串行) |
| **内存占用** | 高 (所有任务) | 低 (单个任务) |
| **磁盘IO** | 低 | 中等 (频繁读写) |
| **恢复能力** | 无 | 完全 |
| **容错能力** | 低 (全部失败) | 高 (单个失败) |

### 工作流程对比

#### 一次性批量执行

```
开始 → 加载计划 → 执行所有任务 → 返回结果 → 结束
         ↓
    [所有任务加载到内存]
         ↓
    [并行/串行执行]
         ↓
    [完成或全部失败]
```

#### 双代理增量执行

```
初始化 → 创建任务列表 → 保存 tasks.json → 结束
   ↓
执行循环:
  读取 tasks.json → 获取下一个任务 → 执行任务
     ↓
  更新 tasks.json → Git 提交 → 显示进度
     ↓
  等待3秒 → 继续循环
     ↓
  所有任务完成 → 结束
```

---

## 🌳 决策树

### 快速决策流程

```
开始选择
    ↓
任务数量 < 10?
    ├─ 是 → 项目预计时间 < 1小时?
    │   ├─ 是 → 使用【一次性批量执行】
    │   └─ 否 → 继续判断
    └─ 否 → 继续判断
         ↓
需要频繁中断/恢复?
    ├─ 是 → 使用【双代理增量执行】
    └─ 否 → 继续判断
         ↓
需要 Git 版本控制?
    ├─ 是 → 使用【双代理增量执行】
    └─ 否 → 继续判断
         ↓
任务数量 < 20?
    ├─ 是 → 使用【一次性批量执行】
    └─ 否 → 使用【双代理增量执行】
```

### 详细评分表

对每个项目进行评分,总分高的模式更适合:

| 评分项 | 权重 | 一次性 | 增量 | 你的项目 |
|--------|------|--------|------|---------|
| **项目规模** | | | | |
| - 任务数量 < 10 | +3 | ✅ | ❌ | |
| - 任务数量 10-50 | 0 | ❌ | ❌ | |
| - 任务数量 > 50 | -3 | ❌ | ✅ | |
| **时间因素** | | | | |
| - 预计 < 30分钟 | +2 | ✅ | ❌ | |
| - 预计 30分钟-2小时 | 0 | ❌ | ❌ | |
| - 预计 > 2小时 | -2 | ❌ | ✅ | |
| **稳定性需求** | | | | |
| - 可中断 | +3 | ❌ | ✅ | |
| - 不可中断 | -3 | ✅ | ❌ | |
| - 需要恢复 | +3 | ❌ | ✅ | |
| **版本控制** | | | | |
| - 需要 Git 历史 | +2 | ❌ | ✅ | |
| - 不需要 Git | -1 | ✅ | ❌ | |
| **团队协作** | | | | |
| - 多人协作 | +2 | ❌ | ✅ | |
| - 个人开发 | 0 | ❌ | ❌ | |
| **代码复杂度** | | | | |
| - 简单任务 | +1 | ✅ | ❌ | |
| - 复杂任务 | -1 | ❌ | ✅ | |
| **总分** | | | | |

**评分说明**:
- 总分 > 5: 推荐双代理增量执行
- 总分 0-5: 根据实际情况选择
- 总分 < 0: 推荐一次性批量执行

---

## 🎬 场景分析

### 场景1: 快速原型开发

**特点**:
- 任务数: 3-5个
- 预计时间: 10-30分钟
- 需求: 快速验证想法

**推荐模式**: ✅ 一次性批量执行

**理由**:
- 任务少,可一次完成
- 不需要中断/恢复
- 代码简单

**示例代码**:

```python
from pathlib import Path
from planning.models import ExecutionPlan, Step
from orchestration.orchestrator import Orchestrator
from common.models import AgentType

plan = ExecutionPlan(
    description="快速原型",
    steps=[
        Step(id="1", description="创建模型", agent_type=AgentType.CODING),
        Step(id="2", description="创建API", agent_type=AgentType.CODING),
        Step(id="3", description="简单测试", agent_type=AgentType.CODING),
    ]
)

result = await Orchestrator(Path("/proto")).execute_plan(plan)
print(f"✅ 原型完成: {result.completed_tasks}/{result.total_tasks}")
```

---

### 场景2: 中型项目开发

**特点**:
- 任务数: 15-30个
- 预计时间: 2-5小时
- 需求: 需要中断,需要 Git 历史

**推荐模式**: ✅ 双代理增量执行

**理由**:
- 任务较多,可能需要多次运行
- 需要 Git 版本控制
- 需要进度可视化

**示例代码**:

```python
from pathlib import Path
from core.task_list_manager import TaskListManager
from orchestration.git_manager import GitAutoCommitManager
from orchestration.orchestrator import Orchestrator
from orchestration.models import OrchestrationConfig, SingleTaskConfig, GitAutoCommitConfig

project_root = Path("/project")

# 配置
config = OrchestrationConfig(
    single_task_mode=SingleTaskConfig(enabled=True, max_files_per_task=5),
    git_auto_commit=GitAutoCommitConfig(enabled=True)
)

# 初始化
task_manager = TaskListManager(project_root)
git_manager = GitAutoCommitManager(project_root, enabled=True)
orchestrator = Orchestrator(project_root, config=config)

# 创建任务列表
task_list = task_manager.create_from_plan(plan)

# 执行循环 (可多次运行)
while True:
    task = task_manager.get_next_task()
    if not task:
        break

    result = await orchestrator.execute_plan(...)
    task_manager.update_task(task.id, "completed" if result.success else "failed")
    await git_manager.commit_task(...)
    task_manager.print_progress()
```

---

### 场景3: 大型项目重构

**特点**:
- 任务数: 50-100个
- 预计时间: 几天到几周
- 需求: 必须支持断点续传,需要详细 Git 历史

**推荐模式**: ✅ 双代理增量执行 + 自动拆分

**理由**:
- 任务很多,必须增量执行
- 需要防止上下文爆炸
- 需要完整的 Git 历史

**示例代码**:

```python
from orchestration.models import (
    OrchestrationConfig,
    SingleTaskConfig,
    GitAutoCommitConfig
)

# 完整配置
config = OrchestrationConfig(
    single_task_mode=SingleTaskConfig(
        enabled=True,
        max_files_per_task=5,        # 限制文件数量
        max_file_size_kb=500,         # 限制文件大小
        enable_auto_split=True        # 超限自动拆分
    ),
    git_auto_commit=GitAutoCommitConfig(
        enabled=True,
        commit_message_template="[Task {task_id}] {description}",
        auto_push=False
    ),
    enable_early_failure=True  # 快速失败
)

orchestrator = Orchestrator(project_root, config=config)

# ... 后续执行代码同场景2
```

---

### 场景4: CI/CD 自动化

**特点**:
- 任务数: 不定
- 预计时间: < 1小时
- 需求: 自动化,不需要中断

**推荐模式**: ✅ 一次性批量执行

**理由**:
- CI/CD 环境稳定,不需要中断
- 简单直接,易于集成
- 一次执行完成

**示例代码**:

```python
# .github/workflows/ci.yml
name: CI
on: [push]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Run SuperAgent
        run: |
          python -c "
          import asyncio
          from pathlib import Path
          from planning.models import ExecutionPlan
          from orchestration.orchestrator import Orchestrator

          async def test():
              result = await Orchestrator(Path('.')).execute_plan(plan)
              exit(0 if result.success else 1)

          asyncio.run(test())
          "
```

---

### 场景5: 学习和实验

**特点**:
- 任务数: 1-3个
- 预计时间: < 10分钟
- 需求: 快速尝试,理解系统

**推荐模式**: ✅ 一次性批量执行

**理由**:
- 学习阶段,简单为主
- 快速看到结果
- 理解基本流程后再使用高级功能

**示例代码**:

```python
# 最简单的示例
from pathlib import Path
from planning.models import ExecutionPlan, Step
from orchestration.orchestrator import Orchestrator
from common.models import AgentType

plan = ExecutionPlan(
    description="学习示例",
    steps=[
        Step(id="1", description="创建Hello World", agent_type=AgentType.CODING)
    ]
)

result = await Orchestrator(Path("/test")).execute_plan(plan)
print(f"结果: {result.success}")
```

---

## 🔄 模式迁移指南

### 从一次性模式迁移到增量模式

**步骤**:

1. **添加配置**
```python
# 原代码
orchestrator = Orchestrator(project_root)

# 新增配置
from orchestration.models import OrchestrationConfig, SingleTaskConfig, GitAutoCommitConfig

config = OrchestrationConfig(
    single_task_mode=SingleTaskConfig(enabled=True),
    git_auto_commit=GitAutoCommitConfig(enabled=True)
)
orchestrator = Orchestrator(project_root, config=config)
```

2. **添加任务管理器**
```python
from core.task_list_manager import TaskListManager

task_manager = TaskListManager(project_root)
task_list = task_manager.create_from_plan(plan)
```

3. **修改执行逻辑**
```python
# 原代码
result = await orchestrator.execute_plan(plan)

# 新代码
while True:
    task = task_manager.get_next_task()
    if not task:
        break

    result = await orchestrator.execute_plan(...)
    task_manager.update_task(task.id, "completed" if result.success else "failed")
    task_manager.print_progress()
```

4. **添加 Git 管理**
```python
from orchestration.git_manager import GitAutoCommitManager

git_manager = GitAutoCommitManager(project_root, enabled=True)

# 在任务完成后
await git_manager.commit_task(...)
```

### 从增量模式迁移到一次性模式

**步骤**:

1. **移除任务管理器**
```python
# 删除
# task_manager = TaskListManager(project_root)
# task_list = task_manager.create_from_plan(plan)
```

2. **简化执行逻辑**
```python
# 原代码
while True:
    task = task_manager.get_next_task()
    ...

# 新代码
result = await orchestrator.execute_plan(plan)
```

3. **移除 Git 自动提交**
```python
# 删除
# git_manager = GitAutoCommitManager(...)
# await git_manager.commit_task(...)
```

---

## 📈 总结

### 选择建议

| 场景 | 推荐模式 | 理由 |
|------|---------|------|
| 快速原型 | 一次性 | 简单快速 |
| 学习实验 | 一次性 | 易于理解 |
| CI/CD | 一次性 | 自动化友好 |
| 小项目 (< 10任务) | 一次性 | 可一次完成 |
| 中项目 (10-30任务) | 增量 | 需要恢复能力 |
| 大项目 (> 30任务) | 增量 | 必须使用增量 |
| 重构项目 | 增量 + 自动拆分 | 防止上下文爆炸 |
| 团队协作 | 增量 | Git 历史 |
| 长时间运行 | 增量 | 支持中断 |

### 核心原则

1. **从简单开始**: 先使用一次性模式,理解后再升级
2. **按需选择**: 根据实际需求选择,不追求最新功能
3. **可逆性**: 两种模式可以相互转换,不锁定
4. **配置驱动**: 通过配置控制,不修改代码

### 最佳实践

- ✅ 小项目: 一次性执行
- ✅ 大项目: 增量执行
- ✅ 不确定: 先一次性,有问题再切换
- ✅ 生产环境: 增量执行 + 完整配置

---

**文档版本**: v3.2.0
**最后更新**: 2026-01-14

**相关文档**:
- [完整使用指南](COMPLETE_USER_GUIDE_v3.2.md)
- [快速入门](QUICK_START_v3.2.md)
- [API参考](AGENT_API_REFERENCE.md)
