# SuperAgent v3.4 - AI Agent 任务编排系统

> **智能任务规划、多 Agent 协作执行、自然语言接口**

> 🎉 **v3.4 新特性**: ✨ HTTP REST API | ✨ 自然语言解析 | ✨ ProjectGuide 分阶段引导 | ✨ MCP Server 可选集成

> 📊 **系统状态**: E2E 97.3% | 集成 92.5% | NLP 100%

---

## 🚀 快速导航

- **[📂 文档中心 (INDEX)](docs/INDEX.md)** - 快速查找所有指南
- **[📚 完整用户指南](docs/user/COMPLETE_USER_GUIDE_v3.2.md)** - 完整功能说明
- **[🏁 快速入门](docs/user/QUICK_START_v3.2.md)** - 5 分钟上手
- **[🛡️ 质量保证](docs/developer/QA_AND_REVIEW_SCHEME.md)** - 审查与测试方案
- **[📖 发布说明](docs/RELEASE_NOTES_v3.4.md)** - v3.4 更新详情

---

## 快速使用

### 方式1：Python 直接调用（推荐）

```python
from SuperAgent import UnifiedAdapter
from pathlib import Path

adapter = UnifiedAdapter(project_root=Path("."))

# 执行任务
result = adapter.execute_task(
    task_type="coding",
    task_data={"description": "创建一个用户登录模块"}
)
```

### 方式2：CLI 交互式引导

```bash
python -m SuperAgent
# 输入: "开发一个电商网站"
# 自动进入 6 阶段引导
```

### 方式3：HTTP API 服务

```bash
# 启动服务
python -m server.fastapi_app

# API 调用
curl -X POST http://localhost:8000/api/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "开发一个用户认证模块"}'
```

---

## 🎯 核心定位

**SuperAgent** 是专为 AI Agent 设计的任务编排系统，支持：

1. **自然语言接口**: 理解用户意图，自动分派到正确的 Agent
2. **分阶段项目引导**: 6 阶段流程（INIT → REQUIREMENT → RESEARCH → DESIGN → DEVELOPMENT → TESTING）
3. **多 Agent 协同**: 13 种专业 Agent（开发、测试、架构、产品管理等）
4. **任务持久化**: 断点续传，状态永不丢失
5. **三层记忆系统**: 跨任务保留关键上下文

---

## 🏗️ 架构概览

```
┌─────────────────────────────────────────────────────────┐
│                    外部调用层                             │
│  ┌───────────┐  ┌───────────┐  ┌───────────┐           │
│  │  Python   │  │  HTTP API │  │   CLI     │           │
│  │   SDK     │  │  (FastAPI)│  │  交互式   │           │
│  └─────┬─────┘  └─────┬─────┘  └─────┬─────┘           │
└────────┼──────────────┼──────────────┼──────────────────┘
         │              │              │
         ▼              ▼              ▼
┌─────────────────────────────────────────────────────────┐
│                  交互服务层 (v3.4)                       │
│  ┌─────────────────┐  ┌─────────────────┐               │
│  │NaturalLanguage  │  │  AgentDispatcher│               │
│  │Parser           │  │                 │               │
│  └────────┬────────┘  └────────┬────────┘               │
│           │                    │                         │
│           ▼                    ▼                         │
│  ┌─────────────────┐  ┌─────────────────┐               │
│  │  ProjectGuide   │  │  IntentRecognizer│               │
│  │  (6阶段引导)     │  │                 │               │
│  └─────────────────┘  └─────────────────┘               │
└─────────────────────────────┬───────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────┐
│                    编排执行层                            │
│  ┌─────────────────────────────────────────────────┐    │
│  │  Orchestrator - 任务调度、并行执行、记忆集成     │    │
│  └─────────────────────────────────────────────────┘    │
│                              │                           │
│         ┌────────────────────┼────────────────────┐     │
│         ▼                    ▼                    ▼     │
│  ┌────────────┐      ┌────────────┐      ┌────────────┐│
│  │ CodingAgent│      │  TestAgent │      │ ReviewAgent││
│  └────────────┘      └────────────┘      └────────────┘│
│         │                    │                    │     │
│         ▼                    ▼                    ▼     │
│  ┌─────────────────────────────────────────────────┐    │
│  │           MemoryManager (3层记忆系统)            │    │
│  └─────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────┘
```

---

## 📦 核心组件

| 组件 | 导入 | 说明 |
|------|------|------|
| **UnifiedAdapter** | `SuperAgent.UnifiedAdapter` | 统一适配器（执行/审查/测试） |
| **ProjectGuide** | `SuperAgent.ProjectGuide` | 6 阶段项目引导器 |
| **NaturalLanguageParser** | `SuperAgent.NaturalLanguageParser` | 自然语言解析 |
| **AgentDispatcher** | `SuperAgent.AgentDispatcher` | Agent 分派 |
| **Orchestrator** | `SuperAgent.Orchestrator` | 任务编排调度 |
| **MemoryManager** | `SuperAgent.MemoryManager` | 3层记忆系统 |

---

## 🤖 Agent 类型

| AgentType | 说明 |
|-----------|------|
| `FULL_STACK_DEV` | 全栈开发 |
| `BACKEND_DEV` | 后端开发 |
| `FRONTEND_DEV` | 前端开发 |
| `CODE_REVIEW` | 代码审查 |
| `API_DESIGN` | API 设计与架构 |
| `QA_ENGINEERING` | 测试工程 |
| `DEVOPS` | DevOps |
| `PRODUCT_MANAGEMENT` | 产品管理 (v3.4) |
| `DATABASE_DESIGN` | 数据库设计 (v3.4) |

---

## 📡 HTTP REST API

启动服务: `python -m server.fastapi_app`

| 端点 | 方法 | 说明 |
|------|------|------|
| `/` | GET | 健康检查 |
| `/api/chat` | POST | 自然语言对话 |
| `/api/execute` | POST | 直接执行任务 |
| `/api/review` | POST | 代码审查 |
| `/api/test` | POST | 运行测试 |
| `/api/intent/recognize` | GET | 意图识别 |

---

## 📚 文档

- **[📖 完整用户指南](docs/guides/COMPLETE_USER_GUIDE_v3.2.md)** - 详细功能说明
- **[📋 发布说明](docs/RELEASE_NOTES_v3.4.md)** - v3.4 更新详情
- **[🛡️ 质量保证方案](docs/guides/QA_AND_REVIEW_SCHEME.md)** - 测试与审查
- **[🔧 开发指南](docs/guides/AGENT_DEVELOPMENT_GUIDE.md)** - 贡献代码

---

## 📊 测试结果

| 测试类型 | 通过率 | 测试数量 |
|----------|--------|----------|
| E2E 端到端测试 | 97.3% | 73 项 |
| 集成测试 | 92.5% | 40 项 |
| 自然语言解析 | 100% | 10 项 |

---

*SuperAgent v3.4 - 让 AI Agent 可被自然语言调用!* 🚀
