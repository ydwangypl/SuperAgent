# 🚀 SuperAgent v3.1 快速使用卡片

> **一页纸快速参考** - 常用命令和使用示例
>
> **v3.1 新特性**: ✨ 任务持久化 | ✨ 增量版本控制 | ✨ 单任务焦点模式

---

## 🎯 v3.1 核心新功能

### 1. TaskListManager - 任务持久化和断点续传

```python
from core.task_list_manager import TaskListManager

# 创建任务列表
manager = TaskListManager(project_root)
task_list = manager.create_from_plan(plan)

# 执行任务
task = manager.get_next_task()
manager.update_task(task.id, "running")
manager.update_task(task.id, "completed")

# 断点续传 - 程序中断后恢复
manager2 = TaskListManager(project_root)
loaded_list = manager2.load_or_create()
print(f"恢复进度: {loaded_list.completed}/{loaded_list.total_tasks}")
```

### 2. GitAutoCommitManager - 增量版本控制

```python
from orchestration.git_manager import GitAutoCommitManager

# 自动提交任务
await git_manager.commit_task(
    task_id="task-001",
    description="实现用户登录",
    changed_files=["login.py", "auth.py"]
)

# 提交 tasks.json 更新
await git_manager.commit_tasks_json()

# 查看提交历史
history = git_manager.get_commit_history(limit=10)
```

### 3. SingleTaskMode - 单任务焦点模式

```python
from orchestration.models import OrchestrationConfig, SingleTaskConfig

config = OrchestrationConfig(
    single_task_mode=SingleTaskConfig(
        enabled=True,
        max_files_per_task=5,
        enable_auto_split=True
    )
)

# 自动验证和拆分超出限制的任务
is_valid, reason = orchestrator._validate_task_scope(task)
if not is_valid:
    split_task = await orchestrator._split_task(task, reason)
```

---

## 📦 安装和设置

```bash
# 克隆仓库
git clone https://github.com/ydwangypl/SuperAgent.git
cd SuperAgent

# 检出版本
git checkout v3.1.0

# 安装依赖
pip install -r requirements.txt
pip install -r requirements-test.txt

# 配置环境变量
cp .env.template .env
# 编辑 .env 文件填入必要配置
```

---

## 🎯 快速开始

### 1. 代码生成和审查 (最常用)

```python
from pathlib import Path
from adapters import UnifiedAdapter

# 初始化
adapter = UnifiedAdapter(Path("/your/project"))

# 执行任务并自动审查
result = await adapter.execute_and_review(
    task_type="code",
    task_data={
        "description": "创建用户管理API",
        "requirements": ["RESTful", "JWT认证"]
    },
    review_config={
        "enable_iterative": True  # 启用循环改进
    }
)

# 查看结果
print(result['summary'])
```

### 2. 完整工作流程 (v3.1 增强)

```python
from pathlib import Path
from core.task_list_manager import TaskListManager
from orchestration.git_manager import GitAutoCommitManager
from orchestration.orchestrator import Orchestrator
from orchestration.models import OrchestrationConfig, SingleTaskConfig

# 1. 创建配置 (启用 v3.1 新功能)
config = OrchestrationConfig(
    single_task_mode=SingleTaskConfig(
        enabled=True,
        max_files_per_task=5,
        enable_auto_split=True
    ),
    git_auto_commit=GitAutoCommitConfig(
        enabled=True
    )
)

# 2. 初始化
project_root = Path("/path/to/project")
task_manager = TaskListManager(project_root)
git_manager = GitAutoCommitManager(project_root, enabled=True)
orchestrator = Orchestrator(project_root, config)

# 3. 创建并执行任务
task_list = task_manager.create_from_plan(plan)
task = task_manager.get_next_task()

# 执行...
task_manager.update_task(task.id, "completed")

# 4. 自动 Git commit
await git_manager.commit_task(
    task_id=task.id,
    description=task.description,
    changed_files=["file1.py"]
)
```

### 3. 内容生成 (v3.0 功能)

```python
# 文章生成
result = await adapter.execute_and_review(
    task_type="article",
    task_data={
        "description": "人工智能发展趋势",
        "context": {
            "tone": "professional",
            "length": 800,
            "audience": "技术从业者"
        }
    }
)
```

---

## 🔧 支持的任务类型

### 代码相关

| 类型 | 说明 | Agent类型 |
|------|------|----------|
| `code` | 通用代码生成 | BACKEND_DEV |
| `backend` | 后端代码 | BACKEND_DEV |
| `api` | API设计 | API_DESIGN |
| `frontend` | 前端代码 | FRONTEND_DEV |
| `fullstack` | 全栈代码 | FULL_STACK_DEV |
| `test` | 测试代码 | QA_ENGINEERING |
| `testing` | 测试代码 | QA_ENGINEERING |
| `refactor` | 代码重构 | CODE_REFACTORING |
| `database` | 数据库设计 | DATABASE_DESIGN |
| `documentation` | 技术文档 | TECHNICAL_WRITING |

### 内容相关 (✨ 新增)

| 类型 | 说明 |
|------|------|
| `article` | 文章生成 |
| `blog` | 博客生成 |
| `documentation` | 文档生成 |

---

## 📝 命令行使用

```bash
# 查看帮助
python superagent.py --help

# 交互模式
python superagent.py interactive

# 直接执行任务
python superagent.py run --type backend --description "创建用户API"

# 查看项目状态
python superagent.py status

# 查看记忆
python superagent.py memory --view

# 清理临时文件
python superagent.py clean
```

---

## 🧪 测试命令

```bash
# 运行所有测试
pytest

# 运行特定测试
pytest tests/test_core_executor.py -v

# 查看测试覆盖率
pytest --cov=. --cov-report=html

# 生成覆盖率报告
python scripts/testing/generate_coverage_report.py

# 运行集成测试
python scripts/testing/run_all_integration_tests.py
```

---

## 🧪 测试 v3.1 新功能

```bash
# 运行所有测试
pytest tests/ -v

# 运行 P0 核心功能测试
pytest tests/unit/test_task_list_manager.py -v
pytest tests/unit/test_git_manager.py -v
pytest tests/unit/test_single_task_mode.py -v

# 运行集成测试
pytest tests/integration/test_p0_integration.py -v

# 运行演示脚本
python examples/p0_demo_comprehensive.py
```

**测试结果**:
- ✅ 55/55 单元测试通过 (100%)
- ✅ 8/8 集成测试通过 (100%)
- ✅ 性能测试全部通过

---

## 📊 v3.0 vs v3.1 功能对比

| 功能 | v3.0 | v3.1 |
|------|------|------|
| 任务持久化 | ❌ | ✅ |
| 断点续传 | ❌ | ✅ |
| 自动 Git Commit | ❌ | ✅ |
| 任务范围验证 | ❌ | ✅ |
| 自动任务拆分 | ❌ | ✅ |
| 5层架构 | ✅ | ✅ |
| 3层记忆系统 | ✅ | ✅ |
| Ralph Wiggum | ✅ | ✅ |

---

## ⚙️ 配置选项

### v3.1 新配置

```python
from orchestration.models import OrchestrationConfig, SingleTaskConfig, GitAutoCommitConfig

config = OrchestrationConfig(
    # 单任务焦点模式 (v3.1 新增)
    single_task_mode=SingleTaskConfig(
        enabled=True,                      # 启用单任务模式
        max_files_per_task=5,              # 每个任务最多修改文件数
        max_file_size_kb=100,              # 单个文件最大大小
        enable_auto_split=True             # 自动拆分超出限制的任务
    ),
    # Git 自动提交 (v3.1 新增)
    git_auto_commit=GitAutoCommitConfig(
        enabled=True,                      # 启用自动提交
        commit_message_template="feat: {task_id} {description}",
        auto_push=False,                   # 是否自动推送
        auto_commit_tasks_json=True        # 自动提交 tasks.json
    )
)
```

### Ralph Wiggum 循环改进 (v3.0)

```python
review_config = {
    "enable_iterative": True,    # 启用循环改进
    "max_iterations": 3,         # 最大迭代次数
    "min_score": 70.0,          # 最低通过分数
    "target_score": 85.0        # 目标分数
}
```

### Agent 配置

```python
from execution.models import AgentConfig

config = AgentConfig(
    max_retries=3,
    timeout=300,
    enable_ralph_wiggum=True
)
```

---

## 📚 常用文档路径

```
docs/
├── USAGE_GUIDE.md                    # 完整使用指南
├── ARCHITECTURE_COMPARISON.md         # 架构对比
└── guides/
    ├── QUICKSTART.md                  # 快速开始
    ├── GLOBAL_SETUP_GUIDE.md          # 全局设置
    └── ralph_wiggum/                  # Ralph Wiggum专题
        ├── RALPH_WIGGUM_QUICK_REF.md
        └── RALPH_WIGGUM_USAGE.md
```

---

## 🔍 故障排查

### 问题: 导入错误

```bash
# 确保在项目根目录
cd /path/to/SuperAgent

# 检查Python路径
export PYTHONPATH="${PYTHONPATH}:$(pwd)"
```

### 问题: 测试失败

```bash
# 清理缓存
rm -rf .pytest_cache __pycache__

# 重新安装依赖
pip install -r requirements.txt --force-reinstall
```

### 问题: Git Worktree错误

```bash
# 清理worktree
git worktree prune

# 删除损坏的worktree
rm -rf .superagent/worktrees/*
```

---

## 🎯 最佳实践

### 1. 使用统一接口

```python
# ✅ 推荐
from adapters import UnifiedAdapter
adapter = UnifiedAdapter(project_path)
result = await adapter.execute_and_review(...)

# ❌ 不推荐 (虽然也可以)
from orchestration import Orchestrator
orchestrator = Orchestrator(...)
# ... 更复杂的代码
```

### 2. 提供详细上下文

```python
# ✅ 好的做法
task_data = {
    "description": "创建用户API",
    "context": {
        "language": "python",
        "framework": "FastAPI",
        "database": "PostgreSQL",
        "security": ["JWT", "OAuth2"]
    }
}

# ❌ 差的做法
task_data = {
    "description": "创建用户API"
}
```

### 3. 启用循环改进

```python
# ✅ 重要任务启用
review_config = {"enable_iterative": True}

# ✅ 快速原型禁用
review_config = {"enable_iterative": False}
```

---

## 📞 获取帮助

```bash
# 查看日志
tail -f logs/superagent.log

# 调试模式
export DEBUG=1
python superagent.py run ...

# 查看版本
python superagent.py --version
```

---

## 🎓 学习路径

1. **初学者**: [快速开始](docs/guides/QUICKSTART.md)
2. **进阶用户**: [使用指南](docs/USAGE_GUIDE.md)
3. **架构师**: [架构对比](docs/ARCHITECTURE_COMPARISON.md)
4. **开发者**: [重构进度](docs/reports/REFACTOR_PROGRESS_SUMMARY.md)

---

**💡 提示**: 将此文件加入浏览器书签,随时快速查阅!

---

**版本**: v3.1.0
**更新**: 2026-01-11
**项目**: https://github.com/ydwangypl/SuperAgent
