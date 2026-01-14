#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
TokenMonitor Tests
"""

import sys
import unittest
import asyncio
from pathlib import Path
import tempfile
import os

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from monitoring.token_monitor import (
    TokenMonitor,
    TokenMonitorConfig,
    TokenUsageRecord
)


class TestTokenMonitor(unittest.IsolatedAsyncioTestCase):
    """Token使用监控器测试类"""

    async def asyncSetUp(self):
        self.tmpdir = tempfile.TemporaryDirectory()
        self.project_root = Path(self.tmpdir.name)
        self.monitor = TokenMonitor(
            project_root=self.project_root,
            config=TokenMonitorConfig(enabled=True)
        )

    async def asyncTearDown(self):
        self.tmpdir.cleanup()

    async def test_log_usage(self):
        """测试记录Token使用情况"""
        print("\n" + "=" * 60)
        print("Test 1: Log Token Usage")
        print("=" * 60)

        # Log usage
        record = await self.monitor.log_usage(
            agent_type="coding",
            task_id="test-001",
            original_tokens=10000,
            compressed_tokens=5000,
            incremental_tokens=1000,
            files_processed=5,
            files_incremental=2,
            compression_method="semantic"
        )

        print(f"Agent type: {record.agent_type}")
        print(f"Task ID: {record.task_id}")
        print(f"Original tokens: {record.original_tokens}")
        print(f"Compressed tokens: {record.compressed_tokens}")
        print(f"Compression ratio: {record.compression_ratio * 100:.1f}%")
        print(f"Savings ratio: {record.savings_ratio * 100:.1f}%")

        # Verify results
        self.assertIsNotNone(record, "Record should not be None")
        self.assertEqual(record.agent_type, "coding", "Agent type should be correct")
        self.assertEqual(record.original_tokens, 10000, "Original tokens should be correct")
        self.assertEqual(record.compression_ratio, 0.5, "Compression ratio should be 0.5")

        print("\n[PASS] Log token usage test passed!")

    async def test_get_records(self):
        """测试获取记录"""
        print("\n" + "=" * 60)
        print("Test 2: Get Records")
        print("=" * 60)

        # Log multiple records
        await self.monitor.log_usage("coding", "task-1", 10000, 5000, 1000, 5, 2, "semantic")
        await self.monitor.log_usage("backend-dev", "task-2", 8000, 3200, 800, 3, 1, "structured")
        await self.monitor.log_usage("frontend-dev", "task-3", 6000, 3000, 500, 2, 1, "auto")

        # Get all records
        records = await self.monitor.get_records(days=7)
        print(f"Total records: {len(records)}")

        # Verify results
        self.assertEqual(len(records), 3, "Should have 3 records")

        # Filter by agent type
        coding_records = await self.monitor.get_records(days=7, agent_type="coding")
        print(f"Coding agent records: {len(coding_records)}")
        self.assertEqual(len(coding_records), 1, "Should have 1 coding record")

        print("\n[PASS] Get records test passed!")

    async def test_get_summary(self):
        """测试获取摘要"""
        print("\n" + "=" * 60)
        print("Test 3: Get Summary")
        print("=" * 60)

        # Log multiple records
        await self.monitor.log_usage("coding", "task-1", 10000, 5000, 1000, 5, 2, "semantic")
        await self.monitor.log_usage("backend-dev", "task-2", 8000, 3200, 800, 3, 1, "structured")

        # Get summary
        summary = await self.monitor.get_summary(days=7)

        print(f"Period days: {summary['period_days']}")
        print(f"Total tasks: {summary['total_tasks']}")
        print(f"Total original tokens: {summary['total_original_tokens']}")
        print(f"Total compressed tokens: {summary['total_compressed_tokens']}")
        print(f"Total savings: {summary['total_savings']}")
        print(f"Overall savings ratio: {summary['overall_savings_ratio'] * 100:.1f}%")

        # Verify results
        self.assertEqual(summary["total_tasks"], 2, "Should have 2 tasks")
        self.assertEqual(summary["total_original_tokens"], 18000, "Original tokens should sum to 18000")
        self.assertEqual(summary["total_compressed_tokens"], 8200, "Compressed tokens should sum to 8200")
        self.assertGreater(summary["overall_savings_ratio"], 0, "Savings ratio should be positive")

        print("\n[PASS] Get summary test passed!")

    async def test_generate_report(self):
        """测试生成报告"""
        print("\n" + "=" * 60)
        print("Test 4: Generate Report")
        print("=" * 60)

        # Log some records
        await self.monitor.log_usage("coding", "task-1", 10000, 5000, 1000, 5, 2, "semantic")
        await self.monitor.log_usage("backend-dev", "task-2", 8000, 3200, 800, 3, 1, "structured")

        # Generate report
        report = await self.monitor.generate_report(days=7)

        print("Report preview:")
        print(report[:500] + "...")

        # Verify results
        self.assertTrue("Token" in report or "Token" in report, "Report should contain token info")
        self.assertTrue("tasks" in report or "任务" in report, "Report should contain tasks info")
        self.assertTrue("savings" in report or "节省" in report, "Report should contain savings info")

        print("\n[PASS] Generate report test passed!")

    async def test_get_daily_stats(self):
        """测试获取每日统计"""
        print("\n" + "=" * 60)
        print("Test 5: Get Daily Stats")
        print("=" * 60)

        # Log some records
        await self.monitor.log_usage("coding", "task-1", 10000, 5000, 1000, 5, 2, "semantic")
        await self.monitor.log_usage("backend-dev", "task-2", 8000, 3200, 800, 3, 1, "structured")

        # Get daily stats
        daily_stats = await self.monitor.get_daily_stats(days=7)

        print(f"Days with activity: {len(daily_stats)}")
        for date, stats in daily_stats.items():
            print(f"  {date}: {stats['tasks']} tasks, {stats['original_tokens']} original, {stats['compressed_tokens']} compressed")

        # Verify results
        self.assertGreaterEqual(len(daily_stats), 1, "Should have at least 1 day with activity")

        print("\n[PASS] Get daily stats test passed!")

    async def test_get_trend(self):
        """测试获取趋势数据"""
        print("\n" + "=" * 60)
        print("Test 6: Get Trend")
        print("=" * 60)

        # Log some records
        await self.monitor.log_usage("coding", "task-1", 10000, 5000, 1000, 5, 2, "semantic")
        await self.monitor.log_usage("backend-dev", "task-2", 8000, 3200, 800, 3, 1, "structured")

        # Get trend
        trend_data = await self.monitor.get_trend(days=7)
        trend = trend_data["trend"]

        print(f"Trend data points: {len(trend)}")
        for point in trend:
            print(f"  {point['date']}: {point['original']} original")

        # Verify results
        self.assertGreaterEqual(len(trend), 1, "Should have at least 1 data point")
        self.assertIn("avg_savings", trend_data, "Should have avg_savings in trend data")

        print("\n[PASS] Get trend test passed!")


if __name__ == "__main__":
    unittest.main()
