# -*- coding: utf-8 -*-
"""
测试辅助工具和Mock类

提供测试用的Mock对象和辅助函数
"""
import sys
from pathlib import Path
from typing import Dict, Any, Optional
from unittest.mock import Mock, MagicMock
import tempfile
import shutil


# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent.parent))


class MockAgent:
    """Mock Agent类 - 用于测试"""

    def __init__(self, agent_type: str = "mock-agent"):
        self.AGENT_TYPE = agent_type
        self.project_dir = None

    def execute(self, task):
        """Mock execute方法"""
        return {
            "status": "success",
            "output_files": [],
            "message": f"{self.AGENT_TYPE} executed successfully"
        }


class MockTask:
    """Mock Task类"""

    def __init__(self, task_id: str, name: str, agent_type: str,
                 input: Dict, output: list, timeout: int = 1800):
        self.id = task_id
        self.name = name
        self.agent_type = agent_type
        self.input = input
        self.output = output
        self.timeout = timeout


class TestProjectHelper:
    """测试项目辅助类"""

    def __init__(self):
        self.temp_dir = None
        self.project_dir = None

    def create_temp_project(self, project_name: str = "test_project") -> str:
        """创建临时测试项目"""
        self.temp_dir = Path(tempfile.mkdtemp())
        self.project_dir = self.temp_dir / project_name
        self.project_dir.mkdir()

        # 创建必要的子目录
        (self.project_dir / "docs").mkdir(exist_ok=True)
        (self.project_dir / "backend").mkdir(exist_ok=True)
        (self.project_dir / "frontend").mkdir(exist_ok=True)

        return str(self.project_dir)

    def create_mock_file(self, relative_path: str, content: str = ""):
        """创建Mock文件"""
        if not self.project_dir:
            raise RuntimeError("必须先调用create_temp_project()")

        file_path = self.project_dir / relative_path
        file_path.parent.mkdir(parents=True, exist_ok=True)
        file_path.write_text(content, encoding="utf-8")

        return file_path

    def cleanup(self):
        """清理临时目录"""
        if self.temp_dir and self.temp_dir.exists():
            shutil.rmtree(self.temp_dir)
            self.temp_dir = None
            self.project_dir = None


class AgentTestHelper:
    """Agent测试辅助类"""

    @staticmethod
    def mock_agent_mapping(custom_agents: Optional[Dict] = None) -> Dict:
        """创建Mock的AGENT_MAPPING"""
        default_mapping = {
            "mock-agent-1": {
                "class": "MockAgent1",
                "module": "super-agent.agents.mock_agent_1",
                "default_output": ["output1.txt"]
            },
            "mock-agent-2": {
                "class": "MockAgent2",
                "module": "super-agent.agents.mock_agent_2",
                "default_output": ["output2.txt"]
            }
        }

        if custom_agents:
            default_mapping.update(custom_agents)

        return default_mapping

    @staticmethod
    def create_mock_agent_class(class_name: str):
        """动态创建Mock Agent类"""
        return type(class_name, (MockAgent,), {
            "__name__": class_name,
            "AGENT_TYPE": class_name.lower().replace("agent", "-agent")
        })

    @staticmethod
    def assert_result_success(result: Dict, message: str = ""):
        """断言测试结果成功"""
        assert result is not None, f"{message}: 结果为None"
        assert "status" in result, f"{message}: 缺少status字段"
        assert result["status"] == "success", \
            f"{message}: 期望success, 实际{result['status']}"
        return True

    @staticmethod
    def assert_result_error(result: Dict, expected_error_substring: str = ""):
        """断言测试结果失败"""
        assert result is not None, "结果为None"
        assert result.get("status") == "error", "期望error状态"

        if expected_error_substring:
            error_msg = result.get("error", "")
            assert expected_error_substring in error_msg, \
                f"错误消息不包含 '{expected_error_substring}': {error_msg}"

        return True


class PerformanceTimer:
    """性能计时器"""

    def __init__(self):
        import time
        self.time = time
        self.start_time = None
        self.end_time = None

    def start(self):
        """开始计时"""
        self.start_time = self.time.time()
        return self

    def stop(self):
        """停止计时"""
        self.end_time = self.time.time()
        return self

    def elapsed(self) -> float:
        """获取耗时（秒）"""
        if self.start_time is None:
            return 0.0

        end = self.end_time or self.time.time()
        return end - self.start_time

    def __enter__(self):
        """上下文管理器入口"""
        return self.start()

    def __exit__(self, exc_type, exc_val, exc_tb):
        """上下文管理器出口"""
        self.stop()


def create_sample_prd(project_dir: str) -> str:
    """创建示例PRD文件"""
    prd_content = """# 产品需求文档 (PRD)

## 项目概述
开发一个测试项目

## 核心功能
- 功能1
- 功能2

## 技术栈
- Python 3.10+
- Flask
"""

    prd_path = Path(project_dir) / "docs" / "PRD.md"
    prd_path.parent.mkdir(parents=True, exist_ok=True)
    prd_path.write_text(prd_content, encoding="utf-8")

    return str(prd_path)


def create_sample_schema(project_dir: str) -> str:
    """创建示例数据库Schema文件"""
    schema_content = """-- 数据库Schema

CREATE TABLE users (
    id INT PRIMARY KEY,
    name VARCHAR(100)
);
"""

    schema_path = Path(project_dir) / "backend" / "database" / "schema.sql"
    schema_path.parent.mkdir(parents=True, exist_ok=True)
    schema_path.write_text(schema_content, encoding="utf-8")

    return str(schema_path)


def skip_if_no_claude_cli():
    """如果没有Claude CLI则跳过测试"""
    import shutil

    claude_cli = shutil.which("claude")
    if not claude_cli:
        import pytest
        pytest.skip("Claude CLI未安装", allow_module_level=True)


# 导出所有辅助类和函数
__all__ = [
    "MockAgent",
    "MockTask",
    "TestProjectHelper",
    "AgentTestHelper",
    "PerformanceTimer",
    "create_sample_prd",
    "create_sample_schema",
    "skip_if_no_claude_cli"
]
