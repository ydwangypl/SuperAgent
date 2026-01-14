# 💻 VS Code 使用提示

## 🎯 SuperAgent v3.2 开发提示

### 推荐扩展

```json
{
  "recommendations": [
    "ms-python.python",
    "ms-python.pylint",
    "ms-python.vscode-pylance",
    "littlefoxteam.vscode-python-test-adapter",
    "github.copilot"
  ]
}
```

### 常用操作

#### 运行测试

- **F5**: 调试当前Python文件
- **Ctrl+Shift+F5**: 运行所有测试
- **Ctrl+F5**: 运行当前文件

#### 查看文档

- **Ctrl+点击**: 跳转到定义
- **F12**: 转到定义
- **Shift+F12**: 查找引用

#### Git操作

- **Ctrl+Shift+G**: 打开Git视图
- **Ctrl+Enter**: 提交消息
- **Alt+Shift+R**: 重新定基

---

### 📁 关键文件快速导航

```
Ctrl+P 然后输入:

> core          # 核心抽象层
> adapters      # 适配器层
> extensions    # 扩展层
> executor      # 执行器
> reviewer      # 审查器
> test          # 测试文件
> config        # 配置文件
```

---

### 🔍 代码片段

#### 创建新Executor

```python
# executor-snippet
from core.executor import Executor, Task, ExecutionResult, TaskStatus

class MyExecutor(Executor):
    def __init__(self, name: str = "MyExecutor"):
        super().__init__(name)
        self.supported_types = ["my_type"]

    def execute(self, task: Task) -> ExecutionResult:
        # 实现执行逻辑
        return ExecutionResult(
            success=True,
            content="result",
            status=TaskStatus.COMPLETED
        )
```

#### 创建新Reviewer

```python
# reviewer-snippet
from core.reviewer import Reviewer, Artifact, ReviewResult, ReviewStatus

class MyReviewer(Reviewer):
    def __init__(self, name: str = "MyReviewer"):
        super().__init__(name)
        self.supported_types = ["my_type"]

    def review(self, artifact: Artifact) -> ReviewResult:
        # 实现审查逻辑
        return ReviewResult(
            status=ReviewStatus.APPROVED,
            overall_score=85.0,
            approved=True
        )
```

---

### ⚙️ 调试配置

创建 `.vscode/launch.json`:

```json
{
  "version": "0.2.0",
  "configurations": [
    {
      "name": "测试SuperAgent",
      "type": "python",
      "request": "launch",
      "module": "pytest",
      "args": ["tests/test_core_executor.py::TestTask::test_task_creation", "-v"],
      "console": "integratedTerminal",
      "justMyCode": false
    },
    {
      "name": "运行SuperAgent",
      "type": "python",
      "request": "launch",
      "program": "superagent.py",
      "args": ["--help"],
      "console": "integratedTerminal"
    }
  ]
}
```

---

### 🧪 测试提示

#### 快速运行特定测试

1. 打开测试文件
2. 点击测试方法左侧的运行按钮
3. 或者右键选择"运行测试"

#### 查看测试覆盖率

```bash
# 在终端运行
pytest --cov=. --cov-report=html

# 然后在浏览器打开
htmlcov/index.html
```

---

### 📊 任务面板

创建 `.vscode/tasks.json`:

```json
{
  "version": "2.0.0",
  "tasks": [
    {
      "label": "运行所有测试",
      "type": "shell",
      "command": "pytest",
      "group": {
        "kind": "test",
        "isDefault": true
      }
    },
    {
      "label": "测试覆盖率",
      "type": "shell",
      "command": "pytest --cov=. --cov-report=html"
    },
    {
      "label": "清理缓存",
      "type": "shell",
      "command": "rm -rf .pytest_cache __pycache__"
    }
  ]
}
```

使用: **Ctrl+Shift+P** → "Tasks: Run Task"

---

### 🎨 推荐设置

```json
{
  "python.linting.enabled": true,
  "python.linting.pylintEnabled": true,
  "python.formatting.provider": "black",
  "editor.formatOnSave": true,
  "python.testing.pytestEnabled": true,
  "python.testing.pytestArgs": ["-v"],
  "files.exclude": {
    "**/__pycache__": true,
    "**/.pytest_cache": true,
    "**/.tmp": true
  }
}
```

---

### 🚀 键盘快捷键

| 操作 | 快捷键 | 说明 |
|------|--------|------|
| 运行测试 | `Ctrl+Shift+F5` | 运行所有测试 |
| 调试 | `F5` | 启动调试 |
| 命令面板 | `Ctrl+Shift+P` | 打开命令面板 |
| 快速打开 | `Ctrl+P` | 快速打开文件 |
| 终端 | `Ctrl+`` | 切换终端 |
| Git | `Ctrl+Shift+G` | 打开Git视图 |
| 测试 | `Ctrl+Shift+T` | 打开测试视图 |

---

### 💡 提示

1. **使用工作区**: 将SuperAgent作为工作区打开,而非单个文件夹
2. **启用自动保存**: 设置 `files.autoSave = "afterDelay"`
3. **使用Git Lens**: 安装Git Lens扩展获得更好的Git体验
4. **配置Python解释器**: 选择正确的虚拟环境

---

**🎯 更多提示**: 查看 [QUICK_REFERENCE.md](../../QUICK_REFERENCE.md)
