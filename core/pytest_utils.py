#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Pytest 工具模块

提供统一的 pytest 命令构建和结果解析功能。
被 TestRunner 和 TestAdapter 共用。

功能:
- 构建 pytest 命令
- 解析 pytest 输出
"""

import re
import time
from typing import List, Optional, Dict, Any, Tuple


def build_pytest_command(
    test_path: Optional[str] = None,
    verbose: bool = True,
    coverage: bool = False,
    markers: Optional[List[str]] = None,
    collect_only: bool = False,
    disable_warnings: bool = True
) -> List[str]:
    """构建 pytest 命令

    Args:
        test_path: 测试文件/目录路径 (可选,默认运行所有测试)
        verbose: 是否详细输出
        coverage: 是否生成覆盖率报告
        markers: pytest markers 过滤
        collect_only: 仅收集测试用例,不执行
        disable_warnings: 是否禁用警告

    Returns:
        pytest 命令列表
    """
    cmd = ["pytest"]

    if test_path:
        cmd.append(test_path)

    if collect_only:
        cmd.append("--collect-only")
    elif verbose:
        cmd.extend(["-v", "--tb=short"])
    else:
        cmd.extend(["-q", "--tb=line"])

    if coverage:
        cmd.extend(["--cov=."])

    if markers:
        for marker in markers:
            cmd.extend(["-m", marker])

    if disable_warnings:
        cmd.extend(["--disable-warnings"])

    return cmd


def parse_pytest_output(output: str) -> Dict[str, Any]:
    """解析 pytest 输出

    Args:
        output: pytest 原始输出

    Returns:
        解析后的结果字典,包含:
            - status: str ("completed" | "error")
            - success: bool
            - total_tests: int
            - passed: int
            - failed: int
            - errors: int
            - skipped: int
            - coverage: Optional[float]
            - failed_tests: List[str]
    """
    # 提取统计信息
    passed = 0
    failed = 0
    errors = 0
    skipped = 0

    # 匹配统计模式
    passed_match = re.search(r'(\d+)\s+passed', output)
    if passed_match:
        passed = int(passed_match.group(1))

    failed_match = re.search(r'(\d+)\s+failed', output)
    if failed_match:
        failed = int(failed_match.group(1))

    error_match = re.search(r'(\d+)\s+error', output)
    if error_match:
        errors = int(error_match.group(1))

    skipped_match = re.search(r'(\d+)\s+skipped', output)
    if skipped_match:
        skipped = int(skipped_match.group(1))

    total_tests = passed + failed + errors + skipped
    success = failed == 0 and errors == 0

    # 提取覆盖率
    coverage = None
    coverage_match = re.search(r'Total coverage:\s*(\d+(?:\.\d+)?)%', output)
    if coverage_match:
        coverage = float(coverage_match.group(1))
    else:
        # 尝试另一种格式
        cov_match = re.search(r'Coverage:\s*(\d+)%', output)
        if cov_match:
            coverage = float(cov_match.group(1))

    # 提取失败测试详情
    failed_tests = []
    for line in output.split('\n'):
        if line.startswith('FAILED '):
            test_name = line.replace('FAILED ', '').strip()
            if '::' in test_name:
                failed_tests.append(test_name)

    return {
        "status": "completed",
        "success": success,
        "total_tests": total_tests,
        "passed": passed,
        "failed": failed,
        "errors": errors,
        "skipped": skipped,
        "coverage": coverage,
        "failed_tests": failed_tests[:10]
    }


def parse_pytest_output_for_testresult(output: str, start_time: float) -> Tuple[bool, int, int, int, int, float, Optional[float], List[str], List[str]]:
    """解析 pytest 输出 (用于 TestRunner)

    Args:
        output: pytest 原始输出
        start_time: 开始时间

    Returns:
        (success, passed, failed, errors, skipped, duration, coverage, failed_tests, error_tests)
    """
    duration = time.time() - start_time

    # 提取统计信息
    passed = 0
    failed = 0
    errors = 0
    skipped = 0

    # 匹配统计模式
    passed_match = re.search(r'(\d+)\s+passed', output)
    if passed_match:
        passed = int(passed_match.group(1))

    failed_match = re.search(r'(\d+)\s+failed', output)
    if failed_match:
        failed = int(failed_match.group(1))

    error_match = re.search(r'(\d+)\s+error', output)
    if error_match:
        errors = int(error_match.group(1))

    skipped_match = re.search(r'(\d+)\s+skipped', output)
    if skipped_match:
        skipped = int(skipped_match.group(1))

    success = failed == 0 and errors == 0

    # 提取覆盖率
    coverage = None
    coverage_match = re.search(r'Total coverage:\s*(\d+(?:\.\d+)?)%', output)
    if coverage_match:
        coverage = float(coverage_match.group(1))
    else:
        cov_match = re.search(r'Coverage:\s*(\d+)%', output)
        if cov_match:
            coverage = float(cov_match.group(1))

    # 提取失败的测试名称
    failed_tests = []
    error_tests = []

    for line in output.split('\n'):
        if line.startswith('FAILED '):
            test_name = line.replace('FAILED ', '').strip()
            if '::' in test_name:
                failed_tests.append(test_name)
        elif line.startswith('ERROR '):
            error_name = line.replace('ERROR ', '').strip()
            if '::' in error_name:
                error_tests.append(error_name)

    return (success, passed, failed, errors, skipped, duration, coverage,
            failed_tests[:10], error_tests[:10])
