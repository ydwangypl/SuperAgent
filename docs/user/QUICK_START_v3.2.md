# 🚀 SuperAgent v3.4 快速入门指南

> **版本**: v3.4.0
> **更新日期**: 2026-01-28
> **适用对象**: 所有用户

---

## 🎯 核心定位

**SuperAgent 是一个 Python AI Agent 任务编排库**，用于管理 AI Agent 执行开发任务。

v3.4 引入了 **UnifiedAdapter (统一适配器)**，将复杂的编排逻辑简化为单一接口，极大降低了上手难度。

---

## 📦 快速使用

### 方式 1：UnifiedAdapter (推荐)

这是 v3.4 推荐的使用方式，只需几行代码即可执行、审查和测试。

```python
from SuperAgent import UnifiedAdapter
from pathlib import Path

# 初始化
adapter = UnifiedAdapter(project_root=Path("."))

# 执行任务
result = adapter.execute_task(
    task_type="coding",
    task_data={"description": "创建一个简单的 Flask 接口"}
)

print(f"执行结果: {result.success}")
```

### 方式 2：自然语言交互 (v3.4 新增)

支持直接输入自然语言，系统会自动识别意图并引导项目。

```python
from SuperAgent import NaturalLanguageParser, AgentDispatcher

# 解析需求
parser = NaturalLanguageParser()
request = parser.parse("帮我开发一个待办事项清单应用")

# 分派执行
dispatcher = AgentDispatcher()
result = await dispatcher.dispatch_async(request)
```

---

## 💻 进阶导入 (Advanced Imports)

如果你需要深度定制，可以直接从 `SuperAgent` 包导入核心组件：

```python
from SuperAgent import (
    Orchestrator,      # 核心编排器
    AgentType,         # Agent 类型枚举
    MemoryManager,     # 记忆管理系统
    HookManager,       # 生命周期钩子 (v3.3+)
    SessionManager     # 会话持久化 (v3.4+)
)
```

---

## 📂 项目结构

运行时数据（如 `tasks.json`）现已统一存储在 `.superagent/` 目录下。

更多细节请参考：
- [完整用户指南](COMPLETE_USER_GUIDE_v3.2.md)
- [开发者项目结构说明](../developer/PROJECT_STRUCTURE.md)


## ✅ 验证安装

运行以下命令验证安装：

```bash
cd E:\SuperAgent
python -c "
import sys
sys.path.insert(0, r'E:\\SuperAgent')
from orchestration.agent_factory import AgentFactory
from common.models import AgentType
from platform_adapters import PlatformDetector
print('SuperAgent 安装验证通过!')
"
```

---

## ✨ v3.3 新特性

v3.3 增加了以下新特性（100% 向后兼容）：

### 1. 生命周期钩子系统
```python
from extensions.hooks import HookManager

hook_manager = HookManager(memory_manager)
hook_manager.register_pre_execute("log_start", lambda ctx: print(f"开始: {ctx.phase}"))
hook_manager.register_post_execute("log_end", lambda ctx: print(f"完成: {ctx.phase}"))
```

### 2. 3-File 规划模式
```python
from extensions.planning_files import TaskPlanManager

plan_manager = TaskPlanManager(
    project_root=Path("."),
    plan_file=Path("task_plan.md"),
    auto_save=True
)
await plan_manager.create_plan(requirements, steps, dependencies)
```

### 3. 环境变量配置
```bash
export SUPERAGENT_LOG_LEVEL=DEBUG
export SUPERAGENT_REDIS_PASSWORD=your_password
export SUPERAGENT_MEMORY_ENABLED=true
```

### 4. 安全验证
```python
from security.validator import InputValidator, PathSanitizer

validator = InputValidator()
result = validator.validate_input(user_input)

sanitizer = PathSanitizer(base_path=Path("/safe"))
safe_path = sanitizer.sanitize(file_path)
```

### 5. 会话恢复机制
```python
from extensions.state_persistence import SessionManager

session_manager = SessionManager(project_root)
session_id = session_manager.start_session("my-task")
# ... 执行任务 ...
session_manager.end_session(session_id, "completed")
```

### 6. BaseAgent Findings 工具
```python
class MyAgent(BaseAgent):
    async def execute_task(self, task):
        await self.write_finding(
            title="重要发现",
            content="研究发现内容...",
            category="research"
        )
```

详见 [v3.3 发布说明](../RELEASE_NOTES_v3.3.md)

---

**版本**: v3.3.0
**更新**: 2026-01-25

**🚀 使用 SuperAgent 提升开发效率！**
