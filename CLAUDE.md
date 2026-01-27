# SuperAgent v3.4 Context

**SuperAgent** 是一个 Python AI Agent 任务编排库，用于智能任务规划、多 Agent 协作执行。

> **v3.4 新增**: 自然语言接口、HTTP REST API、ProjectGuide 分阶段项目引导
> **v3.3 遗产**: 生命周期钩子系统、3-File 规划模式、环境变量配置支持、安全验证层

---

## 快速使用

### 方式1：Python 直接调用（推荐）

```python
from SuperAgent import UnifiedAdapter

adapter = UnifiedAdapter(project_root=Path("."))
result = adapter.execute_task(
    task_type="coding",
    task_data={"description": "创建一个用户登录模块"}
)
```

### 方式2：项目引导模式（交互式）

```bash
python -m SuperAgent
# 输入: "开发一个电商网站"
# 进入 6 阶段引导: INIT -> REQUIREMENT -> RESEARCH -> DESIGN -> DEVELOPMENT -> TESTING
```

### 方式3：HTTP API 调用

```bash
# 启动服务
python -m server.fastapi_app

# API 调用
curl -X POST http://localhost:8000/api/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "开发一个用户认证模块"}'
```

---

## 核心组件

| 组件 | 简洁导入 | 详细导入 | 说明 |
|------|---------|---------|------|
| **UnifiedAdapter** | `SuperAgent.UnifiedAdapter` | `adapters.unified_adapter` | 统一适配器（执行/审查/测试） |
| **NaturalLanguageParser** | `SuperAgent.NaturalLanguageParser` | `server.interaction_service` | 自然语言解析器 |
| **AgentDispatcher** | `SuperAgent.AgentDispatcher` | `server.interaction_service` | Agent 分派器 |
| **ProjectGuide** | `SuperAgent.ProjectGuide` | `server.interaction_service` | 项目引导器（6阶段） |
| **Orchestrator** | `SuperAgent.Orchestrator` | `orchestration.orchestrator` | 任务编排和调度 |
| **AgentFactory** | `SuperAgent.AgentFactory` | `orchestration.agent_factory` | Agent 工厂 |
| **OrchestrationConfig** | `SuperAgent.OrchestrationConfig` | `orchestration.models` | 编排配置 |
| **BaseAgent** | `SuperAgent.BaseAgent` | `execution.base_agent` | 所有 Agent 的基类 |
| **MemoryManager** | `SuperAgent.MemoryManager` | `memory.memory_manager` | 3层记忆系统 |
| **HookManager** | `SuperAgent.HookManager` | `extensions.hooks` | 生命周期钩子系统 |
| **TaskPlanManager** | `SuperAgent.TaskPlanManager` | `extensions.planning_files` | 3-File 规划管理器 |
| **SessionManager** | `SuperAgent.SessionManager` | `extensions.state_persistence` | 会话状态管理器 |
| **WritingExecutor** | `SuperAgent.WritingExecutor` | `extensions.executors` | 文章写作执行器 |
| **ContentReviewer** | `SuperAgent.ContentReviewer` | `extensions.reviewers` | 内容审查器 |

---

## v3.4 新增特性

### 1. HTTP REST API

**文件**: `server/fastapi_app.py`

**端点**:

| 端点 | 方法 | 说明 |
|------|------|------|
| `/` | GET | 服务健康检查 |
| `/api/chat` | POST | 自然语言对话（自动引导项目） |
| `/api/execute` | POST | 直接执行任务 |
| `/api/review` | POST | 代码审查 |
| `/api/test` | POST | 运行测试 |
| `/api/intent/recognize` | GET | 意图识别 |
| `/api/project/phases` | GET | 获取项目阶段信息 |

**启动服务**:
```bash
python -m server.fastapi_app
# 服务运行在 http://localhost:8000
```

**使用示例**:
```python
import httpx

# 自然语言对话
response = httpx.post("http://localhost:8000/api/chat", json={
    "message": "开发一个在线教育平台",
    "enable_guide": True
})
result = response.json()
# 返回: {"success": True, "phase": "REQUIREMENT", ...}

# 直接执行任务
response = httpx.post("http://localhost:8000/api/execute", json={
    "task_type": "coding",
    "description": "创建用户认证模块"
})
```

### 2. 自然语言解析器

**文件**: `server/interaction_service/natural_language_parser.py`

**任务类型**:

| TaskType | 关键词 | 示例 |
|----------|--------|------|
| **CODING** | 创建、实现、开发、编写、添加 | "创建一个用户登录模块" |
| **RESEARCH** | 研究、调研、分析、调查 | "做竞品分析" |
| **REVIEW** | 审查、审核、检查 | "帮我审查代码" |
| **PLANNING** | 规划、计划、设计、架构 | "规划项目架构" |
| **ANALYSIS** | 分析、性能分析、数据分析 | "性能分析" |

**使用示例**:
```python
from server.interaction_service import NaturalLanguageParser, TaskType

parser = NaturalLanguageParser()

# 解析自然语言
result = parser.parse("我需要做竞品分析")

print(f"类型: {result.task_type}")      # TaskType.RESEARCH
print(f"描述: {result.description}")    # "竞品分析"
print(f"置信度: {result.confidence}")   # 0.95
```

### 3. Agent 分派器

**文件**: `server/interaction_service/agent_dispatcher.py`

**任务到 Agent 映射**:

| 任务类型 | AgentType | Agent 名称 |
|---------|-----------|-----------|
| coding | FULL_STACK_DEV | 全栈开发 |
| research | PRODUCT_MANAGEMENT | 产品管理 |
| review | CODE_REVIEW | 代码审查 |
| planning | API_DESIGN | API 设计与架构 |
| analysis | DATABASE_DESIGN | 数据库设计 |

**使用示例**:
```python
from server.interaction_service import AgentDispatcher

dispatcher = AgentDispatcher(project_root=Path("."))

result = dispatcher.dispatch(
    task_type="coding",
    description="创建用户登录模块"
)

print(f"成功: {result.success}")
print(f"消息: {result.message}")  # "任务已分派给 full-stack-dev"
```

### 4. ProjectGuide 项目引导器

**文件**: `server/interaction_service/project_guide.py`

**6 阶段流程**:

```
INIT (初始) -> REQUIREMENT (需求) -> RESEARCH (研究)
    -> DESIGN (设计) -> DEVELOPMENT (开发) -> TESTING (测试) -> COMPLETE (完成)
```

**使用示例**:
```python
from server.interaction_service import ProjectGuide, ProjectPhase

guide = ProjectGuide(project_root=Path("."))

# 阶段 1: INIT -> REQUIREMENT
guide.handle_input("开发一个电商网站")
print(f"当前阶段: {guide.current_phase}")  # ProjectPhase.REQUIREMENT

# 阶段 2: REQUIREMENT -> RESEARCH
guide.handle_input("需要用户管理、商品展示、购物车、订单管理")
print(f"当前阶段: {guide.current_phase}")  # ProjectPhase.RESEARCH

# 收集的信息
print(guide.project_info)
# {"description": "...", "requirements": [...], ...}
```

### 5. CLI 引导模式

**文件**: `cli/main.py`

当检测到用户要创建新项目时，自动进入引导模式：

```bash
$ python -m SuperAgent
SuperAgent> 我想开发一个社交媒体应用

  项目引导模式 (v3.4)
  ====================

  阶段 1/6: 需求分析

  请描述您的项目需求：
  >
```

**自动检测规则**:
- NEW_PROJECT 意图 → 进入引导模式
- ADD_FEATURE 意图且置信度 ≥ 0.6 → 进入引导模式
- 简单命令（help、status、fix bug）→ 跳过引导

---

## v3.3 遗产特性

### 1. 生命周期钩子系统 (Hook System)

```python
from extensions.hooks import HookManager, HookContext, HookResult, LifecycleHookType
from extensions.hooks.lifecycle_hooks import ReReadPlanHook

hook_manager = HookManager(memory_manager=None)
hook = ReReadPlanHook(task_plan_manager=my_tpm)
hook_manager.register(hook)
```

### 2. 3-File 规划模式 (Planning-with-Files)

**文件**: `extensions/planning_files/__init__.py`

SuperAgent 的双重记忆架构：
1. **MemoryManager** - 内存中的 3 层记忆（episodic/semantic/procedural）
2. **Planning Files** - 持久化的 3-File 模式（task_plan.md / findings.md / progress.md）

**设计理念**:
- **JSON → MD 单向同步**: tasks.json 为唯一真实来源，task_plan.md 为人类可读视图
- **与 MemoryManager 联动**: findings.md 同步到 semantic_memory
- **会话进度持久化**: progress.md 记录每次会话的进展

**3-File 结构**:

| 文件 | 路径 | 说明 |
|------|------|------|
| `task_plan.md` | 项目根目录 | 人类可读的任务规划（checkbox 格式） |
| `progress.md` | `docs/progress.md` | 会话进度日志（Action/Status/Details） |
| `findings.md` | `docs/findings.md` | 研究发现（Category/Impact/Source） |

**TaskPlanManager 使用**:
```python
from extensions.planning_files import TaskPlanManager
from pathlib import Path

# 初始化
tpm = TaskPlanManager(
    project_root=Path("."),
    plan_file=Path("task_plan.md"),
    auto_save=True
)

# 创建计划
await tpm.create_plan(
    requirements={"user_input": "开发电商网站"},
    steps=[
        {"step_id": "step_1", "name": "需求分析", "agent_type": "ProductAgent", "description": "收集需求"},
    ],
    dependencies={},
    metadata={"complexity": "high", "tech_stack": ["Python", "React"]}
)

# 更新任务状态
await tpm.update_task_status("step_1", "completed")  # checkbox 变为 [x]
await tpm.update_task_status("step_2", "in_progress")  # checkbox 变为 [/]

# 获取完成度报告
report = await tpm.get_completion_report()
print(f"进度: {report.completed_count}/{report.total_count}")
```

**FindingsManager 使用**:
```python
from extensions.planning_files import FindingsManager
from memory.memory_manager import MemoryManager

memory_manager = MemoryManager(project_root=Path("."))

# 初始化（与 MemoryManager 联动）
fm = FindingsManager(
    project_root=Path("."),
    findings_file=Path("docs/findings.md"),
    memory_manager=memory_manager  # 自动同步到 semantic_memory
)

# 添加研究发现
finding_id = await fm.add_finding(
    content="发现 Django 的性能瓶颈在数据库查询优化",
    category="performance",
    impact="影响 20% 的 API 响应时间",
    source="代码审查"
)

# 查询相关发现
findings = await fm.get_relevant_findings("性能 优化")
```

**ProgressManager 使用**:
```python
from extensions.planning_files import ProgressManager

pm = ProgressManager(
    project_root=Path("."),
    progress_file=Path("docs/progress.md"),
    session_id="20260127_143000"
)

# 记录进度
await pm.log_progress(
    action="执行 UserAgent: 创建用户模型",
    status="completed",
    details="已创建 User model 和 CRUD 接口"
)

# 记录会话总结
await pm.log_session_summary(
    task_count=5,
    status="completed",
    errors=["部分测试用例超时"]
)
```

**自动集成**:
这些管理器在 `Orchestrator` 初始化时自动创建，并在以下时机被调用：

| 管理器 | 触发时机 | 写入文件 |
|--------|---------|---------|
| TaskPlanManager | `execute_plan()` / `update_task_status()` | task_plan.md |
| ProgressManager | Agent 执行前后 | progress.md |
| FindingsManager | `save_finding()` 调用时 | findings.md |

### 3. 环境变量配置支持

```bash
export SUPERAGENT_LOG_LEVEL=DEBUG
export SUPERAGENT_MEMORY_ENABLED=true
```

---

## Agent 类型 (AgentType)

```python
from SuperAgent import AgentType

AgentType.FULL_STACK_DEV      # 全栈开发
AgentType.BACKEND_DEV         # 后端开发
AgentType.FRONTEND_DEV        # 前端开发
AgentType.CODE_REVIEW         # 代码审查
AgentType.API_DESIGN          # API 设计
AgentType.QA_ENGINEERING      # 测试工程
AgentType.DEVOPS              # DevOps
AgentType.PRODUCT_MANAGEMENT  # 产品管理 (v3.4)
AgentType.DATABASE_DESIGN     # 数据库设计 (v3.4)
```

---

## 使用模式

### 1. Python 直接调用（推荐）

```python
from SuperAgent import UnifiedAdapter

adapter = UnifiedAdapter(project_root=Path("."))

# 单一任务
result = adapter.execute_task(
    task_type="coding",
    task_data={"description": "创建用户登录模块"}
)

# 完整工作流：执行 + 审查 + 测试
result = await adapter.execute_and_review_and_test(
    task_type="coding",
    task_data={"description": "实现功能"},
    review_config={"verbose": True},
    test_config={"test_path": "tests"}
)
```

### 2. 项目引导模式（交互式）

```bash
python -m SuperAgent
# 输入项目需求，自动引导完成 6 阶段
```

### 3. HTTP API 服务

```bash
# 启动服务
python -m server.fastapi_app

# HTTP 调用
import httpx
response = httpx.post("http://localhost:8000/api/execute", json={
    "task_type": "planning",
    "description": "设计系统架构"
})
```

### 4. CLI 命令行（直接执行）

```bash
python -m SuperAgent "创建一个用户登录模块"
# 直接执行，不进入引导模式
```

---

## 关键类和方法

### UnifiedAdapter (v3.4 推荐)
- `execute_task(task_type, task_data)` - 执行任务
- `run_tests(test_path, config)` - 运行测试
- `review_code(artifact_data, config)` - 代码审查
- `execute_and_review_and_test(...)` - 完整工作流

### NaturalLanguageParser (v3.4)
- `parse(text)` - 解析自然语言，返回 ParsedRequest
- `parse_with_alternatives(text)` - 返回所有可能类型

### AgentDispatcher (v3.4)
- `dispatch(task_type, description, options)` - 同步分派
- `dispatch_async(task_type, description, options)` - 异步分派

### ProjectGuide (v3.4)
- `handle_input(user_input)` - 处理用户输入，推进阶段
- `current_phase` - 当前阶段
- `project_info` - 收集的项目信息

### Orchestrator
- `execute_plan(plan)` - 执行任务计划
- `execute_task(task)` - 执行单个任务

### MemoryManager
- `save_episodic_memory(content, metadata)` - 保存情节记忆
- `save_semantic_memory(content, category, metadata)` - 保存语义记忆
- `save_procedural_memory(content, category, metadata)` - 保存程序记忆
- `query_semantic_memory(query)` - 查询语义记忆

---

## 配置选项

### TestingConfig (测试配置)
```python
from SuperAgent import TestingConfig

config = TestingConfig(
    enabled=True,
    test_path="tests",
    fail_on_failure=False,
    coverage=False,
    markers=None,
    verbose=True,
    timeout=300
)
```

---

## 注意事项

1. 路径分隔符使用 `/` (跨平台)
2. 异步方法需要 `await` 调用
3. 推荐使用 `async def main(): ... asyncio.run(main())`
4. v3.4 支持 3 种调用方式：Python SDK / HTTP API / CLI 引导
5. MCP Server 需要 `pip install mcp` (可选)
