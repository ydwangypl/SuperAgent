#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
MemoryManager v3 单元测试
"""

import asyncio
import unittest
import tempfile
import shutil
import json
import os
from pathlib import Path
from datetime import datetime

# 添加项目根目录到路径
import sys
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from memory.memory_manager import MemoryManager, MemoryEntry


class TestMemoryManagerV3(unittest.IsolatedAsyncioTestCase):
    """测试 MemoryManager v3 (异步)"""

    async def asyncSetUp(self):
        """每个测试前执行"""
        self.temp_dir = Path(tempfile.mkdtemp())
        # 重置单例以确保测试独立性 (虽然单例很难重置，但在测试中我们可以强制重置 _instance)
        MemoryManager._instance = None
        self.mm = MemoryManager(self.temp_dir)

    async def asyncTearDown(self):
        """每个测试后执行"""
        shutil.rmtree(self.temp_dir, ignore_errors=True)
        MemoryManager._instance = None

    def test_singleton(self):
        """测试单例模式"""
        mm2 = MemoryManager(self.temp_dir)
        self.assertIs(self.mm, mm2)

    def test_init_directories(self):
        """测试目录初始化"""
        self.assertTrue((self.temp_dir / ".superagent" / "memory").exists())
        self.assertTrue((self.temp_dir / ".superagent" / "memory" / "episodic").exists())
        self.assertTrue((self.temp_dir / ".superagent" / "memory" / "semantic").exists())
        self.assertTrue((self.temp_dir / ".superagent" / "memory" / "procedural").exists())
        self.assertTrue((self.temp_dir / ".superagent" / "memory" / "CONTINUITY.md").exists())

    async def test_save_episodic_memory(self):
        """测试保存情节记忆"""
        event = "测试事件"
        memory_id = await self.mm.save_episodic_memory(
            event=event,
            task_id="task-123",
            agent_type="backend-dev"
        )
        
        self.assertTrue(memory_id.startswith("episodic_"))
        
        # 验证文件存在
        file_path = self.temp_dir / ".superagent" / "memory" / "episodic" / f"{memory_id}.json"
        self.assertTrue(file_path.exists())
        
        # 验证内容
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            self.assertEqual(data["content"], event)
            self.assertIn("task:task-123", data["tags"])

    async def test_get_episodic_memories(self):
        """测试获取情节记忆"""
        await self.mm.save_episodic_memory("事件1")
        await self.mm.save_episodic_memory("事件2")
        
        memories = await self.mm.get_episodic_memories(limit=5)
        self.assertEqual(len(memories), 2)
        self.assertEqual(memories[0]["content"], "事件2") # 最近的在前

    async def test_save_semantic_memory(self):
        """测试保存语义记忆"""
        knowledge = "这是一个架构决策"
        category = "architecture"
        memory_id = await self.mm.save_semantic_memory(knowledge, category)
        
        self.assertTrue(memory_id.startswith("semantic_"))
        
        # 验证索引更新
        self.assertIn(memory_id, self.mm.index["semantic"])
        
        # 验证CONTINUITY.md更新
        content = (self.temp_dir / ".superagent" / "memory" / "CONTINUITY.md").read_text(encoding='utf-8')
        self.assertIn(knowledge, content)

    async def test_query_semantic_memory(self):
        """测试查询语义记忆"""
        await self.mm.save_semantic_memory("知识1", "tech")
        await self.mm.save_semantic_memory("架构1", "arch")
        
        # 按分类查询
        tech_mems = await self.mm.query_semantic_memory(category="tech")
        self.assertEqual(len(tech_mems), 1)
        self.assertEqual(tech_mems[0]["content"], "知识1")
        
        # 按关键词查询
        arch_mems = await self.mm.query_semantic_memory(keywords=["架构"])
        self.assertEqual(len(arch_mems), 1)
        self.assertEqual(arch_mems[0]["content"], "架构1")

    async def test_save_procedural_memory(self):
        """测试保存程序记忆"""
        practice = "这是一个最佳实践"
        category = "workflow"
        memory_id = await self.mm.save_procedural_memory(practice, category)
        
        self.assertTrue(memory_id.startswith("procedural_"))
        
        # 验证CONTINUITY.md更新
        content = (self.temp_dir / ".superagent" / "memory" / "CONTINUITY.md").read_text(encoding='utf-8')
        self.assertIn(practice, content)

    async def test_index_persistence(self):
        """测试索引持久化"""
        await self.mm.save_episodic_memory("测试持久化")
        
        # 验证索引文件存在
        index_file = self.temp_dir / ".superagent" / "memory" / "memory_index.json"
        self.assertTrue(index_file.exists())
        
        # 创建新的实例加载索引
        MemoryManager._instance = None
        mm_new = MemoryManager(self.temp_dir)
        self.assertEqual(mm_new.index["total_count"], 1)


if __name__ == '__main__':
    unittest.main()
