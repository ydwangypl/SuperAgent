# SuperAgent 审查与测试方案 (v3.3)

> **目标**: 确保在快速迭代中, 系统的每一个组件和整体流程都能稳定、高效地运行。
> **v3.3 新增**: 双轨质量保障系统 (方案A主工作流 + 方案B独立API)

---

## 📋 方案概览

本方案由五个核心支柱组成：

1. **多层级自动化测试 (Multi-level Testing)**：建立从单元到集成的多维防线。
2. **代码质量静态审查 (Static Analysis)**：强制代码风格一致性与类型安全。
3. **双轨质量保障 (Dual-Mode QA)**：方案A(主工作流) + 方案B(独立API)。
4. **快速验证机制 (Quick Verification)**：提供 `--fast` 与 `--full` 两种验证级别。
5. **人工审查与冒烟测试 (Manual Review)**：整合核心业务链路的 Checklist。

---

## 🎯 质量指标 (Quality Metrics)

为了量化评估代码质量，我们设定以下基准要求：

| 指标类型 | 衡量项 | 目标值 | 备注 |
| :--- | :--- | :--- | :--- |
| **覆盖率** | 单元测试覆盖率 | ≥ 80% | 核心逻辑必须 100% 覆盖 |
| **覆盖率** | 集成测试覆盖率 | ≥ 60% | 覆盖主要业务链路 |
| **覆盖率** | 质量保障测试覆盖率 | 100% | 双轨 QA 功能测试 |
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

## 3. 双轨质量保障系统 (Dual-Mode QA) - v3.3 新增

SuperAgent v3.3 引入了创新的双轨质量保障系统，提供两种测试执行方式。

### 方案A：主工作流集成 (Main Workflow Integration)

**核心价值**: 执行完成后自动运行代码审查和测试。

**工作流程**:
```
execute → code_review → test (自动)
```

**配置方式**:
```python
from SuperAgent import Orchestrator, OrchestrationConfig, TestingConfig

# 启用自动测试
config = OrchestrationConfig()
config.testing.enabled = True
config.testing.test_path = "tests"
config.testing.timeout = 300

orchestrator = Orchestrator(Path("."), config=config)
```

**TestingConfig 配置**:
```python
from SuperAgent import TestingConfig

config = TestingConfig(
    enabled=True,              # 启用测试
    test_path="tests",         # 测试路径
    fail_on_failure=False,     # 失败时是否中断
    coverage=False,            # 是否生成覆盖率
    markers=None,              # pytest markers
    verbose=True,              # 详细输出
    timeout=300                # 超时时间(秒)
)
```

### 方案B：独立API (Independent API)

**核心价值**: 提供独立的测试执行接口，支持同步/异步调用。

**使用方式 1: UnifiedAdapter**
```python
from SuperAgent import UnifiedAdapter

unified = UnifiedAdapter(project_root=Path("."))

# 独立测试执行
result = unified.run_tests_sync(test_path="tests/")

# 完整工作流: execute + review + test
result = await unified.execute_and_review_and_test(
    task_type="coding",
    task_data={"task": "实现功能"},
    review_config={"verbose": True},
    test_config={"test_path": "tests/"}
)
```

**使用方式 2: 独立 TestAdapter**
```python
from SuperAgent import TestAdapter

adapter = TestAdapter(project_root=Path("."))

# 同步执行
result = adapter.run_tests_sync(test_path="tests/")

# 异步执行
result = await adapter.run_tests(test_path="tests/")

# 快速测试
result = await adapter.run_quick_tests()

# 指定模块测试
result = await adapter.run_unit_tests("core")

# 集成测试
result = await adapter.run_integration_tests()
```

### 测试结果结构

**TestResult (方案A)**:
```python
@dataclass
class TestResult:
    success: bool
    total_tests: int = 0
    passed: int = 0
    failed: int = 0
    errors: int = 0
    skipped: int = 0
    duration_seconds: float = 0.0
    output: str = ""
    coverage: Optional[float] = None
    failed_tests: List[str] = field(default_factory=list)
    error_tests: List[str] = field(default_factory=list)
```

**Dict (方案B)**:
```python
{
    "status": "completed",      # "completed" | "error" | "timeout"
    "success": True,
    "total_tests": 10,
    "passed": 10,
    "failed": 0,
    "errors": 0,
    "skipped": 0,
    "duration_seconds": 1.5,
    "coverage": 85.0,
    "failed_tests": []
}
```

### 测试命令
```bash
# 运行双轨质量保障测试
pytest tests/test_dual_mode_qa.py -v      # 单元测试
pytest tests/test_dual_mode_e2e.py -v     # 端到端测试

# 运行所有测试
pytest tests/test_dual_mode_qa.py tests/test_dual_mode_e2e.py -v
```

---

## 4. 快速验证机制 (The "Verify" Script)

使用 `scripts/verify_system.py` 统一入口。

### 4.1 运行模式 (Modes)
- **`--mode fast` (快速模式)**:
    - 运行核心冒烟测试 + 代码风格检查 (约 30s)。
    - 适用场景：开发中频繁自测。
- **`--mode full` (全量模式)**:
    - 运行所有单元测试 + 集成测试 + 覆盖率检查 + 静态分析 (约 5min+)。
    - 适用场景：提交 PR 前、发布版本前。

---

## 5. 人工审查 Checklist

在合并代码前，建议通过以下流程确认核心链路：

### 5.1 核心业务链路自测
- **任务规划**: `sa "创建一个简单项目"` 能否正确拆解任务？
- **任务持久化**: `sa --resume` 能否在中断后正确恢复？
- **版本管理**: 每个任务完成后是否生成了 Git Commit？
- **记忆系统**: `.superagent/memory/` 下是否正确更新了 JSON 记录？

### 5.2 质量保障自测 (v3.3)
- **方案A**: 启用 testing 后，Orchestrator 执行是否自动运行测试？
- **方案B**: TestAdapter 独立调用是否能正确返回测试结果？
- **双轨验证**: 两种方案返回的测试结果是否一致？

### 5.3 错误处理审查
- 异常捕获是否包含详细日志？
- 关键失败点是否支持重试或优雅退出？

---

## 🚀 质量守卫流程 (Quality Gate)

1. **本地开发**: 运行 `python scripts/verify_system.py --mode fast`。
2. **代码提交**: 运行 `python scripts/verify_system.py --mode full` 确认覆盖率达标。
3. **CI 集成**: GitHub Actions 自动运行全量验证，失败则禁止合并。
4. **质量保障验证**:
   - 方案A: `pytest tests/test_dual_mode_qa.py -v`
   - 方案B: `pytest tests/test_dual_mode_e2e.py -v`

---

## 测试覆盖统计

| 测试套件 | 测试数量 | 通过 | 失败 | 通过率 |
|---------|---------|------|------|--------|
| 单元测试 | 10 | 10 | 0 | 100% |
| 生命周期钩子 | 5 | 5 | 0 | 100% |
| 规划文件管理 | 6 | 6 | 0 | 100% |
| 安全验证 | 4 | 4 | 0 | 100% |
| 会话恢复 | 1 | 1 | 0 | 100% |
| BaseAgent 扩展 | 1 | 1 | 0 | 100% |
| 端到端测试 | 7 | 7 | 0 | 100% |
| 双轨质量保障 | 22 | 22 | 0 | 100% |
| **总计** | **56+** | **56+** | **0** | **100%** |

---

**版本**: v3.3.0
**最后更新**: 2026-01-26
**维护者**: SuperAgent QA Team

**核心特性**:
- ✅ 方案A: 主工作流集成 (Orchestrator 自动测试)
- ✅ 方案B: 独立API (TestAdapter / UnifiedAdapter)
- ✅ 同步/异步接口
- ✅ pytest 集成
- ✅ 配置化测试执行
- ✅ 测试结果解析
- ✅ 覆盖率报告支持
