# SuperAgent 测试套件指南

## 🏗️ 测试目录结构

测试文件已按照功能和类型进行了重新组织：

- **[unit/](unit/)**: 单元测试。针对单个模块或类的功能验证。
- **[integration/](integration/)**: 集成测试。验证多个模块之间的协作流程。
- **[performance/](performance/)**: 性能测试。基准测试和压力测试。
- **[security/](security/)**: 安全测试。漏洞扫描和权限验证。

## 🚀 运行测试

### 运行所有测试

使用根目录下的 `run_all_tests.bat` 或直接使用 pytest：

```bash
python -m pytest tests/
```

### 运行特定类别的测试

```bash
# 仅运行单元测试
python -m pytest tests/unit/

# 仅运行集成测试
python -m pytest tests/integration/
```

### 运行单个测试文件

```bash
python -m pytest tests/unit/test_planning.py -v
```

## 🛠️ 测试辅助工具

- **[helpers.py](helpers.py)**: 包含 Mock 对象和通用的测试辅助类（如 `MockAgent`, `TestProjectHelper`）。
- **[performance_baseline.json](performance_baseline.json)**: 存储性能测试的基准数据。

## 📊 覆盖率报告

运行以下命令生成 HTML 覆盖率报告：

```bash
python scripts/testing/generate_coverage_report.py
```

报告将生成在 `htmlcov/` 目录下。

---
*保持测试通过是合并代码的前提。当前状态: 68/68 Pass.*
