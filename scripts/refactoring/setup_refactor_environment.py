#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
重构环境准备脚本

一键准备重构所需的环境和工具。
"""

import subprocess
import sys
from pathlib import Path


def create_git_branches():
    """创建重构分支"""

    print("=" * 70)
    print("创建 Git 分支")
    print("=" * 70)

    commands = [
        # 创建主重构分支
        ["git", "checkout", "-b", "refactor/architecture-refactor"],

        # 创建阶段分支
        ["git", "checkout", "-b", "refactor/step-1-abstract-layer"],
        ["git", "checkout", "-b", "refactor/step-2-migration"],
        ["git", "checkout", "-b", "refactor/step-3-extension"],
        ["git", "checkout", "-b", "refactor/step-4-cleanup"],
    ]

    for cmd in commands:
        try:
            subprocess.run(cmd, check=True, capture_output=True)
            branch_name = cmd[2]
            print(f"[OK] 创建分支: {branch_name}")
        except subprocess.CalledProcessError as e:
            print(f"[WARNING] 分支可能已存在: {cmd[2]}")

    # 切回主重构分支
    subprocess.run(["git", "checkout", "refactor/architecture-refactor"],
                   capture_output=True)
    print(f"\n[OK] 当前分支: refactor/architecture-refactor")
    print()


def create_refactor_scripts():
    """创建重构辅助脚本"""

    print("=" * 70)
    print("创建重构辅助脚本")
    print("=" * 70)

    # 1. 运行所有测试脚本
    script1 = Path("scripts/run_all_tests.bat")
    script1.parent.mkdir(exist_ok=True)
    script1.write_text("""@echo off
echo ========================================
echo 运行所有测试
echo ========================================
echo.

echo [1/4] 单元测试
pytest tests/ -v -k "not integration"

echo.
echo [2/4] 集成测试
pytest tests/test_*.py -v -k "integration"

echo.
echo [3/4] 性能测试
python tests/test_performance.py

echo.
echo [4/4] 生成覆盖率报告
python generate_coverage_report.py

echo.
echo ========================================
echo 所有测试完成!
echo ========================================
pause
""", encoding='utf-8')
    print(f"[OK] 创建: {script1}")

    # 2. 重构前检查脚本
    script2 = Path("scripts/pre_refactor_check.bat")
    script2.write_text("""@echo off
echo ========================================
echo 重构前检查
echo ========================================
echo.

echo [1/3] 运行所有测试
call scripts\\run_all_tests.bat

echo.
echo [2/3] 检查覆盖率
python generate_coverage_report.py

echo.
echo [3/3] 运行性能测试
python tests/test_performance.py

echo.
echo ========================================
echo 重构前检查完成!
echo ========================================
echo.
echo 如果所有测试通过,可以开始重构。
echo.
pause
""", encoding='utf-8')
    print(f"[OK] 创建: {script2}")

    # 3. 重构后验证脚本
    script3 = Path("scripts/post_refactor_check.bat")
    script3.write_text("""@echo off
echo ========================================
echo 重构后验证
echo ========================================
echo.

echo [1/4] 运行所有测试
call scripts\\run_all_tests.bat

echo.
echo [2/4] 性能对比
echo 重构前基准 vs 当前性能
python tests/test_performance.py

echo.
echo [3/4] 覆盖率检查
python generate_coverage_report.py

echo.
echo [4/4] 集成测试
python run_all_integration_tests.py

echo.
echo ========================================
echo 重构后验证完成!
echo ========================================
pause
""", encoding='utf-8')
    print(f"[OK] 创建: {script3}")

    print()


def create_checklist():
    """创建重构检查清单"""

    print("=" * 70)
    print("创建重构检查清单")
    print("=" * 70)

    checklist = """# SuperAgent 重构检查清单

## 重构前检查

### 测试
- [ ] 所有单元测试通过
- [ ] 所有集成测试通过
- [ ] 性能基准测试完成
- [ ] 覆盖率报告已生成

### 文档
- [ ] 重构设计文档已审核
- [ ] 实施计划已确认
- [ ] 风险已评估

### 环境
- [ ] Git 分支已创建
- [ ] 开发环境已配置
- [ ] 测试工具已准备

## 重构阶段检查

### 第 1 阶段: 抽象层建立
- [ ] core/executor.py 已创建
- [ ] core/reviewer.py 已创建
- [ ] 单元测试已编写
- [ ] 测试通过

### 第 2 阶段: 代码迁移
- [ ] CodeExecutor 已迁移
- [ ] CodeReviewer 已迁移
- [ ] Orchestrator 已更新
- [ ] 所有测试通过
- [ ] 向后兼容

### 第 3 阶段: 扩展验证
- [ ] WritingExecutor 已实现
- [ ] ContentReviewer 已实现
- [ ] 集成测试通过
- [ ] 功能验证成功

### 第 4 阶段: 清理优化
- [ ] 弃用代码已删除
- [ ] 文档已更新
- [ ] 性能测试通过
- [ ] 最终验收完成

## 重构后验证

### 功能测试
- [ ] 所有旧功能正常
- [ ] 新功能正常工作
- [ ] 无破坏性变更

### 性能测试
- [ ] 性能不低于基准
- [ ] 性能报告已生成

### 覆盖率
- [ ] 测试覆盖率 >= 60%
- [ ] 覆盖率报告已生成

### 文档
- [ ] API 文档已更新
- [ ] 用户指南已更新
- [ ] 迁移指南已完成

## 完成标准

- [ ] 所有测试通过
- [ ] 性能未下降
- [ ] 覆盖率达标
- [ ] 文档完整
- [ ] 用户审核通过
"""

    checklist_file = Path("docs/REFACTOR_CHECKLIST.md")
    checklist_file.parent.mkdir(exist_ok=True)
    checklist_file.write_text(checklist, encoding='utf-8')

    print(f"[OK] 创建: {checklist_file}")
    print()


def create_progress_tracker():
    """创建进度跟踪器"""

    print("=" * 70)
    print("创建进度跟踪器")
    print("=" * 70)

    tracker = """# SuperAgent 重构进度跟踪

**开始日期**: 待定
**预计完成**: 待定

## 总体进度

- [ ] 第 1 阶段: 抽象层建立 (2-3 天)
- [ ] 第 2 阶段: 代码迁移 (3-4 天)
- [ ] 第 3 阶段: 扩展验证 (2-3 天)
- [ ] 第 4 阶段: 清理优化 (1-2 天)

## 第 1 阶段: 抽象层建立

**状态**: ⬜ 未开始

### 任务
- [ ] 创建 core/ 目录
- [ ] 实现 core/executor.py
  - [ ] Executor ABC
  - [ ] Task 数据模型
  - [ ] ExecutionResult 数据模型
- [ ] 实现 core/reviewer.py
  - [ ] Reviewer ABC
  - [ ] Artifact 数据模型
  - [ ] ReviewResult 数据模型
  - [ ] QualityMetric 数据模型
- [ ] 编写单元测试
- [ ] 验收测试

**预计时间**: 2-3 天
**实际时间**: 待定
**状态**: ⬜ 未开始 → 🔄 进行中 → ✅ 完成

## 第 2 阶段: 代码迁移

**状态**: ⬜ 未开始

### 任务
- [ ] 修改 execution/executor.py
  - [ ] 实现 Executor 接口
  - [ ] 保持向后兼容
- [ ] 修改 review/reviewer.py
  - [ ] 实现 Reviewer 接口
  - [ ] 保持向后兼容
- [ ] 修改 orchestration/orchestrator.py
  - [ ] 使用抽象接口
  - [ ] 支持多种执行器
- [ ] 运行所有测试
- [ ] 验证向后兼容

**预计时间**: 3-4 天
**实际时间**: 待定
**状态**: ⬜ 未开始 → 🔄 进行中 → ✅ 完成

## 第 3 阶段: 扩展验证

**状态**: ⬜ 未开始

### 任务
- [ ] 实现 WritingExecutor
  - [ ] execute() 方法
  - [ ] can_handle() 方法
  - [ ] get_supported_types() 方法
- [ ] 实现 ContentReviewer
  - [ ] review() 方法
  - [ ] can_review() 方法
  - [ ] get_supported_types() 方法
- [ ] 编写集成测试
- [ ] 验证扩展性
- [ ] 运行所有测试

**预计时间**: 2-3 天
**实际时间**: 待定
**状态**: ⬜ 未开始 → 🔄 进行中 → ✅ 完成

## 第 4 阶段: 清理优化

**状态**: ⬜ 未开始

### 任务
- [ ] 删除弃用代码
- [ ] 更新文档
- [ ] 性能优化
- [ ] 最终测试
- [ ] 用户验收

**预计时间**: 1-2 天
**实际时间**: 待定
**状态**: ⬜ 未开始 → 🔄 进行中 → ✅ 完成

## 问题记录

### 问题 1
- **描述**:
- **解决方案**:
- **状态**: ⬜ 未解决 → ✅ 已解决

### 问题 2
- **描述**:
- **解决方案**:
- **状态**: ⬜ 未解决 → ✅ 已解决

## 备注

### 重要决策

### 变更记录
"""

    tracker_file = Path("docs/REFACTOR_PROGRESS.md")
    tracker_file.write_text(tracker, encoding='utf-8')

    print(f"[OK] 创建: {tracker_file}")
    print()


def setup_logging():
    """配置日志系统"""

    print("=" * 70)
    print("配置日志系统")
    print("=" * 70)

    import logging
    from pathlib import Path

    # 创建日志目录
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)

    # 创建日志配置
    log_config = """#!/usr/bin/env python
# -*- coding: utf-8 -*-
\"\"\"
日志配置
\"\"\"

import logging
from pathlib import Path


def setup_logging(log_level: str = "INFO"):
    \"\"\"设置日志\"\"\"
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)

    logging.basicConfig(
        level=getattr(logging, log_level),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_dir / "superagent.log"),
            logging.StreamHandler()
        ]
    )
"""

    config_file = Path("utils/logging_config.py")
    config_file.write_text(log_config, encoding='utf-8')

    print(f"[OK] 创建: {config_file}")
    print()


def create_readme():
    """创建重构目录 README"""

    print("=" * 70)
    print("创建重构 README")
    print("=" * 70)

    readme = """# SuperAgent 重构项目

## 概述

本目录包含 SuperAgent 架构重构的所有相关文档和脚本。

## 文档结构

```
docs/
├── REFACTOR_DESIGN.md          # 主设计文档
├── ARCHITECTURE_DIAGRAMS.md     # 架构图
├── REFACTOR_CHECKLIST.md       # 检查清单
└── REFACTOR_PROGRESS.md        # 进度跟踪

scripts/
├── run_all_tests.bat            # 运行所有测试
├── pre_refactor_check.bat      # 重构前检查
└── post_refactor_check.bat     # 重构后验证
```

## 快速开始

### 重构前

1. 阅读设计文档
2. 创建 Git 分支
3. 运行重构前检查:
   ```bash
   scripts\\pre_refactor_check.bat
   ```

### 重构中

1. 按阶段执行
2. 每阶段完成后运行测试
3. 更新进度跟踪

### 重构后

1. 运行重构后验证:
   ```bash
   scripts\\post_refactor_check.bat
   ```
2. 对比重构前后性能
3. 验证所有功能

## 相关文档

- [重构准备计划](../REFACTOR_PREPARATION_PLAN.md)
- [重构设计文档](REFACTOR_DESIGN.md)
- [架构图](ARCHITECTURE_DIAGRAMS.md)
"""

    readme_file = Path("docs/REFACTOR_README.md")
    readme_file.write_text(readme, encoding='utf-8')

    print(f"[OK] 创建: {readme_file}")
    print()


def main():
    """主函数"""

    print("\n" + "=" * 70)
    print("SuperAgent 重构环境准备")
    print("=" * 70)
    print()

    # 1. 创建 Git 分支
    create_git_branches()

    # 2. 创建辅助脚本
    create_refactor_scripts()

    # 3. 创建检查清单
    create_checklist()

    # 4. 创建进度跟踪器
    create_progress_tracker()

    # 5. 配置日志
    setup_logging()

    # 6. 创建 README
    create_readme()

    print("=" * 70)
    print("重构环境准备完成!")
    print("=" * 70)
    print()
    print("下一步:")
    print("  1. 查看 docs/REFACTOR_README.md")
    print("  2. 阅读 docs/REFACTOR_DESIGN.md")
    print("  3. 运行 scripts\\pre_refactor_check.bat")
    print()

    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as e:
        print(f"\n[ERROR] 准备失败: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
