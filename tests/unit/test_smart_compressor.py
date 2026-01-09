#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
智能上下文压缩系统单元测试 - SuperAgent v2.2.0
"""

import unittest
import sys
from pathlib import Path
import hashlib

# 添加模块路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from context.smart_compressor import (
    KeyInformationExtractor,
    SemanticCompressor,
    StructuredCompressor,
    SmartContextCompressor,
    ContextCache,
    CompressionStats,
    ExtractedInfo
)


class TestKeyInformationExtractor(unittest.TestCase):
    """测试关键信息提取器"""

    def setUp(self):
        self.extractor = KeyInformationExtractor()

    def test_extract_chinese_product_info(self):
        """测试提取中文产品信息"""
        content = """
# 产品需求文档
产品名称: SuperAgent AI项目管理系统
项目名称: 智能化软件开发平台
核心功能: 自动生成代码, 智能规划任务
"""
        extracted = self.extractor.extract(content)
        # 验证提取到的信息
        self.assertTrue(any("SuperAgent AI项目管理系统" in item for item in extracted.product))
        self.assertTrue(any("智能化软件开发平台" in item for item in extracted.product))
        self.assertTrue(any("自动生成代码" in item for item in extracted.product))

    def test_extract_tech_stack(self):
        """测试提取技术栈"""
        content = """
技术栈: Python, FastAPI, PostgreSQL
数据库: Redis, MongoDB
"""
        extracted = self.extractor.extract(content)

        self.assertGreater(len(extracted.tech), 0)
        self.assertTrue(any("Python" in item for item in extracted.tech))

    def test_format_extracted(self):
        """测试格式化提取的信息"""
        info = ExtractedInfo(
            product=["Test Product"],
            tech=["Python"],
            requirements=["Feature 1"]
        )
        summary = info.to_summary()
        self.assertIn("Test Product", summary)
        self.assertIn("Python", summary)


class TestSemanticCompressor(unittest.TestCase):
    """测试语义压缩器"""

    def setUp(self):
        self.compressor = SemanticCompressor()

    def test_compress_short_content(self):
        """测试压缩短内容"""
        content = "这是一个非常短的内容，不应该被过度压缩。"
        compressed, stats = self.compressor.compress(content)
        
        self.assertIsInstance(compressed, str)
        self.assertIsInstance(stats, CompressionStats)
        self.assertEqual(stats.original_length, len(content))

    def test_compress_long_content(self):
        """测试长文本压缩"""
        content = "这不仅是一个长文本。这是一个非常长的文本。" * 10
        # 目标比例 0.5, max_length = 40 (约 10 tokens)
        compressed, stats = self.compressor.compress(content, max_length=40)
        
        self.assertLess(len(compressed), len(content))
        self.assertEqual(stats.original_length, len(content))


class TestStructuredCompressor(unittest.TestCase):
    """测试结构化压缩器"""

    def setUp(self):
        self.compressor = StructuredCompressor()

    def test_compress_markdown(self):
        """测试压缩Markdown结构"""
        content = "# Title\n\n## Subtitle\n\n- Item 1\n- Item 2\n\n| Col 1 | Col 2 |\n|---|---|\n| Val 1 | Val 2 |"
        compressed, stats = self.compressor.compress(content)
        
        self.assertIn("# Title", compressed)
        self.assertIn("- Item 1", compressed)
        self.assertIn("| Val 1 | Val 2 |", compressed)


class TestSmartContextCompressor(unittest.TestCase):
    """测试智能上下文压缩器主接口"""

    def setUp(self):
        self.compressor = SmartContextCompressor()

    def test_compress_context(self):
        """测试上下文压缩"""
        content = """
        # 项目计划
        - 任务1: 完成登录功能
        - 任务2: 修复已知Bug
        """
        # 修改方法名从 compress_context 为 compress_for_agent
        compressed, stats = self.compressor.compress_for_agent(content, agent_type="coding")
        self.assertIsInstance(compressed, str)
        self.assertIsInstance(stats, CompressionStats)
        self.assertLessEqual(len(compressed), len(content))


class TestContextCache(unittest.TestCase):
    """测试上下文缓存"""

    def setUp(self):
        self.cache = ContextCache()
        self.compressor = SemanticCompressor()

    def test_cache_hit(self):
        """测试缓存命中"""
        content = "Test content for caching"

        # 第一次压缩
        result1 = self.cache.get_or_compress(
            content,
            self.compressor
        )

        # 第二次应该从缓存获取
        result2 = self.cache.get_or_compress(
            content,
            self.compressor
        )

        # 结果应该相同 (由于是元组，直接比较)
        self.assertEqual(result1[0], result2[0])
        self.assertEqual(len(self.cache.cache), 1)


if __name__ == "__main__":
    unittest.main()
