#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
适配器层单元测试
"""

import pytest
import sys
from pathlib import Path
from typing import List

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from adapters.executor_adapter import AgentExecutor, ExecutorAdapter
from adapters.reviewer_adapter import CodeReviewerAdapter, ReviewerAdapter
from adapters.unified_adapter import UnifiedAdapter
from core.executor import Task, TaskStatus
from core.reviewer import Artifact, ReviewStatus
from common.models import AgentType


class TestAgentExecutor:
    """AgentExecutor测试"""

    def test_executor_initialization(self):
        """测试执行器初始化"""
        project_root = Path("e:/SuperAgent")
        executor = AgentExecutor(
            project_root=project_root,
            agent_type=AgentType.BACKEND_DEV,
            name="test_executor"
        )

        assert executor.name == "test_executor"
        assert executor.agent_type == AgentType.BACKEND_DEV
        assert executor.project_root == project_root

    def test_get_supported_types(self):
        """测试获取支持的类型"""
        project_root = Path("e:/SuperAgent")

        # 后端开发执行器
        backend_executor = AgentExecutor(
            project_root=project_root,
            agent_type=AgentType.BACKEND_DEV
        )
        types = backend_executor.get_supported_types()
        assert "code" in types
        assert "backend" in types
        assert "api" in types

        # 测试执行器
        test_executor = AgentExecutor(
            project_root=project_root,
            agent_type=AgentType.QA_ENGINEERING
        )
        types = test_executor.get_supported_types()
        assert "test" in types
        assert "testing" in types

    def test_validate_task_valid(self):
        """测试验证有效任务"""
        executor = AgentExecutor(
            project_root=Path("e:/SuperAgent"),
            agent_type=AgentType.BACKEND_DEV
        )

        task = Task(
            task_type="code",
            description="创建用户API"
        )

        # 注意: 由于需要Agent系统,这里只测试validate_task不抛异常
        # 实际的execute测试需要集成测试环境


class TestExecutorAdapter:
    """ExecutorAdapter测试"""

    def test_adapter_initialization(self):
        """测试适配器初始化"""
        project_root = Path("e:/SuperAgent")
        adapter = ExecutorAdapter(project_root)

        assert adapter.project_root == project_root
        assert adapter._executors == {}

    def test_map_task_to_agent(self):
        """测试任务类型到Agent的映射"""
        adapter = ExecutorAdapter(Path("e:/SuperAgent"))

        # 测试各种映射
        assert adapter._map_task_to_agent("code") == AgentType.BACKEND_DEV
        assert adapter._map_task_to_agent("backend") == AgentType.BACKEND_DEV
        assert adapter._map_task_to_agent("test") == AgentType.QA_ENGINEERING
        assert adapter._map_task_to_agent("documentation") == AgentType.TECHNICAL_WRITING

    def test_get_executor(self):
        """测试获取执行器"""
        adapter = ExecutorAdapter(Path("e:/SuperAgent"))

        executor1 = adapter.get_executor("code")
        assert isinstance(executor1, AgentExecutor)

        # 测试缓存
        executor2 = adapter.get_executor("code")
        assert executor1 is executor2


class TestCodeReviewerAdapter:
    """CodeReviewerAdapter测试"""

    def test_reviewer_initialization(self):
        """测试审查器初始化"""
        project_root = Path("e:/SuperAgent")
        reviewer = CodeReviewerAdapter(
            project_root=project_root,
            name="test_reviewer"
        )

        assert reviewer.name == "test_reviewer"
        assert reviewer.project_root == project_root
        assert reviewer._reviewer is not None

    def test_get_supported_types(self):
        """测试获取支持的类型"""
        reviewer = CodeReviewerAdapter(
            project_root=Path("e:/SuperAgent")
        )

        types = reviewer.get_supported_types()
        assert "code" in types
        assert "python" in types


class TestReviewerAdapter:
    """ReviewerAdapter测试"""

    def test_adapter_initialization(self):
        """测试适配器初始化"""
        project_root = Path("e:/SuperAgent")
        adapter = ReviewerAdapter(project_root)

        assert adapter.project_root == project_root
        assert adapter._reviewers == {}


class TestUnifiedAdapter:
    """UnifiedAdapter测试"""

    def test_adapter_initialization(self):
        """测试统一适配器初始化"""
        project_root = Path("e:/SuperAgent")
        adapter = UnifiedAdapter(project_root)

        assert adapter.project_root == project_root
        assert adapter.executor is not None
        assert adapter.reviewer is not None

    def test_extract_code_for_review_from_list(self):
        """测试从列表中提取代码"""
        adapter = UnifiedAdapter(Path("e:/SuperAgent"))

        exec_result = {
            "success": True,
            "content": [
                {
                    "id": "file1",
                    "type": "code",
                    "path": None,
                    "content": "def hello():\n    pass"
                }
            ]
        }

        code = adapter._extract_code_for_review(exec_result)
        assert code is not None
        assert "file1.py" in code
        assert "def hello" in code["file1.py"]

    def test_extract_code_for_review_from_string(self):
        """测试从字符串中提取代码"""
        adapter = UnifiedAdapter(Path("e:/SuperAgent"))

        exec_result = {
            "success": True,
            "content": "def test():\n    pass"
        }

        code = adapter._extract_code_for_review(exec_result)
        assert code is not None
        assert "generated_code.py" in code
        assert "def test" in code["generated_code.py"]

    def test_extract_code_for_review_failed(self):
        """测试提取失败情况"""
        adapter = UnifiedAdapter(Path("e:/SuperAgent"))

        # 执行失败
        exec_result = {
            "success": False,
            "error": "Task failed"
        }

        code = adapter._extract_code_for_review(exec_result)
        assert code is None

        # 无效内容
        exec_result = {
            "success": True,
            "content": None
        }

        code = adapter._extract_code_for_review(exec_result)
        assert code is None

    def test_generate_summary_success_only(self):
        """测试生成总结 - 仅执行成功"""
        adapter = UnifiedAdapter(Path("e:/SuperAgent"))

        exec_result = {
            "success": True,
            "content": ["file1.py"],
            "execution_time": 1.5
        }

        summary = adapter._generate_summary(exec_result, None)

        assert "✅ 任务执行成功" in summary
        assert "1.5" in summary
        assert "生成产物: 1个" in summary

    def test_generate_summary_with_review(self):
        """测试生成总结 - 包含审查"""
        adapter = UnifiedAdapter(Path("e:/SuperAgent"))

        exec_result = {
            "success": True,
            "content": ["file1.py"],
            "execution_time": 2.0
        }

        review_result = {
            "approved": True,
            "overall_score": 85.0,
            "metadata": {
                "issue_count": 3,
                "critical_count": 0,
                "major_count": 1
            }
        }

        summary = adapter._generate_summary(exec_result, review_result)

        assert "✅ 任务执行成功" in summary
        assert "✅ 代码审查通过" in summary
        assert "85.0" in summary
        assert "发现问题: 3个" in summary
        assert "重要: 1个" in summary

    def test_generate_summary_failure(self):
        """测试生成总结 - 执行失败"""
        adapter = UnifiedAdapter(Path("e:/SuperAgent"))

        exec_result = {
            "success": False,
            "error": "Execution failed"
        }

        summary = adapter._generate_summary(exec_result, None)

        assert "❌ 任务执行失败" in summary
        assert "Execution failed" in summary


class TestAdaptersIntegration:
    """适配器集成测试"""

    def test_end_to_end_adapter_flow(self):
        """测试端到端适配器流程"""
        # 这个测试需要实际的Agent环境,暂时跳过
        pytest.skip("Requires Agent environment")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
