# SuperAgent 审查与测试方案 (v3.2)

> **目标**: 确保在快速迭代中, 系统的每一个组件和整体流程都能稳定、高效地运行。

---

## 📋 方案概览

本方案由四个核心支柱组成：
1. **多层级自动化测试 (Multi-level Testing)**：建立从单元到集成的多维防线。
2. **代码质量静态审查 (Static Analysis)**：强制代码风格一致性与类型安全。
3. **快速验证机制 (Quick Verification)**：提供 `--fast` 与 `--full` 两种验证级别。
4. **人工审查与冒烟测试 (Manual Review)**：整合核心业务链路的 Checklist。

---

## 🎯 质量指标 (Quality Metrics)

为了量化评估代码质量，我们设定以下基准要求：

| 指标类型 | 衡量项 | 目标值 | 备注 |
| :--- | :--- | :--- | :--- |
| **覆盖率** | 单元测试覆盖率 | ≥ 80% | 核心逻辑必须 100% 覆盖 |
| **覆盖率** | 集成测试覆盖率 | ≥ 60% | 覆盖主要业务链路 |
| **代码质量** | 圈复杂度 (Cyclomatic Complexity) | < 10 | 超过 15 必须重构 |
| **代码质量** | Lint 错误/警告 | 0 | 严格遵循 Flake8 标准 |
| **自动化** | CI/CD 通过率 | 100% | 阻塞 PR 合并的必要条件 |

---

## 1. 多层级自动化测试

### 1.1 单元测试 (Unit Tests) - 第一道防线
- **范围**: `tests/unit/`
- **频率**: 每次修改代码后立即运行。
- **重点**:
    - `memory_manager.py`: 3层记忆的存取逻辑。
    - `orchestrator.py`: 任务分发与状态流转。
    - `planner.py`: 任务分解的准确性。
- **命令**: `pytest tests/unit/`

### 1.2 集成测试 (Integration Tests) - 第二道防线
- **范围**: `tests/integration/`
- **频率**: 提交代码前。
- **重点**:
    - `Orchestrator` + `MemoryManager` 的协作。
    - `TaskListManager` 的持久化与恢复。
    - `GitAutoCommitManager` 的版本控制集成。
- **命令**: `pytest tests/integration/`

### 1.3 性能测试 (Performance Tests) - *可选 (YAGNI)*
- **注意**: 仅在系统进入稳定期或出现明确性能瓶颈时引入。
- **范围**: `tests/performance/`

---

## 2. 代码质量静态审查

### 2.1 风格审查 (Linting)
- **工具**: `flake8`
- **要求**: 无错误 (Zero Errors), 无警告 (Zero Warnings)。
- **配置**: `--max-line-length=100`

### 2.2 类型检查 (Type Checking)
- **工具**: `mypy`
- **要求**: 核心模块 (`orchestration/`, `planning/`) 必须通过检查。

---

## 3. 快速验证机制 (The "Verify" Script)

使用 `scripts/verify_system.py` 统一入口。

### 3.1 运行模式 (Modes)
- **`--mode fast` (快速模式)**: 
    - 运行核心冒烟测试 + 代码风格检查 (约 30s)。
    - 适用场景：开发中频繁自测。
- **`--mode full` (全量模式)**: 
    - 运行所有单元测试 + 集成测试 + 覆盖率检查 + 静态分析 (约 5min+)。
    - 适用场景：提交 PR 前、发布版本前。

---

## 4. 人工审查 Checklist

在合并代码前，建议通过以下流程确认核心链路：

### 4.1 核心业务链路自测
- **任务规划**: `sa "创建一个简单项目"` 能否正确拆解任务？
- **任务持久化**: `sa --resume` 能否在中断后正确恢复？
- **版本管理**: 每个任务完成后是否生成了 Git Commit？
- **记忆系统**: `.superagent/memory/` 下是否正确更新了 JSON 记录？

### 4.2 错误处理审查
- 异常捕获是否包含详细日志？
- 关键失败点是否支持重试或优雅退出？

---

## 🚀 质量守卫流程 (Quality Gate)

1. **本地开发**: 运行 `python scripts/verify_system.py --mode fast`。
2. **代码提交**: 运行 `python scripts/verify_system.py --mode full` 确认覆盖率达标。
3. **CI 集成**: GitHub Actions 自动运行全量验证，失败则禁止合并。

---

**版本**: v3.2.0
**最后更新**: 2026-01-14
**维护者**: SuperAgent QA Team
