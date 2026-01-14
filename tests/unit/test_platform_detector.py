# -*- coding: utf-8 -*-
"""
平台检测器单元测试 - P2 Task 3.1

测试平台自动检测功能
"""

import unittest
import sys
import os
from unittest.mock import patch

# 添加项目路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from platform_adapters.platform_detector import PlatformDetector, Platform


class TestPlatformDetector(unittest.TestCase):
    """平台检测器测试"""

    def setUp(self):
        """测试前准备"""
        self.detector = PlatformDetector()

    def test_detector_initialization(self):
        """测试检测器初始化"""
        self.assertIsNotNone(self.detector)
        self.assertIsNone(self.detector.cached_platform)  # 初始时无缓存

    def test_detect_platform_returns_valid_platform(self):
        """测试检测返回有效的平台"""
        platform = self.detector.detect_platform()

        # 如果检测到平台,应该是有效的枚举值
        if platform:
            self.assertIsInstance(platform, Platform)
            self.assertIn(platform, list(Platform))

    def test_detect_platform_caches_result(self):
        """检测结果缓存"""
        # 第一次检测
        platform1 = self.detector.detect_platform()

        # 第二次检测应该返回相同的结果(缓存)
        platform2 = self.detector.detect_platform()

        self.assertEqual(platform1, platform2)

    def test_get_platform_info_claude_code(self):
        """测试获取 Claude Code 平台信息"""
        info = self.detector.get_platform_info(Platform.CLAUDE_CODE)

        self.assertIsInstance(info, dict)
        self.assertIn("name", info)
        self.assertIn("company", info)
        self.assertIn("description", info)
        self.assertIn("features", info)

        self.assertEqual(info["name"], "Claude Code")
        self.assertEqual(info["company"], "Anthropic")

    def test_get_platform_info_openai_codex(self):
        """测试获取 OpenAI Codex 平台信息"""
        info = self.detector.get_platform_info(Platform.OPENAI_CODEX)

        self.assertIsInstance(info, dict)
        self.assertEqual(info["name"], "OpenAI Codex")
        self.assertEqual(info["company"], "OpenAI")

    def test_get_platform_info_opencode(self):
        """测试获取 OpenCode 平台信息"""
        info = self.detector.get_platform_info(Platform.OPENCODE)

        self.assertIsInstance(info, dict)
        self.assertEqual(info["name"], "OpenCode")
        self.assertEqual(info["company"], "Community")

    def test_is_compatible_returns_bool(self):
        """测试兼容性检查返回布尔值"""
        for platform in Platform:
            compatible = self.detector.is_compatible(platform)
            self.assertIsInstance(compatible, bool)

    def test_list_compatible_platforms(self):
        """测试列出兼容平台"""
        platforms = self.detector.list_compatible_platforms()

        self.assertIsInstance(platforms, list)
        # 应该至少有一个兼容平台(OpenCode 作为默认平台)
        self.assertGreater(len(platforms), 0)

        # 所有返回的都应该是 Platform 枚举
        for platform in platforms:
            self.assertIsInstance(platform, Platform)

    @patch.dict(os.environ, {'ANTHROPIC_API_KEY': 'test_key'})
    def test_detect_claude_code_with_api_key(self):
        """测试通过 API Key 检测 Claude Code"""
        # 创建新实例以避免缓存影响
        detector = PlatformDetector()
        platform = detector.detect_platform()

        # 有 ANTHROPIC_API_KEY 时应该检测到 Claude Code
        if platform:
            self.assertEqual(platform, Platform.CLAUDE_CODE)

    @patch.dict(os.environ, {'OPENAI_API_KEY': 'test_key'})
    def test_detect_openai_codex_with_api_key(self):
        """测试通过 API Key 检测 OpenAI Codex"""
        # 创建新实例以避免缓存影响
        detector = PlatformDetector()
        platform = detector.detect_platform()

        # 有 OPENAI_API_KEY 时应该检测到 OpenAI Codex
        if platform:
            # 注意: 如果同时有 ANTHROPIC_API_KEY,会优先检测 Claude Code
            self.assertIn(platform, [Platform.OPENAI_CODEX, Platform.CLAUDE_CODE])

    def test_detection_priority(self):
        """测试检测优先级"""
        # 验证检测优先级顺序
        priority = self.detector.DETECTION_PRIORITY

        self.assertIsInstance(priority, list)
        self.assertEqual(len(priority), 3)

        # 优先级应该是: Claude Code > OpenAI Codex > OpenCode
        self.assertEqual(priority[0], Platform.CLAUDE_CODE)
        self.assertEqual(priority[1], Platform.OPENAI_CODEX)
        self.assertEqual(priority[2], Platform.OPENCODE)

    def test_get_all_platform_info(self):
        """测试获取所有平台信息"""
        all_platforms = list(Platform)

        for platform in all_platforms:
            info = self.detector.get_platform_info(platform)

            # 验证必需字段
            self.assertIn("name", info)
            self.assertIn("company", info)
            self.assertIn("description", info)
            self.assertIn("features", info)

            # 验证 features 是列表
            self.assertIsInstance(info["features"], list)

    def test_platform_info_completeness(self):
        """测试平台信息完整性"""
        required_fields = ["name", "company", "description", "features"]

        for platform in Platform:
            info = self.detector.get_platform_info(platform)

            for field in required_fields:
                self.assertIn(field, info, f"Platform {platform.value} missing field: {field}")

            # 验证字段不为空
            self.assertIsNotNone(info["name"])
            self.assertIsNotNone(info["company"])
            self.assertIsNotNone(info["description"])
            self.assertIsNotNone(info["features"])

    def test_claude_code_detection_methods(self):
        """测试 Claude Code 检测方法"""
        # 检查检测方法存在
        self.assertTrue(hasattr(self.detector, '_detect_claude_code'))
        self.assertTrue(callable(self.detector._detect_claude_code))

    def test_openai_codex_detection_methods(self):
        """测试 OpenAI Codex 检测方法"""
        # 检查检测方法存在
        self.assertTrue(hasattr(self.detector, '_detect_openai_codex'))
        self.assertTrue(callable(self.detector._detect_openai_codex))

    def test_opencode_detection_methods(self):
        """测试 OpenCode 检测方法"""
        # 检查检测方法存在
        self.assertTrue(hasattr(self.detector, '_detect_opencode'))
        self.assertTrue(callable(self.detector._detect_opencode))


class TestPlatformEnum(unittest.TestCase):
    """Platform 枚举测试"""

    def test_platform_enum_values(self):
        """测试平台枚举值"""
        self.assertEqual(Platform.CLAUDE_CODE.value, "claude_code")
        self.assertEqual(Platform.OPENAI_CODEX.value, "openai_codex")
        self.assertEqual(Platform.OPENCODE.value, "opencode")

    def test_platform_enum_count(self):
        """测试平台枚举数量"""
        platforms = list(Platform)
        self.assertEqual(len(platforms), 3)

    def test_platform_enum_unique(self):
        """测试平台枚举值唯一性"""
        platforms = list(Platform)
        values = [p.value for p in platforms]

        # 验证没有重复值
        self.assertEqual(len(values), len(set(values)))


class TestPlatformDetectionIntegration(unittest.TestCase):
    """平台检测集成测试"""

    def test_full_detection_workflow(self):
        """测试完整检测工作流"""
        detector = PlatformDetector()

        # 1. 检测平台
        platform = detector.detect_platform()

        # 2. 获取平台信息
        if platform:
            info = detector.get_platform_info(platform)
            self.assertIsNotNone(info)

            # 3. 检查兼容性
            is_compatible = detector.is_compatible(platform)
            self.assertTrue(is_compatible)

            # 4. 列出兼容平台
            compatible = detector.list_compatible_platforms()
            self.assertIn(platform, compatible)

    def test_multiple_detector_instances(self):
        """测试多个检测器实例"""
        detector1 = PlatformDetector()
        detector2 = PlatformDetector()

        # 两个实例应该检测到相同的平台
        platform1 = detector1.detect_platform()
        platform2 = detector2.detect_platform()

        self.assertEqual(platform1, platform2)

    def test_cache_independence(self):
        """测试缓存独立性"""
        detector1 = PlatformDetector()
        detector2 = PlatformDetector()

        # detector1 检测
        _ = detector1.detect_platform()
        self.assertIsNotNone(detector1.cached_platform)

        # detector2 应该有独立的缓存
        # 注意: 由于类级别的检测方法可能共享状态,这里只测试实例属性
        _ = detector2.detect_platform()
        self.assertIsNotNone(detector2.cached_platform)

        # 验证两个实例都成功检测了平台
        self.assertIsNotNone(detector1.cached_platform)
        self.assertIsNotNone(detector2.cached_platform)


if __name__ == '__main__':
    unittest.main()
