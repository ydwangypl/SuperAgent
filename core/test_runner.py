#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
测试运行器 (TestRunner)

提供测试执行能力，支持 pytest 和 unittest。
用于方案A（主工作流集成）的自动测试执行。

功能:
- 运行 pytest 测试
- 运行 unittest 测试
- 解析测试结果
- 支持覆盖率报告
"""

import asyncio
import subprocess
import time
import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional, Dict, Any

from .pytest_utils import build_pytest_command, parse_pytest_output_for_testresult

logger = logging.getLogger(__name__)


@dataclass
class TestResult:
    """测试结果数据类"""
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

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "success": self.success,
            "total_tests": self.total_tests,
            "passed": self.passed,
            "failed": self.failed,
            "errors": self.errors,
            "skipped": self.skipped,
            "duration_seconds": self.duration_seconds,
            "output": self.output,
            "coverage": self.coverage,
            "failed_tests": self.failed_tests,
            "error_tests": self.error_tests
        }


class TestRunner:
    """测试运行器 - 支持 pytest 和 unittest"""

    def __init__(
        self,
        project_root: Optional[Path] = None,
        timeout: int = 300
    ):
        """初始化测试运行器

        Args:
            project_root: 项目根目录
            timeout: 测试执行超时时间(秒)
        """
        self.project_root = project_root or Path(".")
        self._last_result: Optional[TestResult] = None
        self._timeout = timeout

    async def run_pytest(
        self,
        test_path: Optional[str] = None,
        verbose: bool = True,
        collect_only: bool = False,
        coverage: bool = False,
        markers: Optional[List[str]] = None,
        timeout: Optional[int] = None
    ) -> TestResult:
        """运行 pytest 测试

        Args:
            test_path: 测试文件/目录路径 (可选,默认运行所有测试)
            verbose: 是否详细输出
            collect_only: 仅收集测试用例,不执行
            coverage: 是否生成覆盖率报告
            markers: pytest markers 过滤
            timeout: 超时时间(秒),覆盖默认配置

        Returns:
            TestResult: 测试结果
        """
        start_time = time.time()

        cmd = build_pytest_command(
            test_path=test_path,
            verbose=verbose,
            coverage=coverage,
            markers=markers,
            collect_only=collect_only
        )

        logger.info(f"Running pytest: {' '.join(cmd)}")

        try:
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=self.project_root
            )
            stdout, stderr = await process.communicate()

            output = stdout.decode()
            error_output = stderr.decode()

            full_output = output + "\n" + error_output

            result = self._parse_pytest_output(full_output, start_time)

            logger.info(
                f"Tests completed: passed={result.passed}, "
                f"failed={result.failed}, "
                f"duration={result.duration_seconds:.2f}s"
            )

            return result

        except FileNotFoundError:
            logger.error("pytest not installed. Run: pip install pytest pytest-asyncio")
            return TestResult(
                success=False,
                output="pytest not installed",
                duration_seconds=time.time() - start_time
            )
        except Exception as e:
            logger.error(f"Test execution failed: {e}")
            return TestResult(
                success=False,
                output=str(e),
                duration_seconds=time.time() - start_time
            )

    def run_pytest_sync(
        self,
        test_path: Optional[str] = None,
        verbose: bool = True,
        coverage: bool = False,
        markers: Optional[List[str]] = None,
        timeout: Optional[int] = None
    ) -> TestResult:
        """同步运行 pytest 测试

        Args:
            test_path: 测试文件/目录路径
            verbose: 是否详细输出
            coverage: 是否生成覆盖率报告
            markers: pytest markers 过滤
            timeout: 超时时间(秒),覆盖默认配置

        Returns:
            TestResult: 测试结果
        """
        start_time = time.time()
        effective_timeout = timeout or self._timeout

        cmd = build_pytest_command(
            test_path=test_path,
            verbose=verbose,
            coverage=coverage,
            markers=markers
        )

        logger.info(f"Running pytest (sync): {' '.join(cmd)}")

        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                cwd=self.project_root,
                timeout=effective_timeout
            )

            output = result.stdout + "\n" + result.stderr
            parsed_result = self._parse_pytest_output(output, start_time)

            logger.info(
                f"Tests completed: passed={parsed_result.passed}, "
                f"failed={parsed_result.failed}, "
                f"duration={parsed_result.duration_seconds:.2f}s"
            )

            return parsed_result

        except subprocess.TimeoutExpired:
            logger.error(f"Test execution timed out ({effective_timeout}s)")
            return TestResult(
                success=False,
                output="Test execution timed out",
                duration_seconds=time.time() - start_time
            )
        except FileNotFoundError:
            logger.error("pytest not installed")
            return TestResult(
                success=False,
                output="pytest not installed",
                duration_seconds=time.time() - start_time
            )
        except Exception as e:
            logger.error(f"Test execution failed: {e}")
            return TestResult(
                success=False,
                output=str(e),
                duration_seconds=time.time() - start_time
            )

    def _parse_pytest_output(self, output: str, start_time: float) -> TestResult:
        """解析 pytest 输出

        Args:
            output: pytest 原始输出
            start_time: 开始时间

        Returns:
            TestResult: 解析后的结果
        """
        (success, passed, failed, errors, skipped, duration,
         coverage, failed_tests, error_tests) = parse_pytest_output_for_testresult(
            output, start_time
        )

        total_tests = passed + failed + errors + skipped

        return TestResult(
            success=success,
            total_tests=total_tests,
            passed=passed,
            failed=failed,
            errors=errors,
            skipped=skipped,
            duration_seconds=duration,
            output=output,
            coverage=coverage,
            failed_tests=failed_tests,
            error_tests=error_tests
        )

    async def run_specific_tests(
        self,
        test_files: List[str],
        verbose: bool = True
    ) -> TestResult:
        """运行指定的测试文件

        Args:
            test_files: 测试文件路径列表
            verbose: 是否详细输出

        Returns:
            TestResult: 测试结果
        """
        if not test_files:
            return TestResult(success=True, output="No test files specified")

        cmd = list(test_files)

        if verbose:
            cmd.extend(["-v", "--tb=short"])
        else:
            cmd.extend(["-q", "--tb=line"])

        cmd.extend(["--disable-warnings"])

        start_time = time.time()

        try:
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=self.project_root
            )
            stdout, stderr = await process.communicate()

            output = stdout.decode() + "\n" + stderr.decode()
            return self._parse_pytest_output(output, start_time)

        except Exception as e:
            return TestResult(
                success=False,
                output=str(e),
                duration_seconds=time.time() - start_time
            )

    async def run_tests_with_pattern(
        self,
        pattern: str,
        verbose: bool = True
    ) -> TestResult:
        """运行匹配模式的测试

        Args:
            pattern: 测试名称匹配模式 (例如: "test_user_*")
            verbose: 是否详细输出

        Returns:
            TestResult: 测试结果
        """
        cmd = ["-k", pattern]
        if verbose:
            cmd.extend(["-v", "--tb=short"])
        cmd.append("--disable-warnings")
        return await self.run_pytest(test_path=None, verbose=verbose)

    def get_last_result(self) -> Optional[TestResult]:
        """获取上次测试结果"""
        return self._last_result

    def run_quick_tests(self) -> TestResult:
        """运行快速测试 (仅失败和错误的测试)

        Returns:
            TestResult: 测试结果
        """
        return self.run_pytest_sync(
            test_path=None,
            verbose=False,
            coverage=False
        )

    def set_timeout(self, timeout: int) -> None:
        """设置超时时间

        Args:
            timeout: 超时时间(秒)
        """
        self._timeout = timeout
        logger.info(f"Test timeout set to {timeout}s")
