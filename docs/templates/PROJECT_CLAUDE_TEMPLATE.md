# CLAUDE.md - SuperAgent Context
# 复制此文件到你的项目根目录，AI 会自动加载

# SuperAgent 是一个 Python AI Agent 任务编排库

## 使用方法

当用户要求使用 SuperAgent 时，按以下方式导入：

### 方式1：推荐（简洁）
```python
from SuperAgent import Orchestrator, AgentFactory, AgentType

orchestrator = Orchestrator(Path("."))
agent = AgentFactory().create_agent(AgentType.FULL_STACK_DEV, "MyAgent")
```

### 方式2：详细（自定义配置）
```python
import sys
sys.path.insert(0, r'E:\SuperAgent')

from pathlib import Path
from orchestration.orchestrator import Orchestrator
from orchestration.models import OrchestrationConfig
from common.models import AgentType

orchestrator = Orchestrator(
    project_root=Path("."),
    config=OrchestrationConfig()
)
```

## 常用导入

```python
# 简洁导入（推荐）
from SuperAgent import Orchestrator, AgentFactory, AgentType, BaseAgent

# 详细导入
from orchestration.orchestrator import Orchestrator
from orchestration.agent_factory import AgentFactory
from common.models import AgentType
from execution.base_agent import BaseAgent
from core.task_list_manager import TaskListManager
```

## Agent 类型

- `AgentType.FULL_STACK_DEV` - 全栈开发
- `AgentType.BACKEND_DEV` - 后端开发
- `AgentType.FRONTEND_DEV` - 前端开发
- `AgentType.CODE_REVIEW` - 代码审查
- `AgentType.API_DESIGN` - API 设计
- `AgentType.QA_ENGINEERING` - 测试工程
- `AgentType.DEVOPS` - DevOps
