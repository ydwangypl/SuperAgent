# 🚀 SuperAgent v3.0 快速使用卡片

> **一页纸快速参考** - 常用命令和使用示例

---

## 📦 安装和设置

```bash
# 克隆仓库
git clone https://github.com/ydwangypl/SuperAgent.git
cd SuperAgent

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

### 2. 内容生成 (新功能 ✨)

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

## ⚙️ 配置选项

### Ralph Wiggum 循环改进

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

**版本**: v3.0.0
**更新**: 2026-01-11
**项目**: https://github.com/ydwangypl/SuperAgent
