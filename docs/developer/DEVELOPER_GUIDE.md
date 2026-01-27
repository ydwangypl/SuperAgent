# SuperAgent 开发者指南

本文档旨在为开发者提供 SuperAgent v3.4 的核心组件 API 说明及扩展指南。

## 1. 统一适配器 (UnifiedAdapter) - v3.4 推荐

`UnifiedAdapter` 是 v3.4 引入的简化接口，封装了复杂的编排逻辑。

```python
from SuperAgent import UnifiedAdapter
adapter = UnifiedAdapter(project_root=Path("."))
```

---

## 2. 扩展模块化 (Extensions)

在 v3.4 中，`extensions/` 目录进行了模块化重构。

### 2.1 目录结构
- `extensions/executors/`: 存放自定义执行器（如 `WritingExecutor`）。
- `extensions/reviewers/`: 存放自定义审查器（如 `ContentReviewer`）。
- `extensions/hooks/`: 存放生命周期钩子（如 `ReReadPlanHook`）。
- `extensions/state_persistence/`: 存放会话状态管理（`SessionManager`）。

### 2.2 注册自定义扩展
所有扩展必须在 `orchestration/registry.py` 中注册才能被 `AgentFactory` 识别。

---

## 3. 安全验证 (SecurityValidator)

`SecurityValidator` 位于 `common/security.py`，是系统安全的第一道防线。

### 核心方法

#### `validate_path(path: Path, base_dir: Path) -> Path`
验证路径是否在允许的基础目录内，防止路径穿越攻击。

**示例:**
```python
from pathlib import Path
from common.security import SecurityValidator

base = Path("/app/project")
safe_path = SecurityValidator.validate_path(Path("src/main.py"), base)
```

#### `sanitize_input(text: str) -> str`
清理用户输入，移除危险字符和潜在的脚本注入。

#### `validate_git_ref(ref: str) -> str`
验证 Git 分支或标签名称是否符合安全规范。

---

## 2. 编排器扩展 (BaseOrchestrator)

编排器是 SuperAgent 的控制中枢。所有新的编排器都应继承自 `BaseOrchestrator`。

### 扩展步骤

1. **继承基类**: `from orchestration.base import BaseOrchestrator`
2. **初始化**: 调用 `super().__init__(project_root, config)`。
3. **实现逻辑**: 在子类中定义业务逻辑方法。

### 示例代码

```python
from orchestration.base import BaseOrchestrator
from pathlib import Path

class MyOrchestrator(BaseOrchestrator):
    def __init__(self, project_root: Path, config=None):
        super().__init__(project_root, config)
        # 初始化自定义工具
        
    async def execute(self, task: str):
        print(f"正在执行任务: {task} 在项目 {self.project_root}")
```

---

## 3. 记忆系统 (MemoryManager)

`MemoryManager` 负责管理长期和短期记忆。

### 初始化建议
在 v3.2 中，`MemoryManager` 支持无参初始化，默认使用当前工作目录。

```python
from memory.memory_manager import MemoryManager
mm = MemoryManager() # 自动识别项目根目录
```

---

## 4. 最佳实践

- **异步优先**: 所有的核心执行逻辑应使用 `async/await`。
- **类型注解**: 所有的 API 必须包含完整的 Python 类型注解。
- **错误处理**: 使用 `common.exceptions` 中定义的异常类。
