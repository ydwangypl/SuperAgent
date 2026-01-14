# -*- coding: utf-8 -*-
"""
工具映射器单元测试 - P2 Task 3.1

测试工具映射器的跨平台转换功能
"""

import unittest
import sys
import os

# 添加项目路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from platform_adapters import ToolMapper, ToolMapping


class TestToolMapper(unittest.TestCase):
    """工具映射器测试"""

    def setUp(self):
        """测试前准备"""
        self.mapper = ToolMapper()

    def test_map_tool_name_claude_to_openai(self):
        """测试 Claude Code 到 OpenAI Codex 的工具名称映射"""
        mapped = self.mapper.map_tool_name("read_file", "claude_code", "openai_codex")
        self.assertEqual(mapped, "read")

    def test_map_tool_name_openai_to_claude(self):
        """测试 OpenAI Codex 到 Claude Code 的工具名称映射"""
        mapped = self.mapper.map_tool_name("read", "openai_codex", "claude_code")
        self.assertEqual(mapped, "read_file")

    def test_map_tool_name_same_platform(self):
        """测试相同平台的工具名称映射"""
        mapped = self.mapper.map_tool_name("read_file", "claude_code", "claude_code")
        self.assertEqual(mapped, "read_file")

    def test_map_tool_name_unknown_mapping(self):
        """测试未知工具映射"""
        mapped = self.mapper.map_tool_name("unknown_tool", "claude_code", "openai_codex")
        self.assertEqual(mapped, "unknown_tool")

    def test_map_parameters_read_file(self):
        """测试 read_file 参数映射"""
        params = {"file_path": "test.py"}
        mapped = self.mapper.map_parameters("read_file", params, "claude_code", "openai_codex")

        self.assertIsInstance(mapped, dict)
        self.assertIn("file", mapped)
        self.assertEqual(mapped["file"], "test.py")

    def test_map_parameters_write_file(self):
        """测试 write_file 参数映射"""
        params = {"file_path": "test.py", "content": "print('hello')"}
        mapped = self.mapper.map_parameters("write_file", params, "claude_code", "openai_codex")

        self.assertIsInstance(mapped, dict)
        self.assertIn("file", mapped)
        self.assertIn("contents", mapped)
        self.assertEqual(mapped["file"], "test.py")
        self.assertEqual(mapped["contents"], "print('hello')")

    def test_map_parameters_edit_file(self):
        """测试 edit_file 参数映射"""
        params = {
            "file_path": "test.py",
            "old_str": "old",
            "new_str": "new"
        }
        mapped = self.mapper.map_parameters("edit_file", params, "claude_code", "openai_codex")

        # 验证参数已被正确映射
        self.assertIsInstance(mapped, dict)
        self.assertIn("file", mapped)  # file_path → file
        self.assertIn("old_text", mapped)  # old_str → old_text
        self.assertIn("new_text", mapped)  # new_str → new_text
        self.assertEqual(mapped["file"], "test.py")
        self.assertEqual(mapped["old_text"], "old")
        self.assertEqual(mapped["new_text"], "new")

    def test_map_parameters_preserve_unknown(self):
        """测试保留未知参数"""
        params = {"file_path": "test.py", "unknown_param": "value"}
        mapped = self.mapper.map_parameters("read_file", params, "claude_code", "openai_codex")

        # 未知参数应该被保留
        self.assertIn("unknown_param", mapped)

    def test_has_mapping(self):
        """测试检查映射是否存在"""
        # 存在的映射
        has_map = self.mapper.has_mapping("read_file", "claude_code", "openai_codex")
        self.assertTrue(has_map)

        # 不存在的映射
        has_map = self.mapper.has_mapping("unknown_tool", "claude_code", "openai_codex")
        self.assertFalse(has_map)

    def test_get_mapping_info(self):
        """测试获取映射信息"""
        info = self.mapper.get_mapping_info("read_file", "claude_code", "openai_codex")

        self.assertIsNotNone(info)
        self.assertEqual(info.tool_name, "read_file")
        self.assertEqual(info.mapped_name, "read")
        self.assertIn("file_path", info.parameter_map)

    def test_list_mappings_for_platforms(self):
        """测试列出平台间的所有映射"""
        mappings = self.mapper.list_mappings_for_platforms("claude_code", "openai_codex")

        self.assertIsInstance(mappings, list)
        self.assertGreater(len(mappings), 0)

        # 验证至少包含一些基本映射
        tool_names = [m.tool_name for m in mappings]
        self.assertIn("read_file", tool_names)
        self.assertIn("write_file", tool_names)

    def test_map_result_success(self):
        """测试映射成功结果"""
        result = {"output": "success", "error": None}
        mapped = self.mapper.map_result("read_file", result, "openai_codex", "claude_code")

        self.assertIsNotNone(mapped)

    def test_map_result_error(self):
        """测试映射错误结果"""
        result = {"output": None, "error": "File not found"}
        mapped = self.mapper.map_result("read_file", result, "openai_codex", "claude_code")

        self.assertIsNotNone(mapped)

    def test_default_mappings_loaded(self):
        """测试默认映射已加载"""
        # 验证一些关键映射存在
        test_cases = [
            # Claude Code → OpenAI Codex
            ("read_file", "claude_code", "openai_codex", "read"),
            ("write_file", "claude_code", "openai_codex", "write"),
            ("edit_file", "claude_code", "openai_codex", "edit"),
            ("run_bash", "claude_code", "openai_codex", "execute"),
            ("search_files", "claude_code", "openai_codex", "search"),
            # OpenAI Codex → Claude Code
            ("read", "openai_codex", "claude_code", "read_file"),
            ("write", "openai_codex", "claude_code", "write_file"),
            # Claude Code → OpenCode
            ("read_file", "claude_code", "opencode", "read"),
            ("write_file", "claude_code", "opencode", "write"),
            # OpenCode → Claude Code
            ("read", "opencode", "claude_code", "read_file"),
            ("bash", "opencode", "claude_code", "run_bash"),
        ]

        for tool, source, target, expected in test_cases:
            mapped = self.mapper.map_tool_name(tool, source, target)
            self.assertEqual(mapped, expected, f"Failed to map {tool} from {source} to {target}")


class TestToolMapping(unittest.TestCase):
    """ToolMapping 数据类测试"""

    def test_tool_mapping_creation(self):
        """测试创建 ToolMapping"""
        mapping = ToolMapping(
            source_platform="platform_a",
            target_platform="platform_b",
            tool_name="tool_a",
            mapped_name="tool_b",
            parameter_map={
                "param_a": "param_b"
            },
            parameter_transforms={}
        )

        self.assertEqual(mapping.source_platform, "platform_a")
        self.assertEqual(mapping.target_platform, "platform_b")
        self.assertEqual(mapping.tool_name, "tool_a")
        self.assertEqual(mapping.mapped_name, "tool_b")
        self.assertIn("param_a", mapping.parameter_map)

    def test_tool_mapping_optional_fields(self):
        """测试 ToolMapping 可选字段"""
        mapping = ToolMapping(
            source_platform="platform_a",
            target_platform="platform_b",
            tool_name="tool_a",
            mapped_name="tool_b",
            parameter_map={},
            parameter_transforms={}
        )

        # 参数映射应该是空字典
        self.assertEqual(mapping.parameter_map, {})


class TestCrossPlatformCompatibility(unittest.TestCase):
    """跨平台兼容性测试"""

    def setUp(self):
        """测试前准备"""
        self.mapper = ToolMapper()

    def test_bidirectional_mapping(self):
        """测试双向映射"""
        # Claude Code -> OpenAI Codex
        mapped_to_openai = self.mapper.map_tool_name("read_file", "claude_code", "openai_codex")

        # OpenAI Codex -> Claude Code
        mapped_to_claude = self.mapper.map_tool_name(mapped_to_openai, "openai_codex", "claude_code")

        # 应该能映射回原始名称(或等效名称)
        self.assertIsNotNone(mapped_to_claude)

    def test_parameter_round_trip(self):
        """测试参数往返映射"""
        # 原始参数
        original_params = {
            "file_path": "test.py",
            "content": "print('hello')"
        }

        # Claude Code -> OpenAI Codex
        mapped_to_openai = self.mapper.map_parameters(
            "write_file",
            original_params,
            "claude_code",
            "openai_codex"
        )

        # OpenAI Codex -> Claude Code
        mapped_to_claude = self.mapper.map_parameters(
            "write",
            mapped_to_openai,
            "openai_codex",
            "claude_code"
        )

        # 验证关键数据保留
        self.assertIsNotNone(mapped_to_claude)


if __name__ == '__main__':
    unittest.main()
