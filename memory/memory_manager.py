#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
记忆管理器

实现3层记忆系统,防止重复错误,加速项目开发
"""

import asyncio
import threading  # v3.3 优化：使用线程锁保护单例
import logging
import time
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field
import json
import uuid
import aiofiles
from common.monitoring import MetricsManager
from common.exceptions import MemorySystemError
from config.constants import Defaults  # P2: 使用常量替代魔法数字

logger = logging.getLogger(__name__)

# 常量定义
SECTION_MISTAKES = "## 📝 错误与教训"
SECTION_PRACTICES = "## 🎯 最佳实践"
SECTION_ARCHITECTURE = "## 🏗️ 架构决策"
SECTION_STATISTICS = "## 📊 项目统计"


@dataclass
class MemoryEntry:
    """记忆条目"""
    memory_id: str
    memory_type: str  # episodic, semantic, procedural
    timestamp: str
    content: str
    metadata: Dict[str, Any] = field(default_factory=dict)
    tags: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "memory_id": self.memory_id,
            "memory_type": self.memory_type,
            "timestamp": self.timestamp,
            "content": self.content,
            "metadata": self.metadata,
            "tags": self.tags
        }


class MemoryManager:
    """记忆管理器 - 实现3层记忆系统 (单例异步版 v3.4 优化)"""

    _instance: Optional['MemoryManager'] = None
    _class_lock = threading.Lock()  # 线程锁保护单例创建

    def __new__(cls, *args, **kwargs) -> 'MemoryManager':
        # 使用锁保护单例创建
        with cls._class_lock:
            if not cls._instance:
                cls._instance = super(MemoryManager, cls).__new__(cls)
            return cls._instance

    def __init__(self, project_root: Optional[Path] = None) -> None:
        """初始化记忆管理器

        Args:
            project_root: 项目根目录
        """
        # 防止重复初始化
        if getattr(self, '_initialized', False):
            # 如果已经初始化但 project_root 不同，只更新路径
            if project_root is not None and self.project_root != Path(project_root):
                self.project_root = Path(project_root)
            return

        self.project_root = project_root or Path.cwd()

        # 配置各层记忆的存储路径
        self.memory_dir = self.project_root / ".superagent" / "memory"
        self.episodic_dir = self.memory_dir / "episodic"
        self.semantic_dir = self.memory_dir / "semantic"
        self.procedural_dir = self.memory_dir / "procedural"

        # 持续记忆文件
        self.continuity_file = self.memory_dir / "CONTINUITY.md"

        # 索引文件
        self.index_file = self.memory_dir / "memory_index.json"

        # 锁
        self._lock = asyncio.Lock()  # 内存状态锁
        self._io_lock = asyncio.Lock()  # 文件写入锁 (防止并发写入同一文件)
        self._cache_lock = threading.Lock()  # 缓存操作锁（使用线程锁，因为方法是同步的）

        # 创建目录结构
        self._init_directories()

        # 加载索引
        self.index: Dict[str, Any] = self._load_index_sync()

        # 初始化查询缓存 (使用 LRU + LFU 混合策略)
        # 缓存结构: {type: {memory_id: (entry_dict, access_count, last_access_time)}}
        self._cache: Dict[str, Dict[str, tuple[Dict[str, Any], int, float]]] = {
            "episodic": {},
            "semantic": {},
            "procedural": {}
        }
        # 类别索引 (type -> category -> list of memory_ids)
        self._category_index: Dict[str, Dict[str, List[str]]] = {
            "semantic": {},
            "procedural": {}
        }
        self._cache_ttl = Defaults.CACHE_TTL.value  # 使用常量
        self._max_cache_size = Defaults.MAX_CACHE_SIZE.value  # 使用常量
        self._continuity_cache: Optional[str] = None  # CONTINUITY.md 内容缓存
        self._last_flush_time: float = 0.0

        # 标记初始化完成
        self._initialized = True
        self._index_building = False
        self._index_task = None
        self._index_ready = asyncio.Event()  # P0 Fix: 初始化索引就绪事件
        self._index_ready.set()  # 初始状态下索引已完成

        logger.info(f"记忆管理器初始化完成: {self.memory_dir}")

    @classmethod
    def get_instance(cls, project_root: Optional[Path] = None) -> 'MemoryManager':
        """获取单例，支持延迟初始化

        Args:
            project_root: 项目根目录（仅在首次创建时有效）

        Returns:
            MemoryManager 单例
        """
        if not cls._instance:
            with cls._class_lock:
                if not cls._instance:
                    instance = cls(project_root)
                    cls._instance = instance
        return cls._instance

    async def initialize_async(self, project_root: Optional[Path] = None) -> None:
        """异步初始化（可选，用于需要异步初始化的场景）

        P0 Fix: 使用异步锁避免线程/异步锁混用导致的死锁
        Args:
            project_root: 项目根目录
        """
        async with self._lock:
            if not self._index_building:
                self._index_building = True
                self._index_task = asyncio.create_task(self._build_category_index())

    async def wait_for_index(self, timeout: float = 30.0) -> bool:
        """等待类别索引构建完成

        Args:
            timeout: 超时时间（秒）

        Returns:
            是否在超时前完成
        """
        if not self._index_building:
            return True  # 已经完成

        if self._index_task is None:
            return True

        try:
            await asyncio.wait_for(self._index_task, timeout=timeout)
            return True
        except asyncio.TimeoutError:
            logger.warning("等待类别索引构建超时")
            return False

    async def _build_category_index(self) -> None:
        """异步构建类别索引 (v3.3 优化版：IO不在锁内 + 完成通知)"""
        try:
            for mtype in ["semantic", "procedural"]:
                # 1. 先在不占锁的情况下收集所有 ID
                async with self._lock:
                    mids = list(self.index.get(mtype, []))

                for mid in mids:
                    try:
                        folder = (self.semantic_dir if mtype == "semantic"
                                  else self.procedural_dir)
                        file_path = folder / f"{mid}.json"

                        if file_path.exists():
                            # 2. 读取文件 (IO)
                            async with aiofiles.open(file_path, 'r', encoding='utf-8') as f:
                                content = await f.read()
                                memory_data = json.loads(content)
                                category = memory_data.get("metadata", {}).get(
                                    "category", "general"
                                )

                                # 3. 更新内存中的索引 (占锁)
                                async with self._lock:
                                    if category not in self._category_index[mtype]:
                                        self._category_index[mtype][category] = []
                                    if mid not in self._category_index[mtype][category]:
                                        self._category_index[mtype][category].append(mid)
                    except (FileNotFoundError, json.JSONDecodeError, PermissionError) as e:
                        logger.error(f"构建类别索引失败 - 文件损坏或丢失 ({mid}): {e}")
                    except (OSError, IOError) as e:
                        logger.error(f"构建类别索引失败 - IO错误 ({mid}): {e}")
                    except Exception as e:
                        logger.error(f"构建类别索引失败 - 未知错误 ({type(e).__name__}) ({mid}): {e}")
        finally:
            # v3.3: 通知索引构建完成
            self._index_building = False
            self._index_ready.set()
            logger.info("类别索引构建完成")

    def _init_directories(self) -> None:
        """初始化目录结构"""
        for d in [self.memory_dir, self.episodic_dir, self.semantic_dir, self.procedural_dir]:
            d.mkdir(parents=True, exist_ok=True)

        # 初始化CONTINUITY.md(如果不存在)
        if not self.continuity_file.exists():
            self._init_continuity_file_sync()

    def _generate_id(self, prefix: str) -> str:
        """生成唯一的记忆ID"""
        return f"{prefix}_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:8]}"

    def _init_continuity_file_sync(self) -> None:
        content = f"""# SuperAgent v3.2 - 持续记忆 (CONTINUITY)

> 此文件由SuperAgent自动维护,记录项目开发过程中的重要经验、错误教训和最佳实践

---

## 📝 错误与教训 (Mistakes & Learnings)

---

## 🎯 最佳实践 (Best Practices)

---

## 🏗️ 架构决策 (Architecture Decisions)

---

## 📊 项目统计 (Project Statistics)

- **总记忆条目**: 0
- **情节记忆**: 0
- **语义记忆**: 0
- **程序记忆**: 0
- **最后更新**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
"""
        self.continuity_file.write_text(content, encoding='utf-8')

    def _load_index_sync(self) -> Dict[str, Any]:
        """同步加载记忆索引, 增加容错逻辑"""
        default_index = {
            "episodic": [],
            "semantic": [],
            "procedural": [],
            "total_count": 0
        }

        if not self.index_file.exists():
            return default_index

        try:
            with open(self.index_file, 'r', encoding='utf-8') as f:
                content = f.read()
                if not content.strip():
                    return default_index
                return json.loads(content)
        except (json.JSONDecodeError, IOError) as e:
            logger.error(f"加载记忆索引失败, 文件可能已损坏: {e}。正在创建新索引。")
            # 备份损坏的文件
            try:
                import shutil
                backup_path = self.index_file.with_suffix('.bak')
                shutil.copy2(self.index_file, backup_path)
                logger.info(f"已将损坏的索引备份至: {backup_path}")
            except (shutil.Error, OSError) as e:
                logger.warning(f"备份损坏的索引文件失败: {e}")
            return default_index

    def _get_from_cache(self, memory_type: str, memory_id: str) -> Optional[Dict[str, Any]]:
        """从缓存获取记忆条目 (v3.3 LRU + LFU 混合策略)

        Args:
            memory_type: 记忆类型
            memory_id: 记忆 ID

        Returns:
            缓存的条目或 None
        """
        if memory_type not in self._cache:
            return None

        # v3.3 优化：使用线程锁保护，确保原子性
        with self._cache_lock:
            cached_entry_data = self._cache[memory_type].get(memory_id)
            if not cached_entry_data:
                return None

            entry, access_count, timestamp = cached_entry_data
            if time.time() - timestamp > self._cache_ttl:
                del self._cache[memory_type][memory_id]
                return None

            # 访问时更新 LFU 计数和 LRU 时间戳 (原子操作)
            self._cache[memory_type][memory_id] = (entry, access_count + 1, time.time())
            return entry

    def _save_to_cache(self, memory_type: str, memory_id: str, entry: Dict[str, Any]) -> None:
        """保存记忆条目到缓存 (v3.3 LRU + LFU 混合淘汰策略)"""
        if memory_type not in self._cache:
            return

        # v3.3 优化：使用线程锁保护
        with self._cache_lock:
            # 当缓存满时，使用 LFU + LRU 混合策略淘汰
            # 优先淘汰访问频率低的条目，频率相同时淘汰最久未访问的
            if len(self._cache[memory_type]) >= self._max_cache_size:
                candidates = []
                for mid, (_entry, count, ts) in self._cache[memory_type].items():
                    candidates.append((mid, count, ts))

                # 找出访问频率最低的条目（保留至少访问过一次的）
                min_count = min(c[1] for c in candidates) if candidates else 0
                low_freq_items = [c for c in candidates if c[1] == min_count]

                # 从低频条目中找出最久未访问的
                oldest = min(low_freq_items, key=lambda c: c[2])
                del self._cache[memory_type][oldest[0]]
                logger.debug(f"缓存淘汰: {oldest[0]} (访问次数: {oldest[1]})")

            # 保存新条目 (access_count=0 表示刚添加)
            self._cache[memory_type][memory_id] = (entry, 0, time.time())

    def _clean_expired_cache(self) -> None:
        """清理过期缓存 (v3.3 优化)"""
        now = time.time()
        cleaned = 0
        for memory_type in self._cache:
            with self._cache_lock:
                expired_keys = [
                    k for k, (_entry, _count, t) in self._cache[memory_type].items()
                    if now - t > self._cache_ttl
                ]
                for k in expired_keys:
                    del self._cache[memory_type][k]
                    cleaned += 1

        if cleaned > 0:
            logger.debug(f"清理过期缓存: {cleaned} 个条目")

    async def _save_index(self) -> None:
        """异步保存记忆索引 (带 IO 锁保护)"""
        try:
            # 1. 先准备要写入的内容 (内存操作)
            async with self._lock:
                content = json.dumps(self.index, indent=2, ensure_ascii=False)

            # 2. 获取 IO 锁并写入文件
            async with self._io_lock:
                # 使用原子写入：先写临时文件再重命名
                temp_file = self.index_file.with_suffix('.tmp')
                async with aiofiles.open(temp_file, 'w', encoding='utf-8') as f:
                    await f.write(content)

                # Windows 下 replace 前如果目标文件存在需要处理，但 Path.replace 应该可以处理
                temp_file.replace(self.index_file)

        except (OSError, IOError) as e:
            logger.error(f"保存记忆索引失败 (IO错误): {e}")
            raise MemorySystemError(f"保存记忆索引失败 (IO错误): {str(e)}")
        except (TypeError, ValueError) as e:
            logger.error(f"保存记忆索引失败 (序列化错误): {e}")
            raise MemorySystemError(f"保存记忆索引失败 (序列化错误): {str(e)}")
        except Exception as e:
            logger.error(f"保存记忆索引遇到未知错误 ({type(e).__name__}): {e}")
            raise MemorySystemError(
                f"保存记忆索引遇到未知错误 ({type(e).__name__}): {str(e)}"
            )

    async def _save_entry(self, entry: MemoryEntry, directory: Path) -> None:
        """通用条目保存方法 (已优化：剥离 IO 锁)"""
        try:
            file_path = directory / f"{entry.memory_id}.json"
            entry_dict = entry.to_dict()

            # 1. 先写条目文件 (不占锁)
            async with aiofiles.open(file_path, 'w', encoding='utf-8') as f:
                await f.write(json.dumps(entry_dict, indent=2, ensure_ascii=False))

            # 2. 更新缓存和内存索引 (占锁)
            async with self._lock:
                # 保存到缓存
                self._save_to_cache(entry.memory_type, entry.memory_id, entry_dict)

                # 更新索引列表
                if entry.memory_id not in self.index[entry.memory_type]:
                    self.index[entry.memory_type].append(entry.memory_id)
                    self.index["total_count"] += 1

                # 更新类别索引
                if entry.memory_type in self._category_index:
                    category = entry.metadata.get("category", "general")
                    if category not in self._category_index[entry.memory_type]:
                        self._category_index[entry.memory_type][category] = []
                    if entry.memory_id not in \
                            self._category_index[entry.memory_type][category]:
                        self._category_index[entry.memory_type][category].append(
                            entry.memory_id
                        )

            # 3. 异步保存索引文件 (IO 密集，移出主锁)
            await self._save_index()

            # 4. 更新监控指标
            MetricsManager.record_memory_op(entry.memory_type, "save", "success")
            # 此时访问 self.index 需要注意并发，但在 record 这种非关键操作中通常 OK
            MetricsManager.update_memory_size(
                entry.memory_type,
                len(self.index[entry.memory_type])
            )

        except (OSError, IOError, PermissionError) as e:
            logger.error(f"保存记忆条目失败 (文件或磁盘错误): {e}")
            MetricsManager.record_memory_op(entry.memory_type, "save", "error")
            raise MemorySystemError(f"保存记忆条目失败 (IO错误): {str(e)}")
        except MemorySystemError:
            MetricsManager.record_memory_op(entry.memory_type, "save", "error")
            raise
        except Exception as e:
            logger.error(f"保存记忆条目失败 (未知错误 - {type(e).__name__}): {e}")
            MetricsManager.record_memory_op(entry.memory_type, "save", "error")
            raise MemorySystemError(
                f"保存记忆条目遇到未知错误 ({type(e).__name__}): {str(e)}"
            )

    # ========== Episodic Memory (情节记忆) ==========

    async def save_episodic_memory(
        self,
        event: str,
        task_id: Optional[str] = None,
        agent_type: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """保存情节记忆 - 记录任务执行历史"""
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        memory_id = self._generate_id("episodic")

        entry = MemoryEntry(
            memory_id=memory_id,
            memory_type="episodic",
            timestamp=timestamp,
            content=event,
            metadata=metadata or {},
            tags=["episodic"]
        )

        if task_id:
            entry.tags.append(f"task:{task_id}")
        if agent_type:
            entry.tags.append(f"agent:{agent_type}")

        await self._save_entry(entry, self.episodic_dir)

        logger.info(f"保存情节记忆: {memory_id}")
        return memory_id

    async def store_memory(
        self,
        content: str,
        memory_type: str = "episodic",
        metadata: Optional[Dict] = None
    ) -> str:
        """存储记忆 (通用包装器)"""
        if memory_type == "episodic":
            return await self.save_episodic_memory(event=content, metadata=metadata)
        elif memory_type == "semantic":
            category = metadata.get("category", "general") if metadata else "general"
            return await self.save_semantic_memory(
                knowledge=content,
                category=category,
                metadata=metadata
            )
        elif memory_type == "procedural":
            category = metadata.get("category", "general") if metadata else "general"
            return await self.save_procedural_memory(
                practice=content,
                category=category,
                metadata=metadata
            )
        else:
            raise MemorySystemError(f"不支持的记忆类型: {memory_type}")

    async def get_episodic_memories(
        self,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """获取最近的情节记忆"""
        MetricsManager.record_memory_op("episodic", "query", "start")
        memories = []
        recent_ids = self.index.get("episodic", [])[-limit:]

        self._clean_expired_cache()

        for memory_id in reversed(recent_ids):
            # 尝试从缓存获取
            cached_entry = self._get_from_cache("episodic", memory_id)
            if cached_entry:
                memories.append(cached_entry)
                continue

            file_path = self.episodic_dir / f"{memory_id}.json"
            if file_path.exists():
                async with aiofiles.open(file_path, 'r', encoding='utf-8') as f:
                    content = await f.read()
                    entry = json.loads(content)
                    memories.append(entry)
                    # 保存到缓存
                    self._save_to_cache("episodic", memory_id, entry)

        return memories

    # ========== Semantic Memory (语义记忆) ==========

    async def save_semantic_memory(
        self,
        knowledge: str,
        category: str,
        tags: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """保存语义记忆 - 记录项目知识和架构决策"""
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        memory_id = self._generate_id(f"semantic_{category}")

        # 基础元数据
        base_metadata = {"category": category}
        if metadata:
            base_metadata.update(metadata)

        entry = MemoryEntry(
            memory_id=memory_id,
            memory_type="semantic",
            timestamp=timestamp,
            content=knowledge,
            metadata=base_metadata,
            tags=["semantic", category] + (tags or [])
        )

        await self._save_entry(entry, self.semantic_dir)

        # 更新CONTINUITY.md
        await self._append_to_continuity("semantic", knowledge, category)

        logger.info(f"保存语义记忆: {memory_id} (分类: {category})")
        return memory_id

    async def query_semantic_memory(
        self,
        category: Optional[str] = None,
        keywords: Optional[List[str]] = None
    ) -> List[Dict[str, Any]]:
        """查询语义记忆 (利用索引优化版)"""
        MetricsManager.record_memory_op("semantic", "query", "start")
        memories = []

        # 获取待查 memory_ids
        if category:
            # 如果指定了类别，直接从类别索引获取 ID
            target_ids = self._category_index["semantic"].get(category, [])
        else:
            # 否则获取所有语义记忆 ID
            target_ids = self.index.get("semantic", [])

        self._clean_expired_cache()

        # 批量加载和过滤
        for memory_id in target_ids:
            # 尝试从缓存获取
            entry = self._get_from_cache("semantic", memory_id)

            if not entry:
                file_path = self.semantic_dir / f"{memory_id}.json"
                if not file_path.exists():
                    continue

                try:
                    async with aiofiles.open(file_path, 'r', encoding='utf-8') as f:
                        content = await f.read()
                        entry = json.loads(content)
                        # 保存到缓存
                        self._save_to_cache("semantic", memory_id, entry)
                except (FileNotFoundError, json.JSONDecodeError, UnicodeDecodeError) as e:
                    logger.error(f"加载记忆文件失败 (文件损坏或编码错误) {memory_id}: {e}")
                    continue
                except (OSError, IOError) as e:
                    logger.error(f"加载记忆文件失败 (系统IO错误) {memory_id}: {e}")
                    continue
                except Exception as e:
                    logger.error(f"加载记忆文件遇到非预期错误 ({type(e).__name__}) {memory_id}: {e}")
                    continue

            # 关键词过滤
            if keywords:
                content_text = entry.get("content", "").lower()
                if not any(kw.lower() in content_text for kw in keywords):
                    continue

            memories.append(entry)

        return memories

    # ========== Procedural Memory (程序记忆) ==========

    async def save_procedural_memory(
        self,
        practice: str,
        category: str,
        agent_type: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """保存程序记忆 - 存储最佳实践和工作流程"""
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        memory_id = self._generate_id(f"procedural_{category}")

        # 基础元数据
        base_metadata = {"category": category}
        if agent_type:
            base_metadata["agent_type"] = agent_type
        if metadata:
            base_metadata.update(metadata)

        entry = MemoryEntry(
            memory_id=memory_id,
            memory_type="procedural",
            timestamp=timestamp,
            content=practice,
            metadata=base_metadata,
            tags=["procedural", category]
        )

        if agent_type:
            entry.tags.append(f"agent:{agent_type}")

        await self._save_entry(entry, self.procedural_dir)

        # 更新CONTINUITY.md
        await self._append_to_continuity("procedural", practice, category)

        logger.info(f"保存程序记忆: {memory_id} (分类: {category})")
        return memory_id

    async def _append_to_continuity(
        self,
        memory_type: str,
        content: str,
        category: str
    ) -> None:
        """异步更新 CONTINUITY.md (优化版：IO 与内存操作分离)"""
        try:
            # 1. 读取当前内容 (IO 占 IO 锁)
            async with self._io_lock:
                if self._continuity_cache is None:
                    if self.continuity_file.exists():
                        async with aiofiles.open(self.continuity_file, 'r', encoding='utf-8') as f:
                            full_content = await f.read()
                    else:
                        full_content = "# SuperAgent v3.2 - 持续记忆 (CONTINUITY)\n\n"
                else:
                    full_content = self._continuity_cache

            # 2. 在内存中处理内容 (不占锁，因为是局部变量)
            timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            new_entry = f"\n- [{timestamp}] **{category}**: {content}\n"

            if category == "mistake" or "mistake" in content.lower():
                section = SECTION_MISTAKES
            elif memory_type == "procedural":
                section = SECTION_PRACTICES
            elif category == "architecture":
                section = SECTION_ARCHITECTURE
            else:
                section = SECTION_MISTAKES

            if section and section in full_content:
                parts = full_content.split(section)
                full_content = parts[0] + section + new_entry + parts[1]

            # 更新统计信息
            async with self._lock:
                stats = {
                    "total": self.index.get("total_count", 0),
                    "episodic": len(self.index.get("episodic", [])),
                    "semantic": len(self.index.get("semantic", [])),
                    "procedural": len(self.index.get("procedural", [])),
                }

            # 3. 更新统计部分内容 (字符串操作)
            stat_content = f"""## 📊 项目统计

- **总记忆条目**: {stats['total']}
- **情节记忆**: {stats['episodic']}
- **语义记忆**: {stats['semantic']}
- **程序记忆**: {stats['procedural']}
- **最后更新**: {timestamp}
"""
            if SECTION_STATISTICS in full_content:
                full_content = full_content.split(SECTION_STATISTICS)[0] + stat_content

            # 4. 写入文件 (IO 占 IO 锁)
            async with self._io_lock:
                async with aiofiles.open(self.continuity_file, 'w', encoding='utf-8') as f:
                    await f.write(full_content)
                self._continuity_cache = full_content

        except (OSError, IOError) as e:
            logger.error(f"更新 CONTINUITY.md 失败 (IO错误): {e}")
        except Exception as e:
            logger.error(f"更新 CONTINUITY.md 失败 (未知错误 - {type(e).__name__}): {e}")

    # ========== 综合查询 ==========

    async def query_relevant_memory(
        self,
        task: str,
        agent_type: Optional[str] = None
    ) -> Dict[str, List[str]]:
        """查询相关记忆,避免重复错误"""
        relevant = {
            "mistakes": [],
            "best_practices": [],
            "architecture_decisions": []
        }

        try:
            async with aiofiles.open(self.continuity_file, 'r', encoding='utf-8') as f:
                continuity = await f.read()

            if "## 📝 错误与教训" in continuity:
                relevant["mistakes"].append("查看 .superagent/memory/CONTINUITY.md")

            if "## 🎯 最佳实践" in continuity:
                relevant["best_practices"].append("查看 .superagent/memory/CONTINUITY.md")

            if "## 🏗️ 架构决策" in continuity:
                relevant["architecture_decisions"].append("查看 .superagent/memory/CONTINUITY.md")

        except (FileNotFoundError, UnicodeDecodeError) as e:
            logger.error(f"查询相关记忆失败 (文件缺失或编码错误): {e}")
        except (OSError, IOError) as e:
            logger.error(f"查询相关记忆失败 (系统IO错误): {e}")
        except Exception as e:
            logger.error(f"查询相关记忆遇到非预期错误 ({type(e).__name__}): {e}")

        return relevant

    async def save_mistake(
        self,
        error: Exception,
        context: str,
        fix: str,
        learning: str
    ) -> None:
        """保存错误教训 (重构版：委托处理)"""
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        error_name = error.__class__.__name__

        # 1. 保存到情节记忆
        mistake_entry = f"""## 错误: {error_name}
**时间**: {timestamp}
**上下文**: {context}
**错误信息**:
```
{str(error)}
```
**修复方案**: {fix}
**经验教训**: {learning}
---
"""
        await self.save_episodic_memory(
            event=mistake_entry,
            metadata={"type": "mistake", "error_type": error_name}
        )

        # 2. 委托更新 CONTINUITY.md
        summary = f"错误: {error_name} | 上下文: {context} | 方案: {fix}"
        await self._append_to_continuity("episodic", summary, "mistake")

        logger.info(f"保存错误教训: {error_name}")

    # ========== 统计信息 ==========

    def get_statistics(self) -> Dict[str, Any]:
        """获取记忆统计信息 (v3.3 优化：包含缓存命中率)"""
        idx = self.index

        # v3.3 计算缓存命中率
        total_access = sum(
            sum(entry[1] for entry in cache.values()) + len(cache)
            for cache in self._cache.values()
        )
        cache_hits = sum(
            sum(entry[1] for entry in cache.values())
            for cache in self._cache.values()
        )
        cache_hit_rate = (cache_hits / total_access * 100) if total_access > 0 else 0

        return {
            "total_memories": idx.get("total_count", 0),
            "episodic_count": len(idx.get("episodic", [])),
            "semantic_count": len(idx.get("semantic", [])),
            "procedural_count": len(idx.get("procedural", [])),
            "memory_dir": str(self.memory_dir),
            "cache_size": {t: len(c) for t, c in self._cache.items()},
            "cache_hit_rate": round(cache_hit_rate, 2),
            "index_ready": not self._index_building
        }

    def clear_cache(self) -> None:
        """清除所有查询缓存 (v3.3)"""
        for cache_type in self._cache:
            self._cache[cache_type].clear()
        logger.info("记忆查询缓存已清除")
