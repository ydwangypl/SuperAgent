# -*- coding: utf-8 -*-
"""
单元测试: AgentTools核心功能

测试范围:
- 路径解析
- Agent映射
- 缓存机制
- 错误恢复建议生成
"""
import sys
from pathlib import Path
import unittest
import shutil
import tempfile
import pytest
from unittest.mock import Mock, patch, MagicMock

from common.models import AgentType

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from agent_tools import AgentTools


@pytest.fixture
def agent_tools(tmp_path):
    """创建AgentTools fixture"""
    project_dir = tmp_path / "test_project"
    project_dir.mkdir()
    with patch.object(AgentTools, '_find_superagent_root', return_value=Path(__file__).parent.parent.parent):
        return AgentTools(str(project_dir))


class TestAgentTools(unittest.TestCase):
    """测试AgentTools核心功能"""

    def setUp(self):
        """测试前准备"""
        self.temp_dir = tempfile.mkdtemp(prefix="superagent_test_")
        # Mock superagent_root
        with patch.object(AgentTools, '_find_superagent_root', return_value=Path(self.temp_dir).parent):
            self.tools = AgentTools(self.temp_dir)

    def tearDown(self):
        """测试后清理"""
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_init_basic(self):
        """测试基本初始化"""
        with patch.object(AgentTools, '_find_superagent_root', return_value=Path(self.temp_dir)):
            tools = AgentTools(self.temp_dir)

            self.assertEqual(tools.project_dir, Path(self.temp_dir).resolve())
            self.assertEqual(tools.executed_agents, [])
            self.assertEqual(tools.task_history, {})
            self.assertEqual(tools._agent_cache, {})

    def test_init_with_auto_discover(self):
        """测试启用自动发现的初始化"""
        with patch.object(AgentTools, '_find_superagent_root', return_value=Path(self.temp_dir)):
            with patch.object(AgentTools, 'refresh_agent_mapping') as mock_refresh:
                tools = AgentTools(self.temp_dir, auto_discover=True)
                mock_refresh.assert_called_once()

    def test_agent_mapping_completeness(self):
        """测试AGENT_MAPPING包含所有8个Agent"""
        expected_agents = {
            "product-management",
            "database-design",
            "backend-dev",
            "frontend-dev",
            "qa-engineering",
            "devops-engineering",
            "mini-program-dev",
            "ui-design"
        }

        actual_agents = set(AgentTools.AGENT_MAPPING.keys())

        self.assertEqual(actual_agents, expected_agents,
            f"AGENT映射不完整。期望: {expected_agents}, 实际: {actual_agents}")

    def test_resolve_agent_module_path(self):
        """测试Agent模块路径解析"""
        module_name = "super-agent.agents.product_manager_agent"
        result = self.tools._resolve_agent_module_path(module_name)

        # 验证路径格式
        self.assertTrue(str(result).replace('\\', '/').endswith(".super-agent/agents/product_manager_agent.py"))
        self.assertTrue(result.is_absolute())

    def test_resolve_multiple_modules(self):
        """测试多个模块的路径解析"""
        test_cases = [
            ("super-agent.agents.database_designer_agent",
             ".super-agent/agents/database_designer_agent.py"),
            ("super-agent.agents.backend_architect_agent",
             ".super-agent/agents/backend_architect_agent.py"),
            ("super-agent.agents.qa_engineer_agent",
             ".super-agent/agents/qa_engineer_agent.py"),
        ]

        for module_name, expected_suffix in test_cases:
            result = self.tools._resolve_agent_module_path(module_name)
            self.assertTrue(str(result).replace('\\', '/').endswith(expected_suffix)), \
                f"模块 {module_name} 路径解析错误: {result}"


class TestAgentCache:
    """测试Agent缓存机制"""

    def test_cache_initially_empty(self, agent_tools):
        """测试缓存初始为空"""
        assert len(agent_tools._agent_cache) == 0

    def test_cache_stores_agent_class(self, agent_tools):
        """测试缓存存储Agent类"""
        # Mock加载过程
        mock_agent_class = Mock(name="MockAgent")
        agent_tools._agent_cache["test-agent"] = mock_agent_class

        assert "test-agent" in agent_tools._agent_cache
        assert agent_tools._agent_cache["test-agent"] == mock_agent_class

    def test_cache_hit_returns_cached_class(self, agent_tools):
        """测试缓存命中时返回缓存的类"""
        mock_agent_class = Mock(name="MockAgent")
        agent_tools._agent_cache["cached-agent"] = mock_agent_class

        # 验证从缓存读取
        result = agent_tools._agent_cache.get("cached-agent")

        assert result == mock_agent_class

    def test_cache_multiple_agents(self, agent_tools):
        """测试缓存多个Agent"""
        agents = {
            "agent1": Mock(name="Agent1"),
            "agent2": Mock(name="Agent2"),
            "agent3": Mock(name="Agent3")
        }

        for name, agent_class in agents.items():
            agent_tools._agent_cache[name] = agent_class

        assert len(agent_tools._agent_cache) == 3
        for name in agents:
            assert name in agent_tools._agent_cache


class TestRecoveryHints:
    """测试错误恢复建议生成"""

    @pytest.mark.parametrize("error_msg,expected_hint", [
        ("找不到PRD文件", "请先执行product-management Agent生成PRD文档"),
        ("缺少schema", "请先执行database-design Agent生成数据库schema"),
        ("API不存在", "请先执行backend-dev Agent生成API代码"),
        ("文件不存在错误", "请检查必需的文件是否存在"),
        ("权限被拒绝", "请检查文件和目录的读写权限"),
        ("导入模块失败", "请检查Python环境和依赖包"),
    ])
    def test_recovery_hint_matching(self, agent_tools, error_msg, expected_hint):
        """测试错误消息匹配恢复建议"""
        hint = agent_tools._get_recovery_hint("test-agent", error_msg)

        # 验证建议包含关键词
        assert any(keyword in hint for keyword in expected_hint.split()[:3])

    def test_agent_specific_hints(self, agent_tools):
        """测试Agent特定的恢复建议"""
        test_cases = [
            ("database-design", "product-management"),
            ("backend-dev", "product-management和database-design"),
            ("frontend-dev", "product-management和backend-dev"),
        ]

        for agent_name, expected_dependency in test_cases:
            hint = agent_tools._get_recovery_hint(agent_name, "unknown error")
            assert expected_dependency in hint, \
                f"Agent {agent_name} 的依赖建议不正确"

    def test_default_hint(self, agent_tools):
        """测试默认恢复建议"""
        hint = agent_tools._get_recovery_hint("unknown-agent", "unknown error")

        assert "show_status()" in hint or "错误详情" in hint


class TestAgentMapping:
    """测试AGENT_MAPPING配置"""

    def test_all_agents_have_required_fields(self):
        """测试所有Agent映射都包含必需字段"""
        required_fields = {"class", "module", "default_output"}

        for agent_name, agent_info in AgentTools.AGENT_MAPPING.items():
            assert required_fields.issubset(agent_info.keys()), \
                f"Agent {agent_name} 缺少必需字段"

    def test_agent_classes_exist(self):
        """测试所有Agent类名符合命名规范"""
        for agent_name, agent_info in AgentTools.AGENT_MAPPING.items():
            class_name = agent_info["class"]
            # 类名应该以Agent结尾
            assert class_name.endswith("Agent"), \
                f"Agent {agent_name} 的类名 {class_name} 不符合规范"

    def test_module_names_consistent(self):
        """测试模块名格式一致"""
        for agent_name, agent_info in AgentTools.AGENT_MAPPING.items():
            module_name = agent_info["module"]
            # 模块名应该以super-agent.agents开头
            assert module_name.startswith("super-agent.agents."), \
                f"Agent {agent_name} 的模块名 {module_name} 格式不一致"


class TestErrorHandling:
    """测试错误处理"""

    def test_value_error_for_unknown_agent(self, agent_tools):
        """测试未知Agent抛出ValueError"""
        with pytest.raises(ValueError) as exc_info:
            agent_tools._load_agent_class("non-existent-agent")

        assert "不存在" in str(exc_info.value)
        assert "non-existent-agent" in str(exc_info.value)

    @patch('orchestration.registry.AgentRegistry.get_impl_class', return_value=None)
    @patch('agent_tools.AgentTools.AGENT_MAPPING', {
        "product-management": {
            "type": AgentType.PRODUCT_MANAGEMENT,
            "module": "invalid.module", 
            "class": "InvalidClass", 
            "default_output": []
        }
    })
    def test_import_error_for_invalid_module(self, mock_get_impl, agent_tools):
        """测试无效模块抛出ImportError"""
        # 清除缓存以强制加载
        agent_tools._agent_cache.clear()

        with pytest.raises(ImportError) as exc_info:
            agent_tools._load_agent_class("product-management")

        assert "加载Agent product-management 失败" in str(exc_info.value)


class TestUtilityMethods:
    """测试工具方法"""

    def test_get_next_steps_empty(self, agent_tools):
        """测试没有执行Agent时的下一步建议"""
        next_steps = agent_tools.get_next_steps()

        expected = list(AgentTools.AGENT_MAPPING.keys())
        assert set(next_steps) == set(expected)

    def test_get_next_steps_partial(self, agent_tools):
        """测试部分执行Agent后的下一步建议"""
        agent_tools.executed_agents = ["product-management", "database-design"]

        next_steps = agent_tools.get_next_steps()

        assert "product-management" not in next_steps
        assert "database-design" not in next_steps
        assert "backend-dev" in next_steps

    def test_get_next_steps_complete(self, agent_tools):
        """测试所有Agent执行完成后的下一步建议"""
        agent_tools.executed_agents = list(AgentTools.AGENT_MAPPING.keys())

        next_steps = agent_tools.get_next_steps()

        assert len(next_steps) == 0


@pytest.mark.parametrize("agent_name,expected_class", [
    ("product-management", "ProductManagerAgent"),
    ("database-design", "DatabaseDesignerAgent"),
    ("backend-dev", "BackendArchitectAgent"),
    ("frontend-dev", "WebFrontendDeveloperAgent"),
    ("qa-engineering", "QaEngineerAgent"),
    ("devops-engineering", "DevopsEngineerAgent"),
    ("mini-program-dev", "MiniProgramDeveloperAgent"),
    ("ui-design", "UiDesignerAgent"),
])
def test_agent_class_names_correct(agent_name, expected_class):
    """测试所有Agent的类名正确"""
    assert AgentTools.AGENT_MAPPING[agent_name]["class"] == expected_class
