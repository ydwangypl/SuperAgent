# ⚡ SuperAgent 命令行速查卡

> **最常用命令** - 复制粘贴即可使用

---

## 🚀 快速开始

```bash
# 初始化项目
cd SuperAgent
pip install -r requirements.txt

# 运行测试
pytest

# 查看帮助
python superagent.py --help
```

---

## 📝 核心命令

### 任务执行

```bash
# 代码生成
python superagent.py run --type backend --description "创建用户API"

# 交互模式
python superagent.py interactive

# 查看状态
python superagent.py status
```

### 测试命令

```bash
# 所有测试
pytest

# 特定测试文件
pytest tests/test_core_executor.py -v

# 测试覆盖率
pytest --cov=. --cov-report=html

# 集成测试
python scripts/testing/run_all_integration_tests.py
```

### 记忆管理

```bash
# 查看记忆
python superagent.py memory --view

# 清理记忆
python superagent.py memory --clear

# 导出记忆
python superagent.py memory --export memory.json
```

### Git Worktree

```bash
# 清理worktree
git worktree prune

# 列出worktree
git worktree list

# 删除worktree
git worktree remove <path>
```

---

## 🔧 高级用法

### 环境变量

```bash
# 设置调试模式
export DEBUG=1

# 设置日志级别
export LOG_LEVEL=DEBUG

# 设置API密钥
export ANTHROPIC_API_KEY="your-key"
```

### Python脚本

```python
# 基本使用
from adapters import UnifiedAdapter
from pathlib import Path

adapter = UnifiedAdapter(Path("/project"))
result = await adapter.execute_and_review(
    task_type="code",
    task_data={"description": "创建用户API"}
)
```

---

## 📊 常用路径

```
配置: config/settings.py
日志: logs/superagent.log
记忆: .superagent/memory/
测试: tests/
文档: docs/
```

---

## 🆘 故障排查

```bash
# 清理缓存
rm -rf .pytest_cache __pycache__

# 重新安装
pip install -r requirements.txt --force-reinstall

# 查看日志
tail -f logs/superagent.log
```

---

**保存为书签,随时查阅!** 📌
