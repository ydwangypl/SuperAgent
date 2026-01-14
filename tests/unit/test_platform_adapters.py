# -*- coding: utf-8 -*-
"""
平台适配器单元测试 - P2 Task 3.1

测试所有平台适配器的功能
"""

import unittest
import sys
import os

# 添加项目路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from platform_adapters import (
    PlatformAdapter,
    Platform,
    ClaudeCodeAdapter,
    OpenAICodexAdapter,
    OpenCodeAdapter,
    AdapterFactory
)


class TestClaudeCodeAdapter(unittest.TestCase):
    """Claude Code 适配器测试"""

    def setUp(self):
        """测试前准备"""
        self.adapter = ClaudeCodeAdapter()

    def test_get_platform_name(self):
        """测试获取平台名称"""
        self.assertEqual(self.adapter.get_platform_name(), "Claude Code")

    def test_get_available_tools(self):
        """测试获取可用工具"""
        tools = self.adapter.get_available_tools()
        self.assertIsInstance(tools, list)
        self.assertGreater(len(tools), 0)

        # 验证必需工具存在
        tool_names = [tool.name for tool in tools]
        self.assertIn("read_file", tool_names)
        self.assertIn("write_file", tool_names)
        self.assertIn("edit_file", tool_names)
        self.assertIn("run_bash", tool_names)
        self.assertIn("search_files", tool_names)

    def test_get_context(self):
        """测试获取平台上下文"""
        context = self.adapter.get_context()
        self.assertIsInstance(context, dict)
        self.assertIn("platform", context)
        self.assertEqual(context["platform"], "claude_code")
        self.assertIn("capabilities", context)

    def test_is_available(self):
        """测试平台可用性检查"""
        # 只验证方法可以调用,不依赖实际环境
        available = self.adapter.is_available()
        self.assertIsInstance(available, bool)


class TestOpenAICodexAdapter(unittest.TestCase):
    """OpenAI Codex 适配器测试"""

    def setUp(self):
        """测试前准备"""
        self.adapter = OpenAICodexAdapter()

    def test_get_platform_name(self):
        """测试获取平台名称"""
        self.assertEqual(self.adapter.get_platform_name(), "OpenAI Codex")

    def test_get_available_tools(self):
        """测试获取可用工具"""
        tools = self.adapter.get_available_tools()
        self.assertIsInstance(tools, list)
        self.assertGreater(len(tools), 0)

        # 验证必需工具存在
        tool_names = [tool.name for tool in tools]
        self.assertIn("read", tool_names)
        self.assertIn("write", tool_names)
        self.assertIn("edit", tool_names)
        self.assertIn("execute", tool_names)
        self.assertIn("search", tool_names)

    def test_get_context(self):
        """测试获取平台上下文"""
        context = self.adapter.get_context()
        self.assertIsInstance(context, dict)
        self.assertIn("platform", context)
        self.assertEqual(context["platform"], "openai_codex")
        self.assertIn("capabilities", context)

    def test_is_available(self):
        """测试平台可用性检查"""
        available = self.adapter.is_available()
        self.assertIsInstance(available, bool)


class TestOpenCodeAdapter(unittest.TestCase):
    """OpenCode 适配器测试"""

    def setUp(self):
        """测试前准备"""
        self.adapter = OpenCodeAdapter()

    def test_get_platform_name(self):
        """测试获取平台名称"""
        self.assertEqual(self.adapter.get_platform_name(), "OpenCode")

    def test_get_available_tools(self):
        """测试获取可用工具"""
        tools = self.adapter.get_available_tools()
        self.assertIsInstance(tools, list)
        self.assertGreater(len(tools), 0)

        # 验证必需工具存在
        tool_names = [tool.name for tool in tools]
        self.assertIn("read", tool_names)
        self.assertIn("write", tool_names)
        self.assertIn("edit", tool_names)
        self.assertIn("bash", tool_names)
        self.assertIn("grep", tool_names)
        self.assertIn("glob", tool_names)

    def test_get_context(self):
        """测试获取平台上下文"""
        context = self.adapter.get_context()
        self.assertIsInstance(context, dict)
        self.assertIn("platform", context)
        self.assertEqual(context["platform"], "opencode")
        self.assertIn("capabilities", context)

    def test_is_available(self):
        """测试平台可用性检查"""
        available = self.adapter.is_available()
        self.assertIsInstance(available, bool)


class TestAdapterFactory(unittest.TestCase):
    """适配器工厂测试"""

    def test_list_supported_platforms(self):
        """测试列出支持的平台"""
        platforms = AdapterFactory.list_supported_platforms()
        self.assertIsInstance(platforms, list)
        self.assertEqual(len(platforms), 3)

        # 验证所有平台都在列表中
        platform_values = [p.value for p in platforms]
        self.assertIn("claude_code", platform_values)
        self.assertIn("openai_codex", platform_values)
        self.assertIn("opencode", platform_values)

    def test_get_adapter_claude_code(self):
        """测试获取 Claude Code 适配器"""
        adapter = AdapterFactory.get_adapter(Platform.CLAUDE_CODE)
        self.assertIsNotNone(adapter)
        self.assertIsInstance(adapter, PlatformAdapter)
        self.assertEqual(adapter.get_platform_name(), "Claude Code")

    def test_get_adapter_openai_codex(self):
        """测试获取 OpenAI Codex 适配器"""
        adapter = AdapterFactory.get_adapter(Platform.OPENAI_CODEX)
        self.assertIsNotNone(adapter)
        self.assertIsInstance(adapter, PlatformAdapter)
        self.assertEqual(adapter.get_platform_name(), "OpenAI Codex")

    def test_get_adapter_opencode(self):
        """测试获取 OpenCode 适配器"""
        adapter = AdapterFactory.get_adapter(Platform.OPENCODE)
        self.assertIsNotNone(adapter)
        self.assertIsInstance(adapter, PlatformAdapter)
        self.assertEqual(adapter.get_platform_name(), "OpenCode")

    def test_adapter_registration(self):
        """测试适配器注册"""
        # 验证所有适配器都已注册
        for platform in Platform:
            adapter = AdapterFactory.get_adapter(platform)
            self.assertIsNotNone(adapter, f"Platform {platform.value} adapter not registered")


class TestPlatformInterface(unittest.TestCase):
    """测试平台适配器接口一致性"""

    def test_all_adapters_implement_interface(self):
        """测试所有适配器都实现了必需的接口"""
        adapters = [
            ClaudeCodeAdapter(),
            OpenAICodexAdapter(),
            OpenCodeAdapter()
        ]

        for adapter in adapters:
            # 验证所有必需方法都存在
            self.assertTrue(hasattr(adapter, 'get_platform_name'))
            self.assertTrue(hasattr(adapter, 'get_available_tools'))
            self.assertTrue(hasattr(adapter, 'execute_tool'))
            self.assertTrue(hasattr(adapter, 'get_context'))
            self.assertTrue(hasattr(adapter, 'is_available'))
            self.assertTrue(callable(adapter.get_platform_name))
            self.assertTrue(callable(adapter.get_available_tools))
            self.assertTrue(callable(adapter.execute_tool))
            self.assertTrue(callable(adapter.get_context))
            self.assertTrue(callable(adapter.is_available))

    def test_all_tools_have_required_fields(self):
        """测试所有工具都有必需的字段"""
        adapters = [
            ClaudeCodeAdapter(),
            OpenAICodexAdapter(),
            OpenCodeAdapter()
        ]

        for adapter in adapters:
            tools = adapter.get_available_tools()
            for tool in tools:
                # 验证工具必需字段
                self.assertTrue(hasattr(tool, 'name'))
                self.assertTrue(hasattr(tool, 'description'))
                self.assertTrue(hasattr(tool, 'parameters'))
                self.assertTrue(hasattr(tool, 'platform_specific'))

                # 验证工具名称非空
                self.assertIsNotNone(tool.name)
                self.assertNotEqual(tool.name, "")

                # 验证参数结构
                self.assertIsInstance(tool.parameters, dict)
                self.assertIn("type", tool.parameters)
                self.assertEqual(tool.parameters["type"], "object")


class TestPlatformTools(unittest.TestCase):
    """测试平台工具功能"""

    def test_claude_code_read_file_tool(self):
        """测试 Claude Code read_file 工具定义"""
        adapter = ClaudeCodeAdapter()
        tools = adapter.get_available_tools()
        read_tool = next((t for t in tools if t.name == "read_file"), None)

        self.assertIsNotNone(read_tool)
        self.assertIn("file_path", read_tool.parameters["properties"])
        self.assertIn("file_path", read_tool.parameters["required"])

    def test_openai_read_tool(self):
        """测试 OpenAI Codex read 工具定义"""
        adapter = OpenAICodexAdapter()
        tools = adapter.get_available_tools()
        read_tool = next((t for t in tools if t.name == "read"), None)

        self.assertIsNotNone(read_tool)
        self.assertIn("file", read_tool.parameters["properties"])
        self.assertIn("file", read_tool.parameters["required"])

    def test_opencode_read_tool(self):
        """测试 OpenCode read 工具定义"""
        adapter = OpenCodeAdapter()
        tools = adapter.get_available_tools()
        read_tool = next((t for t in tools if t.name == "read"), None)

        self.assertIsNotNone(read_tool)
        self.assertIn("path", read_tool.parameters["properties"])
        self.assertIn("path", read_tool.parameters["required"])


if __name__ == '__main__':
    unittest.main()
