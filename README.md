# SuperAgent v3.1 - Claude Code智能编排系统

> **Claude Code的增强型任务编排和Agent管理插件**
>
> 🎉 **v3.1 新特性**: ✨ 任务持久化 | ✨ 增量版本控制 | ✨ 单任务焦点模式
>
> 📊 **测试覆盖**: 63/63 测试通过 (100%)

**📌 快速导航**:
- [🚀 快速参考卡](QUICK_REFERENCE.md) - 一页纸快速指南
- [⚡ 命令行速查](COMMANDS_CHEATSHEET.md) - 常用命令速查
- [💻 VS Code使用提示](.vscode/SUPERAGENT_GUIDE.md) - IDE开发提示
- [📖 v3.1 发布说明](docs/RELEASE_NOTES_v3.1.md) - 完整更新日志

---

## 🆕 v3.1 核心新功能 (2026-01-11)

### 1. TaskListManager - 任务持久化和断点续传 ✨

**核心价值**: 永不丢失进度,程序中断后可恢复执行

```python
from core.task_list_manager import TaskListManager

# 创建任务列表
manager = TaskListManager(project_root)
task_list = manager.create_from_plan(plan)

# 执行任务
task = manager.get_next_task()
manager.update_task(task.id, "completed")

# 断点续传 - 程序重启后自动恢复
manager2 = TaskListManager(project_root)
loaded_list = manager2.load_or_create()
```

**测试**: 22/22 通过 (100%)

### 2. GitAutoCommitManager - 增量版本控制 ✨

**核心价值**: 每个任务自动创建 Git commit,清晰的版本历史

```python
from orchestration.git_manager import GitAutoCommitManager

# 自动提交任务
await git_manager.commit_task(
    task_id="task-001",
    description="实现用户登录",
    changed_files=["login.py", "auth.py"]
)

# 提交 tasks.json 进度更新
await git_manager.commit_tasks_json()
```

**测试**: 19/19 通过 (100%)

### 3. SingleTaskMode - 单任务焦点模式 ✨

**核心价值**: 任务范围验证 + 自动拆分,防止上下文爆炸

```python
from orchestration.models import OrchestrationConfig, SingleTaskConfig

config = OrchestrationConfig(
    single_task_mode=SingleTaskConfig(
        enabled=True,
        max_files_per_task=5,
        enable_auto_split=True  # 自动拆分大任务
    )
)

# 自动验证和拆分
is_valid, reason = orchestrator._validate_task_scope(task)
if not is_valid:
    split_task = await orchestrator._split_task(task, reason)
```

**测试**: 14/14 通过 (100%)

**完整文档**: [P0 完成总结](docs/P0_COMPLETION_SUMMARY.md)

---

## 🎯 核心定位

**SuperAgent v3.1** 是专为 **Claude Code** 设计的增强型任务编排和Agent管理系统,它不是独立的AI系统,而是作为Claude Code的插件/工具。

### 设计理念

```
┌─────────────────────────────────────────────────────────────┐
│                    Claude Code 环境                          │
│                                                              │
│  ┌──────────────────────────────────────────────────────┐  │
│  │            SuperAgent v3.1 (插件/工具)                │  │
│  │                                                        │  │
│  │  • 智能任务编排    • Agent管理    • 3层记忆系统        │  │
│  └──────────────────────────────────────────────────────┘  │
│                          ↕                                   │
│                   返回需求/框架                               │
│                          ↕                                   │
│  ┌──────────────────────────────────────────────────────┐  │
│  │         Claude Code (代码生成引擎)                     │  │
│  │                                                        │  │
│  │  • 自然语言理解  • 代码生成  • 代码审查  • 调试       │  │
│  └──────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

### 职责分工

| 特性 | SuperAgent v3.1 | Claude Code |
|------|-----------------|-------------|
| **角色** | 任务编排器 / Agent管理器 | 代码生成引擎 |
| **输入** | 项目需求 | 任务需求框架 |
| **输出** | 任务计划、执行框架 | 实际代码、测试、文档 |
| **记忆** | 3层项目记忆系统 | 会话上下文 |
| **Agent** | 返回需求/规格 | 生成代码/测试 |

---

## 🏗️ 多层可扩展架构

### ✨ v3.1 重构亮点 (2026-01-10)

**架构升级**: 引入核心抽象层,支持多领域扩展,完全向后兼容!

```python
# 新架构 - 统一接口,多领域支持
from adapters import UnifiedAdapter
from pathlib import Path

adapter = UnifiedAdapter(Path("/project"))

# ✅ 代码生成和审查 (原有功能)
result = await adapter.execute_and_review(
    task_type="code",
    task_data={"description": "创建用户API"}
)

# ✅ 内容生成和审查 (新功能)
result = await adapter.execute_and_review(
    task_type="article",
    task_data={
        "description": "人工智能发展趋势",
        "context": {"tone": "professional", "length": 800}
    }
)
```

**核心改进**:
- ✅ 新增核心抽象层 (`core/`) - Executor/Reviewer接口
- ✅ 新增适配器层 (`adapters/`) - 桥接新旧系统
- ✅ 新增扩展层 (`extensions/`) - 支持多领域
- ✅ 100%向后兼容 - 现有代码无需修改
- ✅ 符合所有SOLID原则
- ✅ 80个测试,97%+覆盖率

详见: [重构进度总结](docs/reports/REFACTOR_PROGRESS_SUMMARY.md) | [使用指南](docs/USAGE_GUIDE.md)

---

### 第0层: 核心抽象层 (Core Abstraction Layer) ✨ 新增

**文件**: `core/`

**职责**: 定义Executor和Reviewer抽象接口

```python
from core.executor import Executor, Task, ExecutionResult
from core.reviewer import Reviewer, Artifact, ReviewResult

# 任何执行器都需要实现Executor接口
class MyExecutor(Executor):
    def execute(self, task: Task) -> ExecutionResult:
        # 实现执行逻辑
        pass

# 任何审查器都需要实现Reviewer接口
class MyReviewer(Reviewer):
    def review(self, artifact: Artifact) -> ReviewResult:
        # 实现审查逻辑
        pass
```

**核心抽象**:
- `Executor`: 任务执行器抽象
- `Reviewer`: 产物审查器抽象
- `Task`: 统一任务模型
- `ExecutionResult`: 统一执行结果
- `Artifact`: 统一产物模型
- `ReviewResult`: 统一审查结果

---

### 第1层: 对话层 (Conversation Layer)

**文件**: `conversation/`

**职责**: 自然语言意图识别

```python
from conversation import ConversationManager

manager = ConversationManager()
intent = await manager.recognize_intent("开发一个用户管理API")
# 返回: Intent(backend_api_development, confidence=0.95)
```

---

### 第2层: 规划层 (Planning Layer)

**文件**: `planning/`

**职责**: 智能规划,13种专用Agent

```python
from planning import ProjectPlanner

planner = ProjectPlanner()
plan = await planner.generate_plan("开发一个博客系统")

# 自动生成执行计划:
# - Step 1: 数据库设计 (database-design)
# - Step 2: API设计 (api-design) [依赖: Step 1]
# - Step 3: 后端开发 (backend-dev) [依赖: Step 2]
# - Step 4: 测试 (testing) [依赖: Step 3]
```

**13种Agent类型**:
1.  backend-dev - 后端开发
2.  frontend-dev - 前端开发
3.  database-design - 数据库设计
4.  api-design - API设计
5.  testing - 测试
6.  documentation - 文档
7.  deployment - 部署
8.  refactoring - 重构
9.  security - 安全审计
10. performance - 性能优化
11. code-review - 代码审查
12. data-migration - 数据迁移
13. infra-setup - 基础设施

---

### 第3层: 编排层 (Orchestration Layer)

**文件**: `orchestration/`

**职责**: 任务调度、并行执行、3层记忆集成

```python
from orchestration import Orchestrator
from pathlib import Path

orchestrator = Orchestrator(Path("."))

result = await orchestrator.execute_plan(plan)

# 自动处理:
# 1. 查询相关记忆(防止重复错误)
# 2. 依赖感知的并行调度
# 3. Git Worktree隔离(可选)
# 4. 自动错误恢复
```

**关键特性**:
- ✅ 依赖感知的并行执行
- ✅ Git Worktree任务隔离
- ✅ 智能资源管理
- ✅ 快速失败机制

---

### 第4层: 执行层 (Execution Layer)

**文件**: `execution/` + `extensions/` ✨ 扩展

**职责**: 实现Agent逻辑,支持多领域执行器

#### 原有执行器 (execution/)

```python
from execution import CodingAgent

agent = CodingAgent("coding-agent-1")
result = await agent.execute(context, {
    "description": "开发用户管理API"
})
```

**4种核心Agent**:
- `CodingAgent`: 编码Agent - 返回代码需求
- `TestingAgent`: 测试Agent - 返回测试需求
- `DocumentationAgent`: 文档Agent - 返回文档需求
- `RefactoringAgent`: 重构Agent - 返回重构建议

#### 新增扩展执行器 (extensions/) ✨

```python
from extensions.writing_executor import WritingExecutor
from core.executor import Task

executor = WritingExecutor()
result = executor.execute(Task(
    task_type="article",
    description="人工智能发展趋势",
    context={"tone": "professional", "length": 800}
))
```

**扩展执行器**:
- `WritingExecutor`: 写作执行器 - 生成文章、博客、文档
- 未来可添加: `DesignExecutor`, `VideoExecutor`等

---

### 第5层: 审查层 (Review Layer)

**文件**: `review/` + `extensions/` ✨ 扩展

**职责**: 自动代码审查,Ralph Wiggum循环,多领域审查

#### 原有审查器 (review/)

```python
from review import CodeReviewer

reviewer = CodeReviewer()
result = reviewer.review_code(
    task_id="task-1",
    files=["user/api.py"],
    code_content={"user/api.py": "..."}
)
```

**审查维度**:
- 风格检查 (PEP 8规范)
- 安全检查 (SQL注入、XSS等)
- 性能检查 (算法复杂度)
- 最佳实践 (SOLID原则)

#### 新增扩展审查器 (extensions/) ✨

```python
from extensions.content_reviewer import ContentReviewer
from core.reviewer import Artifact

reviewer = ContentReviewer()
result = reviewer.review(Artifact(
    artifact_type="article",
    content="文章内容..."
))
```

**扩展审查器**:
- `ContentReviewer`: 内容审查器 - 5个质量指标
  - 长度审查 (15%)
  - 可读性审查 (25%)
  - 结构审查 (20%)
  - 语法审查 (20%)
  - SEO审查 (20%)
- 未来可添加: `DesignReviewer`, `VideoReviewer`等

---

### 适配器层 (Adapter Layer) ✨ 新增

**文件**: `adapters/`

**职责**: 桥接核心抽象和现有系统

```python
from adapters import UnifiedAdapter
from pathlib import Path

# 统一接口 - 自动选择执行器和审查器
adapter = UnifiedAdapter(Path("/project"))

# 最常用: 执行并审查
result = await adapter.execute_and_review(
    task_type="code",
    task_data={"description": "创建用户API"},
    review_config={"enable_iterative": True}
)

# 返回:
{
    "execution": {...},  # 执行结果
    "review": {...},     # 审查结果
    "summary": "..."      # 综合总结
}
```

**适配器组件**:
- `AgentExecutor`: Agent系统 → Executor接口
- `CodeReviewerAdapter`: CodeReviewer → Reviewer接口
- `UnifiedAdapter`: 高级统一接口 (推荐使用)

---

## 🧠 3层记忆系统

基于认知科学原理,参考Loki Mode设计:

### 第1层: 情节记忆 (Episodic Memory)

记录"发生了什么" - 任务执行历史

```python
await memory_manager.save_episodic_memory(
    event="任务执行: 开发用户管理API\n状态: completed",
    task_id="task-1",
    agent_type="backend-dev"
)
```

### 第2层: 语义记忆 (Semantic Memory)

存储"知道什么" - 项目知识和架构决策

```python
await memory_manager.save_semantic_memory(
    knowledge="项目采用微服务架构,理由:\n1. 模块独立性\n2. 可扩展性",
    category="architecture",
    tags=["microservices", "scalability"]
)
```

### 第3层: 程序记忆 (Procedural Memory)

保持"如何做" - 最佳实践和工作流程

```python
await memory_manager.save_procedural_memory(
    practice="编码最佳实践:\n1. 遵循PEP 8\n2. 使用类型注解",
    category="coding"
)
```

### CONTINUITY.md

人类可读的持续记忆文件:

```markdown
# SuperAgent v3.1 - 持续记忆

## 📝 错误与教训
### 2026-01-08 12:00:00
**错误类型**: ValueError
**上下文**: 任务 task-1 执行失败
**修复方案**: 添加输入验证
**经验教训**: 外部输入必须验证

## 🎯 最佳实践
### coding - 2026-01-08 12:05:00
遵循PEP 8编码规范

## 🏗️ 架构决策
### architecture - 2026-01-08 12:10:00
项目采用微服务架构

## 📊 项目统计
- **总记忆条目**: 150
- **情节记忆**: 80
- **语义记忆**: 45
- **程序记忆**: 25
```

### 自动集成

```python
# 执行前自动查询相关记忆
relevant = await memory_manager.query_relevant_memory(
    task="开发用户管理API",
    agent_type="backend-dev"
)
# 返回: {
#   "mistakes": [...],
#   "best_practices": [...],
#   "architecture_decisions": [...]
# }

# 执行后自动保存情节记忆
await memory_manager.save_episodic_memory(...)

# 错误时自动保存教训
await memory_manager.save_mistake(
    error=e,
    context="任务执行失败",
    fix="修复方案",
    learning="经验教训"
)
```

---

## 🚀 快速开始

### 安装

```bash
# 克隆项目
git clone https://github.com/your-org/SuperAgent.git
cd SuperAgent

# 安装依赖
pip install -r requirements.txt
```

### 基本使用

```python
from pathlib import Path
from orchestration import Orchestrator
from planning import ProjectPlanner

# 1. 初始化
project_root = Path(".")
orchestrator = Orchestrator(project_root)

# 2. 生成计划
planner = ProjectPlanner()
plan = await planner.generate_plan("开发一个博客系统")

# 3. 执行计划
result = await orchestrator.execute_plan(plan)

# 4. 查看结果
print(f"完成任务: {result.completed_tasks}/{result.total_tasks}")
print(f"质量评分: {result.code_review_summary['overall_score']}")
```

### 查看记忆

```bash
# 查看持续记忆文件
cat .superagent/memory/CONTINUITY.md

# 查看记忆统计
python -c "
from pathlib import Path
from memory import MemoryManager
mm = MemoryManager(Path('.'))
print(mm.get_statistics())
"
```

---

## 📊 v2.2.0 → v3.1 对比

| 特性 | v2.2.0 | v3.1 | 变化 |
|------|--------|------|------|
| **定位** | 独立AI系统 | Claude Code插件 | 🔄 架构重构 |
| **代码生成** | 内置LLM | Claude Code | 🔄 移除LLM集成 |
| **记忆系统** | 7层 | 3层 | 🔄 简化优化 |
| **向量数据库** | ✅ | ❌ | ❌ 移除 |
| **Agent输出** | 代码 | 需求/框架 | 🔄 职责分离 |
| **编排能力** | 基础 | 智能并行 | ✅ 增强 |
| **代码审查** | ✅ | ✅ | ✅ 保留 |
| **记忆系统** | 7层 | 3层 | ✅ 优化 |

### v2.2.0特性保留

| 特性 | 保留情况 | 说明 |
|------|---------|------|
| 智能规划 | ✅ 完全保留 | 规划层自动生成完整计划 |
| 并行调度 | ✅ 完全保留 | 编排层依赖感知并行执行 |
| 自动审查 | ✅ 完全保留 | 审查层自动代码审查 |
| Token优化 | ✅ 完全保留 | 智能缓存和Agent重用 |
| 记忆系统 | ✅ 保留并调整 | 从7层简化为3层 |
| 对话层 | ✅ 保留并简化 | 仅保留意图识别 |

### 移除的特性

| 特性 | 移除原因 | 替代方案 |
|------|---------|---------|
| 向量数据库 | Claude Code已有搜索 | 使用Grep/Glob工具 |
| 外部LLM集成 | SuperAgent是Claude Code插件 | 直接使用Claude Code |

---

## 📖 文档

### 核心文档

- [ARCHITECTURE_V3_FINAL.md](ARCHITECTURE_V3_FINAL.md) - 最终架构确认文档
- [docs/MEMORY_SYSTEM_GUIDE.md](docs/MEMORY_SYSTEM_GUIDE.md) - 记忆系统使用指南
- [docs/USER_GUIDE.md](docs/USER_GUIDE.md) - 用户使用指南

### 完成报告

- [PHASE_A_COMPLETION_REPORT.md](PHASE_A_COMPLETION_REPORT.md) - Phase A完成报告
- [PHASE4_COMPLETION_REPORT.md](PHASE4_COMPLETION_REPORT.md) - Phase 4完成报告
- [PHASE5_COMPLETION_REPORT.md](PHASE5_COMPLETION_REPORT.md) - Phase 5完成报告(本阶段)

---

## 🎯 使用场景

### ✅ 适合的场景

- **项目管理**: 智能任务分解和调度
- **知识积累**: 3层记忆系统防止重复错误
- **质量保证**: 自动代码审查和Ralph Wiggum循环
- **团队协作**: 项目知识持续积累

### ❌ 不适合的场景

- **独立代码生成**: 应该使用Claude Code直接生成
- **简单任务**: 单个文件修改不需要SuperAgent
- **非Python项目**: 当前版本主要支持Python

---

## 🔧 技术栈

### 核心依赖

```python
# 数据模型
pydantic >= 2.0.0

# 异步支持
asyncio (标准库)

# Git操作 (可选)
gitpython >= 3.1.0
```

### Python版本

- **最低版本**: Python 3.10+
- **推荐版本**: Python 3.11+

### 平台支持

- **Windows**: ✅ 完全支持
- **macOS**: ✅ 完全支持
- **Linux**: ✅ 完全支持

---

## 📝 开发路线图

### v3.1 (当前) - Claude Code插件 ✅

- ✅ 5层完整架构
- ✅ 3层记忆系统
- ✅ 智能任务编排
- ✅ 并行调度能力
- ✅ 自动代码审查

### v3.1 (未来) - 增强功能

- 📋 更多Agent类型
- 📋 记忆导入/导出
- 📋 Web Dashboard
- 📋 更智能的查询算法

### v3.2 (未来) - 团队协作

- 📋 云端记忆同步
- 📋 多人协作
- 📋 权限管理
- 📋 Agent市场

---

## 💡 常见问题

### Q1: SuperAgent是独立的AI系统吗?

**A**: 不是。SuperAgent v3.1是Claude Code的插件/工具,负责任务编排和Agent管理,实际的代码生成由Claude Code完成。

### Q2: 为什么移除了向量数据库?

**A**: Claude Code已经提供了强大的代码搜索能力(Grep/Glob工具),遵循YAGNI原则,不重复已有功能。

### Q3: 3层记忆系统和7层的区别?

**A**:
- **7层系统**: 包含会话上下文记忆
- **3层系统**: 专注于项目知识(情节/语义/程序),会话上下文由Claude Code管理

### Q4: Agent返回需求而不是代码?

**A**: 这是设计决策。SuperAgent负责编排和规划,Claude Code负责代码生成,职责分离更高效。

### Q5: 如何在项目中使用?

**A**:
1. 初始化Orchestrator
2. 生成执行计划
3. 执行计划(自动集成记忆系统)
4. Claude Code根据需求生成代码

---

## 🤝 贡献指南

欢迎提交Issue和PR!

重点改进方向:
1. 更多专业Agent
2. 更智能的记忆查询
3. 更好的可视化
4. 性能优化

---

## 📄 许可证

MIT License

---

## 🙏 致谢

感谢:
- Anthropic Claude团队
- Claude Code社区
- Loki Mode项目 (asklokesh/claudeskill-loki-mode)
- SuperAgent早期测试用户

---

## 📞 联系方式

- **项目**: SuperAgent v3.1
- **版本**: v3.1.0
- **状态**: ✅ 生产就绪

---

**SuperAgent v3.1 - 让Claude Code更智能!** 🚀
