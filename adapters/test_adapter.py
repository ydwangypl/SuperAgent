#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
测试适配器 (TestAdapter)

为 UnifiedAdapter 提供独立测试执行能力。
用于方案B（独立API）的测试执行。

功能:
- 独立运行测试
- 同步/异步接口
- 配置选项支持
"""

import asyncio
import subprocess
import time
import logging
from pathlib import Path
from typing import Dict, Any, Optional

from core.pytest_utils import build_pytest_command, parse_pytest_output
from core.test_runner import TestResult  # 统一使用 TestResult dataclass
from common.exceptions import TimeoutError

logger = logging.getLogger(__name__)


class TestAdapter:
    """测试执行适配器 - 方案B的独立测试API"""

    def __init__(
        self,
        project_root: Path,
        timeout: int = 300
    ):
        """初始化测试适配器

        Args:
            project_root: 项目根目录
            timeout: 测试执行超时时间(秒)
        """
        self.project_root = Path(project_root)
        self._timeout = timeout

    async def run_tests(
        self,
        test_path: Optional[str] = None,
        config: Optional[Dict[str, Any]] = None
    ) -> TestResult:
        """
        独立运行测试 (异步版本)

        Args:
            test_path: 测试文件/目录路径 (可选,默认运行所有测试)
            config: 配置选项
                - verbose: bool = True
                - coverage: bool = False
                - markers: Optional[List[str]] = None
                - collect_only: bool = False
                - timeout: int = 300

        Returns:
            TestResult: 统一的测试结果
        """
        config = config or {}
        start_time = time.time()
        effective_timeout = config.get("timeout", self._timeout)

        cmd = build_pytest_command(
            test_path=test_path,
            verbose=config.get("verbose", True),
            coverage=config.get("coverage", False),
            markers=config.get("markers"),
            collect_only=config.get("collect_only", False)
        )

        logger.info(f"Running tests (async): {' '.join(cmd)}")

        # P0 Security: 添加超时控制
        async def run_with_timeout():
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=self.project_root
            )
            stdout, stderr = await process.communicate()
            return stdout, stderr

        try:
            stdout, stderr = await asyncio.wait_for(
                run_with_timeout(),
                timeout=effective_timeout
            )

            output = stdout.decode() + "\n" + stderr.decode()
            duration = time.time() - start_time

            # 使用统一的解析方法
            result = self._parse_output(output, duration)

            logger.info(
                f"Tests completed: passed={result.passed}, "
                f"failed={result.failed}, "
                f"duration={duration:.2f}s"
            )

            return result

        except asyncio.TimeoutError:
            logger.error(f"Test execution timed out ({effective_timeout}s)")
            raise TimeoutError(
                message=f"Test execution timed out after {effective_timeout}s",
                timeout=effective_timeout,
                operation="run_tests"
            )
        except Exception as e:
            logger.error(f"Test execution failed: {e}")
            return TestResult(
                success=False,
                output=str(e),
                duration_seconds=time.time() - start_time
            )

    def run_tests_sync(
        self,
        test_path: Optional[str] = None,
        config: Optional[Dict[str, Any]] = None
    ) -> TestResult:
        """
        独立运行测试 (同步版本)

        Args:
            test_path: 测试文件/目录路径
            config: 配置选项

        Returns:
            TestResult: 统一的测试结果
        """
        config = config or {}
        start_time = time.time()
        effective_timeout = config.get("timeout", self._timeout)

        cmd = build_pytest_command(
            test_path=test_path,
            verbose=config.get("verbose", True),
            coverage=config.get("coverage", False),
            markers=config.get("markers")
        )

        logger.info(f"Running tests (sync): {' '.join(cmd)}")

        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                cwd=self.project_root,
                timeout=effective_timeout
            )

            output = result.stdout + "\n" + result.stderr
            duration = time.time() - start_time

            # 使用统一的解析方法
            test_result = self._parse_output(output, duration)

            logger.info(
                f"Tests completed: passed={test_result.passed}, "
                f"failed={test_result.failed}, "
                f"duration={duration:.2f}s"
            )

            return test_result

        except subprocess.TimeoutExpired:
            logger.error(f"Test execution timed out ({effective_timeout}s)")
            return TestResult(
                success=False,
                output=f"Test execution timed out ({effective_timeout}s)",
                duration_seconds=time.time() - start_time
            )
        except Exception as e:
            logger.error(f"Test execution failed: {e}")
            return TestResult(
                success=False,
                output=str(e),
                duration_seconds=time.time() - start_time
            )

    async def run_quick_tests(self) -> TestResult:
        """运行快速测试

        Returns:
            TestResult: 统一的测试结果
        """
        return await self.run_tests(
            test_path=None,
            config={"verbose": False}
        )

    async def run_unit_tests(self, module_name: str) -> TestResult:
        """运行指定模块的单元测试

        Args:
            module_name: 模块名称 (例如: "core", "execution")

        Returns:
            TestResult: 统一的测试结果
        """
        test_path = f"tests/unit/test_{module_name}.py"
        return await self.run_tests(
            test_path=test_path,
            config={"verbose": True}
        )

    async def run_integration_tests(self) -> TestResult:
        """运行集成测试

        Returns:
            TestResult: 统一的测试结果
        """
        return await self.run_tests(
            test_path="tests/integration",
            config={"verbose": True, "markers": ["integration"]}
        )

    def set_timeout(self, timeout: int) -> None:
        """设置超时时间

        Args:
            timeout: 超时时间(秒)
        """
        self._timeout = timeout
        logger.info(f"Test timeout set to {timeout}s")

    def _parse_output(self, output: str, duration: float) -> TestResult:
        """解析 pytest 输出 - 统一使用 TestResult 格式

        Args:
            output: pytest 原始输出
            duration: 执行时间

        Returns:
            TestResult: 统一的测试结果格式
        """
        parsed = parse_pytest_output(output)
        return TestResult(
            success=parsed.get("success", False),
            total_tests=parsed.get("total_tests", 0),
            passed=parsed.get("passed", 0),
            failed=parsed.get("failed", 0),
            errors=parsed.get("errors", 0),
            skipped=parsed.get("skipped", 0),
            duration_seconds=duration,
            output=output,
            coverage=parsed.get("coverage"),
            failed_tests=[],
            error_tests=[]
        )
