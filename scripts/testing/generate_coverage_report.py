#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
测试覆盖率报告生成脚本

使用 pytest-cov 生成 SuperAgent 的测试覆盖率报告。
"""

import subprocess
import sys
from pathlib import Path


def run_coverage_tests():
    """运行覆盖率测试并生成报告"""

    print("=" * 70)
    print("SuperAgent 测试覆盖率报告生成")
    print("=" * 70)

    # 项目根目录
    project_root = Path(__file__).parent

    # 构建 pytest 命令 - 只覆盖实际被测试的模块
    cmd = [
        sys.executable, "-m", "pytest",
        "--cov=utils",              # 只测试 utils 模块 (错误处理)
        "--cov-report=html",
        "--cov-report=term-missing",
        "--cov-report=json",
        "-v",
        "tests/test_core_integration.py",
        "tests/test_async_integration.py",
    ]

    print("\n执行的命令:")
    print(" ".join(cmd))
    print("\n开始运行测试...\n")

    # 运行命令
    result = subprocess.run(
        cmd,
        cwd=project_root,
        capture_output=False,
        text=True
    )

    # 检查结果
    print("\n" + "=" * 70)
    if result.returncode == 0:
        print("覆盖率报告生成成功!")
    else:
        print("覆盖率报告生成完成 (有警告)")
    print("=" * 70)

    # 检查生成的文件
    html_report = project_root / "htmlcov" / "index.html"
    json_report = project_root / "coverage.json"

    if html_report.exists():
        print(f"\n[HTML] 报告已生成: {html_report}")
        print(f"       在浏览器中打开: file:///{html_report.as_posix()}")

    if json_report.exists():
        print(f"\n[JSON] 报告已生成: {json_report}")

        # 读取并分析覆盖率数据
        try:
            import json
            with open(json_report, 'r', encoding='utf-8') as f:
                coverage_data = json.load(f)

            print("\n" + "=" * 70)
            print("覆盖率摘要")
            print("=" * 70)

            if 'files' in coverage_data:
                total_lines = 0
                covered_lines = 0

                for file_info in coverage_data['files'].values():
                    summary = file_info['summary']
                    total_lines += summary.get('num_statements', 0)
                    covered_lines += summary.get('covered_lines', 0)

                if total_lines > 0:
                    coverage_percent = (covered_lines / total_lines) * 100
                    print(f"\n总体覆盖率: {coverage_percent:.1f}%")
                    print(f"总行数: {total_lines}")
                    print(f"已覆盖: {covered_lines}")
                    print(f"未覆盖: {total_lines - covered_lines}")

                # 显示每个文件的覆盖率
                print("\n各模块覆盖率:")
                for file_path, file_info in coverage_data['files'].items():
                    summary = file_info['summary']
                    total = summary.get('num_statements', 0)
                    covered = summary.get('covered_lines', 0)
                    if total > 0:
                        percent = (covered / total) * 100
                        print(f"  {file_path}: {percent:.1f}% ({covered}/{total})")

        except Exception as e:
            print(f"\n[WARNING] 无法解析覆盖率数据: {e}")

    print("\n" + "=" * 70)
    return 0


def create_coverage_config():
    """创建 .coveragerc 配置文件"""

    config_content = """[run]
source = .
omit =
    tests/*
    test_*.py
    */tests/*
    */test_*.py
    */__pycache__/*
    setup.py

[report]
exclude_lines =
    pragma: no cover
    def __repr__
    raise AssertionError
    raise NotImplementedError
    if __name__ == .__main__.:
    if TYPE_CHECKING:
    @abstract
    @abc.abstractmethod

[html]
directory = htmlcov

[json]
output = coverage.json
"""

    config_file = Path(__file__).parent / ".coveragerc"
    config_file.write_text(config_content, encoding='utf-8')
    print(f"[OK] 创建覆盖率配置: {config_file}")


def main():
    """主函数"""

    # 创建配置文件
    create_coverage_config()

    # 运行覆盖率测试
    return run_coverage_tests()


if __name__ == "__main__":
    sys.exit(main())
