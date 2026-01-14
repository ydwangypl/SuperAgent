# SuperAgent v3.2 - Claude Code 智能编排系统

> **Claude Code 的增强型任务编排和 Agent 管理插件**
>
> 🎉 **v3.2 新特性**: ✨ 平台适配器重构 | ✨ 任务粒度自动化验证 | ✨ 文档架构降噪
>
> 📊 **系统状态**: 68/68 测试通过 (100%)

---

## 🚀 快速导航

- **[📚 文档中心 (INDEX)](docs/INDEX.md)** - **所有文档、指南和 API 参考的入口**
- **[🏁 快速入门](docs/guides/QUICK_START_v3.2.md)** - 5 分钟上手指南
- **[🛡️ 质量保证](docs/guides/QA_AND_REVIEW_SCHEME.md)** - 审查与测试方案
- **[⚡ 命令速查](docs/guides/COMMANDS_CHEATSHEET.md)** - 常用 CLI 命令汇总
- **[📖 使用指南](docs/guides/COMPLETE_USER_GUIDE_v3.2.md)** - 完整功能说明
- **[💻 示例代码](examples/)** - 各种模式的演示脚本

---

## 🎯 核心定位

**SuperAgent** 是专为 **Claude Code** 设计的增强型任务编排系统。它作为 Claude Code 的智能插件，提供：

1.  **任务持久化**: `TaskListManager` 确保进度永不丢失，支持断点续传。
2.  **增量版本控制**: `GitAutoCommitManager` 为每个任务自动创建清晰的 Git 历史。
3.  **单任务焦点模式**: 自动验证任务粒度，防止上下文爆炸，确保执行效率。
4.  **三层记忆系统**: 跨任务保留关键上下文，提升复杂项目的处理能力。

---

## 🏗️ 架构概览

SuperAgent 采用多层可扩展架构，支持从简单的代码生成到复杂的跨领域（如内容创作、调试）任务：

- **核心抽象层 (`core/`)**: 定义执行器和审查器的统一接口。
- **编排层 (`orchestration/`)**: 处理并发、依赖管理和任务流转。
- **执行层 (`execution/`)**: 具体的业务逻辑执行 Agent（如 `CodingAgent`, `TestingAgent`）。
- **适配器层 (`platform_adapters/`)**: 桥接不同的 AI 平台（Claude, OpenAI, OpenCode）。

---

## 🤝 贡献与反馈

- **[开发人员指南](docs/guides/AGENT_DEVELOPMENT_GUIDE.md)**: 了解如何贡献代码。
- **[贡献者规范](CONTRIBUTING.md)**: 参与项目的基本规则。

*历史报告和过时计划已移至 [docs/archive/](docs/archive/) 目录以保持项目整洁。*


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
# SuperAgent v3.2 - 持续记忆

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

## 📊 v2.2.0 → v3.2 对比

| 特性 | v2.2.0 | v3.2 | 变化 |
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

### v3.2 (当前) - Claude Code插件 ✅

- ✅ 5层完整架构
- ✅ 3层记忆系统
- ✅ 智能任务编排
- ✅ 并行调度能力
- ✅ 自动代码审查

### v3.2 (未来) - 增强功能

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

**A**: 不是。SuperAgent v3.2是Claude Code的插件/工具,负责任务编排和Agent管理,实际的代码生成由Claude Code完成。

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

我们欢迎各种形式的贡献!

### 快速开始

1. Fork 本仓库
2. 创建您的特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交您的更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 开启一个 Pull Request

### 贡献方式

- 🐛 报告 Bug
- 💡 提出新功能
- 📖 改进文档
- 🔧 修复代码
- ✅ 编写测试

**详细指南**: 请参阅 [CONTRIBUTING.md](CONTRIBUTING.md)

### 社区准则

请阅读并遵守我们的 [行为准则](CODE_OF_CONDUCT.md)

### 重点改进方向

1. 更多专业Agent
2. 更智能的记忆查询
3. 更好的可视化
4. 性能优化
5. 平台适配器扩展

### 贡献者

感谢所有贡献者!

<!--
贡献者列表将自动更新
-->

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

- **项目**: SuperAgent v3.2
- **版本**: v3.2.0
- **状态**: ✅ 生产就绪

---

**SuperAgent v3.2 - 让Claude Code更智能!** 🚀
