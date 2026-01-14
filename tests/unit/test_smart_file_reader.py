#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
SmartFileReader Tests
"""

import sys
import unittest
import asyncio
from pathlib import Path
import tempfile
import os

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from utils.smart_file_reader import (
    SmartFileReader,
    FileReadStats
)


class TestSmartFileReader(unittest.IsolatedAsyncioTestCase):
    """智能文件读取器测试类"""

    async def asyncSetUp(self):
        self.reader = SmartFileReader()
        self.tmpdir = tempfile.TemporaryDirectory()
        self.tmp_path = Path(self.tmpdir.name)

    async def asyncTearDown(self):
        self.tmpdir.cleanup()

    async def test_small_file_full_read(self):
        """测试小文件全量读取"""
        print("\n" + "=" * 60)
        print("Test 1: Small File Full Read (<10KB)")
        print("=" * 60)

        # Create small test file
        test_file = self.tmp_path / "small_file.txt"
        content = '\n'.join([f"Line {i}" for i in range(100)])
        test_file.write_text(content)

        # Read in auto mode
        result, stats = await self.reader.read(test_file, mode="auto")

        print(f"File size: {stats.file_size} bytes")
        print(f"Read mode: {stats.read_mode}")
        print(f"Lines total: {stats.lines_total}")
        print(f"Lines read: {stats.lines_read}")
        print(f"Compression ratio: {stats.compression_ratio * 100:.1f}%")

        # Verify results
        self.assertEqual(stats.read_mode, "full", "Small file should be read fully")
        self.assertEqual(stats.lines_total, stats.lines_read, "All lines should be read")
        self.assertEqual(stats.compression_ratio, 1.0, "Compression ratio should be 100%")

        print("\n[PASS] Small file full read test passed!")

    async def test_large_file_summary(self):
        """测试大文件摘要读取"""
        print("\n" + "=" * 60)
        print("Test 2: Large File Summary Read (>=10KB)")
        print("=" * 60)

        # Create large test file (more than 10KB)
        test_file = self.tmp_path / "large_file.txt"
        lines = [f"This is line {i} with some content to make the file larger" for i in range(500)]
        content = '\n'.join(lines)
        test_file.write_text(content)

        print(f"File size: {test_file.stat().st_size} bytes")

        # Read in auto mode
        result, stats = await self.reader.read(test_file, mode="auto")

        print(f"Read mode: {stats.read_mode}")
        print(f"Lines total: {stats.lines_total}")
        print(f"Lines read: {stats.lines_read}")
        print(f"Compression ratio: {stats.compression_ratio * 100:.1f}%")

        # Verify results
        self.assertEqual(stats.read_mode, "summary", "Large file should use summary mode")
        self.assertLess(stats.lines_read, stats.lines_total, "Only some lines should be read")
        self.assertLess(stats.compression_ratio, 1.0, "Compression ratio should be less than 100%")

        # Verify content structure
        self.assertTrue("... (省略" in result or "... (skipped" in result or "..." in result, "Should contain summary marker")
        self.assertTrue("This is line 0" in result, "Should contain first line")
        self.assertTrue("This is line 499" in result.replace('\r\n', '\n'), "Should contain last line")

        print("\n[PASS] Large file summary read test passed!")

    async def test_force_full_mode(self):
        """测试强制全量读取模式"""
        print("\n" + "=" * 60)
        print("Test 3: Force Full Read Mode")
        print("=" * 60)

        # Create test file
        test_file = self.tmp_path / "test_file.txt"
        lines = [f"Line {i}" for i in range(100)]
        content = '\n'.join(lines)
        test_file.write_text(content)

        # Force full read
        result, stats = await self.reader.read(test_file, mode="full")

        self.assertEqual(stats.read_mode, "full")
        self.assertEqual(stats.lines_total, 100)

        print("\n[PASS] Force full read mode test passed!")

    async def test_force_summary_mode(self):
        """测试强制摘要模式"""
        print("\n" + "=" * 60)
        print("Test 4: Force Summary Read Mode")
        print("=" * 60)

        # Create test file
        test_file = self.tmp_path / "test_file.txt"
        lines = [f"Line {i}" for i in range(100)]
        content = '\n'.join(lines)
        test_file.write_text(content)

        # Force summary read
        result, stats = await self.reader.read(test_file, mode="summary")

        self.assertEqual(stats.read_mode, "summary")
        self.assertLess(stats.lines_read, stats.lines_total)

        print("\n[PASS] Force summary read mode test passed!")

    async def test_skip_mode(self):
        """测试跳过模式"""
        print("\n" + "=" * 60)
        print("Test 5: Skip Read Mode")
        print("=" * 60)

        # Create test file
        test_file = self.tmp_path / "test_file.txt"
        test_file.write_text("Some content")

        # Skip read
        result, stats = await self.reader.read(test_file, mode="skip")

        self.assertEqual(result, "")
        self.assertEqual(stats.read_mode, "skipped")

        print("\n[PASS] Skip read mode test passed!")

    async def test_read_multiple_files(self):
        """测试读取多个文件"""
        print("\n" + "=" * 60)
        print("Test 6: Read Multiple Files")
        print("=" * 60)

        # Create multiple files
        files = []
        for i in range(3):
            f = self.tmp_path / f"file_{i}.txt"
            f.write_text(f"Content of file {i}")
            files.append(f)

        # Read each
        results = []
        for f in files:
            res, stat = await self.reader.read(f)
            results.append(res)

        self.assertEqual(len(results), 3)
        self.assertEqual(results[0], "Content of file 0")

        print("\n[PASS] Read multiple files test passed!")

    async def test_get_summary_stats(self):
        """测试获取统计摘要"""
        print("\n" + "=" * 60)
        print("Test 7: Get Summary Statistics")
        print("=" * 60)

        # Create a small and a large file
        small_file = self.tmp_path / "small.txt"
        small_file.write_text("Small content")

        large_file = self.tmp_path / "large.txt"
        large_content = "Large content " * 1000
        large_file.write_text(large_content)

        # Read both
        await self.reader.read(small_file)
        await self.reader.read(large_file)

        # Get stats
        stats_list = self.reader.get_read_summary()
        print(f"Small file size: {stats_list[0]['file_size']}")
        print(f"Large file size: {stats_list[1]['file_size']}")

        self.assertEqual(len(stats_list), 2)
        self.assertEqual(stats_list[0]['read_mode'], "full")
        self.assertEqual(stats_list[1]['read_mode'], "summary")

        print("\n[PASS] Get summary statistics test passed!")

    async def test_file_not_found(self):
        """测试文件不存在错误"""
        print("\n" + "=" * 60)
        print("Test 8: File Not Found Error")
        print("=" * 60)

        non_existent = self.tmp_path / "non_existent.txt"

        with self.assertRaises(FileNotFoundError):
            await self.reader.read(non_existent)

        print("\n[PASS] File not found error test passed!")


if __name__ == "__main__":
    unittest.main()
