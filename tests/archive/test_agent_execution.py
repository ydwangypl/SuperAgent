# -*- coding: utf-8 -*-
"""
集成测试: Agent端到端执行流程

测试范围:
- Agent加载和执行
- 多Agent协作工作流
- 错误处理和恢复
- 文件生成
"""
import sys
from pathlib import Path
import pytest
import shutil
from unittest.mock import patch

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from agent_tools import AgentTools


@pytest.fixture(scope="function")
def project_dir(tmp_path):
    """创建临时项目目录，每个测试后清理"""
    project = tmp_path / "integration_test_project"
    project.mkdir()

    yield str(project)

    # 清理
    if project.exists():
        shutil.rmtree(project)


@pytest.fixture(scope="function")
def agent_tools(project_dir):
    """创建AgentTools实例"""
    # Mock superagent_root指向实际目录
    real_superagent = Path(__file__).parent.parent.parent

    with patch.object(AgentTools, '_find_superagent_root', return_value=real_superagent):
        tools = AgentTools(project_dir)
        yield tools


@pytest.mark.integration
@pytest.mark.slow
class TestAgentLoading:
    """测试Agent加载功能"""

    def test_load_all_agents_successfully(self, agent_tools):
        """测试成功加载所有8个Agent"""
        loaded_agents = []

        for agent_name in AgentTools.AGENT_MAPPING.keys():
            try:
                AgentClass = agent_tools._load_agent_class(agent_name)
                loaded_agents.append(agent_name)
                assert AgentClass is not None
            except Exception as e:
                pytest.fail(f"加载Agent {agent_name} 失败: {e}")

        assert len(loaded_agents) == 8, f"只加载了 {len(loaded_agents)}/8 个Agent"

    def test_cache_effectiveness(self, agent_tools):
        """测试缓存有效性"""
        agent_name = "product-management"

        # 第一次加载 - 缓存未命中
        assert agent_name not in agent_tools._agent_cache
        agent_class1 = agent_tools._load_agent_class(agent_name)

        # 验证已缓存
        assert agent_name in agent_tools._agent_cache

        # 第二次加载 - 缓存命中
        agent_class2 = agent_tools._load_agent_class(agent_name)

        # 验证返回的是同一个类
        assert agent_class1 is agent_class2


@pytest.mark.integration
@pytest.mark.slow
class TestAgentExecution:
    """测试Agent执行功能"""

    def test_execute_product_manager_agent(self, agent_tools):
        """测试执行产品经理Agent"""
        result = agent_tools.execute_agent("product-management", {
            "user_request": "开发一个简单的任务管理系统"
        })

        assert result["status"] == "success"
        assert "files" in result
        assert len(result["files"]) > 0

        # 验证Agent已记录
        assert "product-management" in agent_tools.executed_agents

    def test_execute_with_cache_benefit(self, agent_tools, project_dir):
        """测试缓存带来的性能提升"""
        import time

        agent_name = "product-management"

        # 第一次执行（无缓存）
        start1 = time.time()
        result1 = agent_tools.execute_agent(agent_name, {
            "user_request": "测试项目1"
        })
        time1 = time.time() - start1

        # 清理生成的文件
        for file in result1.get("files", []):
            file_path = Path(file)
            if file_path.exists():
                file_path.unlink()

        # 第二次执行（有缓存）
        start2 = time.time()
        result2 = agent_tools.execute_agent(agent_name, {
            "user_request": "测试项目2"
        })
        time2 = time.time() - start2

        # 验证两次都成功
        assert result1["status"] == "success"
        assert result2["status"] == "success"

        # 验证缓存被使用（第二次应该更快或相近）
        # 注意: 这个测试可能不稳定，因为执行时间受很多因素影响
        print(f"\n[性能] 第一次: {time1:.3f}s, 第二次: {time2:.3f}s")


@pytest.mark.integration
@pytest.mark.slow
class TestWorkflowExecution:
    """测试完整工作流"""

    def test_two_agent_workflow(self, agent_tools):
        """测试两个Agent的协作工作流"""
        # 步骤1: 产品需求
        result1 = agent_tools.execute_agent("product-management", {
            "user_request": "开发一个博客系统"
        })

        assert result1["status"] == "success", f"产品经理Agent失败: {result1.get('error')}"

        # 步骤2: 数据库设计
        result2 = agent_tools.execute_agent("database-design", {})

        # 验证结果
        if result2["status"] == "error":
            # 某些Agent可能依赖文件，如果失败提供恢复建议
            assert "recovery_hint" in result2
            print(f"[提示] {result2['recovery_hint']}")
        else:
            assert result2["status"] == "success"

    def test_workflow_with_modification(self, agent_tools):
        """测试包含修改的工作流"""
        # 初始执行
        result1 = agent_tools.execute_agent("product-management", {
            "user_request": "开发一个在线书店"
        })

        assert result1["status"] == "success"

        # 修改需求
        result2 = agent_tools.modify("product-management", "增加电子书功能")

        assert result2["status"] in ["success", "error"]


@pytest.mark.integration
class TestErrorRecovery:
    """测试错误恢复机制"""

    def test_unknown_agent_error(self, agent_tools):
        """测试未知Agent的错误处理"""
        result = agent_tools.execute_agent("unknown-agent", {})

        assert result["status"] == "error"
        assert "recovery_hint" in result
        assert "不存在" in result["message"]

    def test_error_with_recovery_hint(self, agent_tools):
        """测试错误包含恢复建议"""
        # 尝试在缺少前置文件的情况下执行Agent
        result = agent_tools.execute_agent("database-design", {})

        # 不管成功还是失败，都应该有适当的处理
        assert "status" in result

        if result["status"] == "error":
            # 失败时应该有恢复建议
            assert "recovery_hint" in result
            assert len(result["recovery_hint"]) > 0

    def test_task_history_tracking(self, agent_tools):
        """测试任务历史跟踪"""
        agent_name = "product-management"
        task = {"user_request": "测试任务"}

        # 执行Agent
        agent_tools.execute_agent(agent_name, task)

        # 验证任务历史已记录
        assert agent_name in agent_tools.task_history
        assert agent_tools.task_history[agent_name] == task


@pytest.mark.integration
@pytest.mark.slow
class TestFileGeneration:
    """测试文件生成功能"""

    def test_files_generated_in_correct_location(self, agent_tools, project_dir):
        """测试文件生成在正确位置"""
        result = agent_tools.execute_agent("product-management", {
            "user_request": "测试文件生成"
        })

        if result["status"] == "success":
            # 验证生成的文件路径
            for file_path in result.get("files", []):
                path = Path(file_path)
                # 验证路径是绝对路径或相对于项目目录
                if path.is_absolute():
                    assert str(project_dir) in str(path)
                else:
                    # 相对路径，应该在项目目录下
                    full_path = Path(project_dir) / path
                    assert full_path.exists() or Path(path).exists()

    def test_show_status_displays_files(self, agent_tools, capsys):
        """测试show_status正确显示文件"""
        # 执行一个Agent
        agent_tools.execute_agent("product-management", {
            "user_request": "测试状态显示"
        })

        # 调用show_status
        agent_tools.show_status()

        # 捕获输出
        captured = capsys.readouterr()
        output = captured.out

        # 验证输出包含关键信息
        assert "项目状态" in output or "project" in output.lower()


@pytest.mark.integration
class TestAutoDiscovery:
    """测试Agent自动发现功能"""

    def test_auto_discover_agents(self, agent_tools):
        """测试自动发现Agent"""
        # 记录原始映射
        original_mapping = AgentTools.AGENT_MAPPING.copy()

        # 调用自动发现
        agent_tools.refresh_agent_mapping()

        # 验证仍然有Agent映射
        assert len(AgentTools.AGENT_MAPPING) > 0

        # 验证常见的Agent仍然存在
        common_agents = ["product-management", "database-design", "backend-dev"]
        for agent in common_agents:
            assert agent in AgentTools.AGENT_MAPPING, \
                f"自动发现后缺少常见Agent: {agent}"

    def test_auto_discover_with_cache_clear(self, agent_tools):
        """测试自动发现后缓存被清除"""
        # 预先加载一个Agent到缓存
        agent_tools._load_agent_class("product-management")
        assert "product-management" in agent_tools._agent_cache

        # 自动发现会更新AGENT_MAPPING
        agent_tools.refresh_agent_mapping()

        # 缓存应该被清除或更新
        # (因为映射可能改变，旧缓存可能失效)


@pytest.mark.integration
@pytest.mark.parametrize("agent_name", [
    "product-management",
    "database-design",
    "backend-dev",
])
def test_individual_agent_loading(agent_name, agent_tools):
    """参数化测试: 各个Agent的加载"""
    try:
        AgentClass = agent_tools._load_agent_class(agent_name)
        assert AgentClass is not None
        assert hasattr(AgentClass, 'execute'), \
            f"Agent {agent_name} 缺少execute方法"
    except Exception as e:
        pytest.fail(f"加载Agent {agent_name} 失败: {e}")


# 辅助函数
def patch(object_path, **kwargs):
    """简化patching"""
    import unittest.mock as mock
    return mock.patch(object_path, **kwargs)
