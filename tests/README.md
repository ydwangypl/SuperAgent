# SuperAgent v3.1 测试指南

## 快速开始

### 运行所有测试

```bash
python run_v3_tests.py
```

### 运行单个测试文件

```bash
# CLI测试
python -m pytest tests/test_cli.py -v

# 对话管理测试
python -m pytest tests/test_conversation.py -v

# 规划层测试
python -m pytest tests/test_planning.py -v

# 集成测试
python -m pytest tests/test_integration.py -v
```

### 运行特定测试

```bash
# 运行单个测试
python -m pytest tests/test_planning.py::TestStepGenerator::test_step_dependencies -v

# 运行包含特定关键词的测试
python -m pytest tests/ -k "test_do_cd" -v
```

## 测试结构

```
tests/
├── test_cli.py              # CLI层单元测试 (14个)
├── test_conversation.py     # 对话管理层单元测试 (13个)
├── test_planning.py         # 规划层单元测试 (18个)
├── test_integration.py      # 集成测试 (10个)
└── README.md               # 本文档
```

## 测试覆盖

### CLI层 (test_cli.py)

- 命令初始化与配置
- 命令执行 (status, help, pwd, cd, ls, clear, quit, exit)
- 自然语言输入处理
- 用户交互验证

### 对话管理层 (test_conversation.py)

- 意图识别 (NEW_PROJECT, QUERY, FIX_BUG, ADD_FEATURE, UNKNOWN)
- 需求明确性判断
- 澄清问题生成
- 对话历史管理
- 上下文传递

### 规划层 (test_planning.py)

- **TestProjectPlanner**: 计划生成、格式化
- **TestStepGenerator**: 步骤生成、依赖关系、并行标识、时间估算
- **TestDependencyAnalyzer**: 依赖图构建、执行顺序、关键路径
- **TestDataModels**: 数据模型创建与验证

### 集成测试 (test_integration.py)

- **TestFullIntegration**: 端到端流程验证
- **TestErrorHandling**: 边界情况处理
- **TestPerformance**: 性能基准验证

## 性能基准

| 操作 | 目标 | 当前 |
|------|------|------|
| 对话处理 | <100ms | ~50ms |
| 规划生成 | <200ms | ~150ms |
| 完整测试套件 | <1s | 0.356s |

## 调试测试

### 启用详细输出

```bash
python run_v3_tests.py -v
```

### 显示print输出

```bash
python -m pytest tests/test_planning.py::TestStepGenerator::test_step_dependencies -v -s
```

### 进入调试器

```bash
python -m pytest tests/test_planning.py::TestStepGenerator::test_step_dependencies --pdb
```

## 已知问题

### 1. Windows平台UTF-8编码

**问题**: 中文输出乱码
**解决**: 已在 `cli/main.py` 中添加UTF-8支持

### 2. 临时目录清理

**问题**: Windows平台 `TemporaryDirectory()` 递归错误
**解决**: 使用系统临时目录而非创建新目录

### 3. Async函数警告

**问题**: RuntimeWarning: coroutine was never awaited
**影响**: 不影响测试结果
**状态**: 可忽略

## 贡献指南

### 添加新测试

1. 在对应的测试文件中创建新测试方法
2. 使用清晰的命名: `test_<功能>_<场景>`
3. 添加docstring说明测试目的
4. 遵循AAA模式: Arrange, Act, Assert

```python
def test_example_feature(self):
    """测试示例功能"""
    # Arrange - 准备测试数据
    input_data = "test input"

    # Act - 执行被测功能
    result = process(input_data)

    # Assert - 验证结果
    self.assertEqual(result, "expected output")
```

### 测试命名规范

- 测试类: `Test<ModuleName>`
- 测试方法: `test_<function>_<scenario>`

### Mock使用

```python
from unittest.mock import patch, MagicMock

# Mock函数调用
with patch('module.function') as mock_func:
    mock_func.return_value = "mocked value"
    # 执行测试
```

## 测试最佳实践

1. **独立性**: 每个测试应该独立运行
2. **可读性**: 使用清晰的命名和注释
3. **速度**: 测试应该快速执行
4. **覆盖**: 测试正常流程和边界情况
5. **Mock**: 隔离外部依赖

## 相关文档

- [PHASE1_COMPLETION_REPORT.md](../PHASE1_COMPLETION_REPORT.md) - Phase 1完成报告
- [PHASE1.4_COMPLETION_REPORT.md](../PHASE1.4_COMPLETION_REPORT.md) - Phase 1.4完成报告
- [SUPERAGENT_V3.0_DESIGN.md](../SUPERAGENT_V3.0_DESIGN.md) - 设计文档

---

最后更新: 2025-01-08
