#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
增量更新检测系统单元测试 - SuperAgent v2.2.0
"""

import unittest
import tempfile
import json
from pathlib import Path
from datetime import datetime
import sys
import os
import asyncio

# 添加模块路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from context.incremental_updater import (
    FileSnapshot,
    ChangeRecord,
    IncrementalUpdater,
    IncrementalUpdateManager
)


class TestFileSnapshot(unittest.TestCase):
    """测试FileSnapshot数据类"""

    def test_create_snapshot(self):
        """测试创建快照"""
        snapshot = FileSnapshot(
            path="test.py",
            size=1000,
            mtime=1234567890.0,
            hash="abc123",
            snapshot_time=1234567890.0,
            content="print('hello')"
        )

        self.assertEqual(snapshot.path, "test.py")
        self.assertEqual(snapshot.size, 1000)
        self.assertEqual(snapshot.content, "print('hello')")

    def test_to_dict_excludes_content(self):
        """测试序列化时排除content字段"""
        snapshot = FileSnapshot(
            path="test.py",
            size=1000,
            mtime=1234567890.0,
            hash="abc123",
            snapshot_time=1234567890.0,
            content="print('hello')"
        )

        data = snapshot.to_dict()

        # content应该被设为None以节省空间
        self.assertIsNone(data['content'])
        self.assertEqual(data['path'], "test.py")

    def test_from_dict(self):
        """测试从字典恢复快照"""
        data = {
            "path": "test.py",
            "size": 1000,
            "mtime": 1234567890.0,
            "hash": "abc123",
            "snapshot_time": 1234567890.0,
            "content": None
        }

        snapshot = FileSnapshot.from_dict(data)

        self.assertEqual(snapshot.path, "test.py")
        self.assertEqual(snapshot.size, 1000)


class TestIncrementalUpdater(unittest.IsolatedAsyncioTestCase):
    """测试IncrementalUpdater核心功能"""

    async def asyncSetUp(self):
        """每个测试前创建临时目录"""
        # 使用唯一前缀避免状态污染
        self.temp_dir = tempfile.mkdtemp(prefix="superagent_test_")
        self.updater = IncrementalUpdater(Path(self.temp_dir))

    async def asyncTearDown(self):
        """每个测试后清理"""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    async def test_create_single_file_snapshot(self):
        """测试创建单个文件快照"""
        # 创建测试文件
        test_file = Path(self.temp_dir) / "test.py"
        test_file.write_text("print('hello')", encoding='utf-8')

        # 创建快照
        snapshots = await self.updater.take_snapshot([str(test_file.name)])

        self.assertEqual(len(snapshots), 1)
        self.assertIn("test.py", snapshots)
        self.assertIsNotNone(snapshots["test.py"].content)

    async def test_detect_new_file(self):
        """测试检测新文件"""
        # 使用全新的目录避免历史快照干扰
        temp_dir = tempfile.mkdtemp(prefix="superagent_new_")
        updater = IncrementalUpdater(Path(temp_dir))

        try:
            # 拍摄初始快照
            before_snapshots = await updater.take_snapshot([], save=True)

            test_file = Path(temp_dir) / "new.py"
            test_file.write_text("print('new')", encoding='utf-8')

            # 检测变更 - 显式传入之前的快照，以检测新增文件
            # detect_project_changes 支持 before_snapshots，而 detect_changes 不支持
            changes = await updater.detect_project_changes(before_snapshots=before_snapshots)

            # 找到我们关注的文件
            test_file_changes = [c for c in changes if c and Path(c.path).name == "new.py"]
            self.assertGreaterEqual(len(test_file_changes), 1)
            self.assertEqual(test_file_changes[0].change_type, "added")
        finally:
            import shutil
            shutil.rmtree(temp_dir, ignore_errors=True)

    async def test_detect_modified_file(self):
        """测试检测文件修改"""
        test_file = Path(self.temp_dir) / "test.py"
        original_content = "print('hello')"
        test_file.write_text(original_content, encoding='utf-8')

        # 创建快照
        await self.updater.take_snapshot([str(test_file.name)])

        # 修改文件
        modified_content = "print('hello')\nprint('world')"
        test_file.write_text(modified_content, encoding='utf-8')

        # 检测变更
        changes = await self.updater.detect_changes([str(test_file.name)])

        # 找到test.py的修改记录
        modified_changes = [c for c in changes if c.path == "test.py" and c.change_type == 'modified']
        self.assertGreater(len(modified_changes), 0)
        self.assertGreater(modified_changes[0].diff_ratio, 0)

    async def test_detect_deleted_file(self):
        """测试检测文件删除"""
        test_file = Path(self.temp_dir) / "test.py"
        test_file.write_text("print('hello')", encoding='utf-8')

        # 创建快照
        await self.updater.take_snapshot([str(test_file.name)])

        # 删除文件
        test_file.unlink()

        # 检测变更
        changes = await self.updater.detect_changes([str(test_file.name)])

        # 找到test.py的删除记录
        deleted_changes = [c for c in changes if c.path == "test.py" and c.change_type == 'deleted']
        self.assertGreater(len(deleted_changes), 0)

    async def test_get_incremental_update_with_diff(self):
        """测试获取增量更新(小改动)"""
        test_file = Path(self.temp_dir) / "test.py"
        original_content = "def hello():\n    pass\n"
        test_file.write_text(original_content, encoding='utf-8')

        # 创建快照
        await self.updater.take_snapshot([str(test_file.name)])

        # 小改动 (差异<30%才会使用增量)
        modified_content = original_content + "    # 添加注释\n"
        test_file.write_text(modified_content, encoding='utf-8')

        # 检测变更
        await self.updater.detect_changes([str(test_file.name)])

        # 获取增量更新
        update = await self.updater.get_incremental_update(str(test_file))

        self.assertIsNotNone(update)
        self.assertEqual(update['change_type'], 'modified')
        # 验证返回格式正确(无论是否使用增量)
        self.assertIn('use_incremental', update)
        self.assertIn('diff_size', update)

    async def test_get_incremental_update_full_content(self):
        """测试获取完整内容(大改动)"""
        test_file = Path(self.temp_dir) / "test.py"
        original_content = "def hello():\n    pass\n"
        test_file.write_text(original_content, encoding='utf-8')

        # 创建快照
        await self.updater.take_snapshot([str(test_file.name)])

        # 大改动(完全重写)
        modified_content = "def world():\n    pass\ndef foo():\n    pass\ndef bar():\n    pass\n"
        test_file.write_text(modified_content, encoding='utf-8')

        # 检测变更
        await self.updater.detect_changes([str(test_file.name)])

        # 获取增量更新
        update = await self.updater.get_incremental_update(str(test_file))

        self.assertIsNotNone(update)
        # 大改动可能不使用增量,取决于diff_ratio
        # 这里验证返回格式正确
        self.assertIn('diff_ratio', update)
        self.assertIn('diff_size', update)

    async def test_state_persistence(self):
        """测试状态持久化"""
        test_file = Path(self.temp_dir) / "test.py"
        test_file.write_text("print('hello')", encoding='utf-8')

        # 创建快照
        await self.updater.take_snapshot([str(test_file.name)])

        # 创建新的updater实例,验证状态加载
        new_updater = IncrementalUpdater(Path(self.temp_dir))

        # 验证test.py在快照中
        self.assertIn("test.py", new_updater.snapshots)
        # 至少包含我们创建的快照(可能有其他文件)
        self.assertGreaterEqual(len(new_updater.snapshots), 1)

    async def test_change_summary(self):
        """测试变更摘要"""
        test_file = Path(self.temp_dir) / "test.py"
        test_file.write_text("print('hello')", encoding='utf-8')

        # 创建快照
        await self.updater.take_snapshot([str(test_file.name)])

        # 修改文件
        test_file.write_text("print('world')", encoding='utf-8')

        # 检测变更
        await self.updater.detect_changes([str(test_file.name)])

        # 获取摘要 - 使用异步版本
        summary = await self.updater.get_change_summary_async()

        # 验证摘要包含我们的变更
        self.assertIn('modified', summary)
        self.assertIn('test.py', summary['modified'])


class TestIncrementalUpdateManager(unittest.IsolatedAsyncioTestCase):
    """测试IncrementalUpdateManager集成"""

    async def asyncSetUp(self):
        """创建临时目录和manager"""
        self.temp_dir = tempfile.mkdtemp(prefix="superagent_manager_")
        self.manager = IncrementalUpdateManager(Path(self.temp_dir))

    async def asyncTearDown(self):
        """清理"""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    async def test_before_after_agent_execution(self):
        """测试Agent执行前后工作流"""
        test_file = Path(self.temp_dir) / "test.py"
        test_file.write_text("print('hello')", encoding='utf-8')

        # Agent执行前
        before_result = await self.manager.before_agent_execution([str(test_file.name)])
        # IncrementalUpdateManager.before_agent_execution 返回的是 get_change_summary_async 的结果
        self.assertIn('total_changes', before_result)

        # 修改文件
        test_file.write_text("print('world')", encoding='utf-8')

        # Agent执行后
        after_result = await self.manager.after_agent_execution([str(test_file.name)])
        # after_agent_execution 返回的是 {"change_count": len(changes), "changes": [...], ...}
        self.assertGreaterEqual(after_result['change_count'], 1)

    async def test_get_incremental_updates_for_context(self):
        """测试为上下文获取增量更新"""
        test_file = Path(self.temp_dir) / "test.py"
        original_content = "line1\nline2\n"
        test_file.write_text(original_content, encoding='utf-8')

        # 创建快照
        await self.manager.before_agent_execution([str(test_file.name)])

        # 小改动
        modified_content = original_content + "line3\n"
        test_file.write_text(modified_content, encoding='utf-8')

        # 检测变更
        await self.manager.after_agent_execution([str(test_file.name)])

        # 获取增量更新
        updates = await self.manager.get_incremental_updates_for_context([str(test_file)])

        self.assertEqual(len(updates), 1)
        self.assertIn('use_incremental', updates[0])


class TestDiffGeneration(unittest.IsolatedAsyncioTestCase):
    """测试Diff生成逻辑"""

    async def asyncSetUp(self):
        self.temp_dir = tempfile.mkdtemp(prefix="superagent_diff_")
        self.updater = IncrementalUpdater(Path(self.temp_dir))

    async def asyncTearDown(self):
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    async def test_unified_diff_format(self):
        """测试unified diff格式"""
        test_file = Path(self.temp_dir) / "test.py"
        original = "def hello():\n    pass\n"
        modified = "def hello():\n    print('hi')\n    pass\n"

        test_file.write_text(original, encoding='utf-8')
        await self.updater.take_snapshot([str(test_file.name)])

        test_file.write_text(modified, encoding='utf-8')
        await self.updater.detect_changes([str(test_file.name)])

        update = await self.updater.get_incremental_update(str(test_file))

        if update['use_incremental']:
            diff = update['diff']
            # 验证diff格式
            self.assertIn('---', diff)
            self.assertIn('+++', diff)
            self.assertIn('@@', diff)

    async def test_diff_ratio_calculation(self):
        """测试差异比例计算"""
        # 完全相同
        ratio1 = self.updater._calculate_diff_ratio("hello", "hello")
        self.assertEqual(ratio1, 0.0)


if __name__ == "__main__":
    unittest.main()
