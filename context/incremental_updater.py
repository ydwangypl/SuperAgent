#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
增量更新检测器

提供文件快照和增量更新检测功能,减少Token消耗
基于V2.2.0的incremental_updater.py实现
"""

import json
import hashlib
import logging
import asyncio
import aiofiles
from typing import Dict, List, Optional, Tuple, Any, Union
from pathlib import Path
from dataclasses import dataclass, field, asdict
from datetime import datetime
import shutil
import difflib

from common.security import validate_path
from common.exceptions import SecurityError

logger = logging.getLogger(__name__)


@dataclass
class FileSnapshot:
    """文件快照"""
    path: str                    # 相对路径
    size: int                    # 文件大小(bytes)
    mtime: float                 # 修改时间
    hash: str                    # MD5哈希
    snapshot_time: float         # 拍摄时间
    content: Optional[str] = None  # 缓存内容用于diff

    def to_dict(self) -> Dict:
        return {
            "path": self.path,
            "size": self.size,
            "mtime": self.mtime,
            "hash": self.hash,
            "snapshot_time": self.snapshot_time,
            "content": None  # 序列化时排除内容以节省空间
        }

    @classmethod
    def from_dict(cls, data: Dict) -> 'FileSnapshot':
        return cls(**data)


@dataclass
class ChangeRecord:
    """变更记录"""
    path: str
    change_type: str  # "added", "modified", "deleted"
    old_snapshot: Optional[FileSnapshot] = None
    new_snapshot: Optional[FileSnapshot] = None
    diff_ratio: float = 0.0  # 差异比例 (0-1)
    diff: Optional[str] = None  # diff内容(如果适用)
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())

    @property
    def file_path(self) -> str:
        """兼容性属性"""
        return self.path

    def to_dict(self) -> Dict:
        return {
            "path": self.path,
            "change_type": self.change_type,
            "diff_ratio": self.diff_ratio,
            "diff": self.diff,
            "timestamp": self.timestamp
        }


@dataclass
class IncrementalConfig:
    """增量更新配置"""
    enabled: bool = True
    retention_days: int = 30
    incremental_threshold: float = 0.3  # 30%以下使用增量
    max_snapshots_per_file: int = 10
    cache_content: bool = True
    snapshot_dir: str = ".superagent/snapshots"

    def to_dict(self) -> Dict:
        return {
            "enabled": self.enabled,
            "retention_days": self.retention_days,
            "incremental_threshold": self.incremental_threshold,
            "max_snapshots_per_file": self.max_snapshots_per_file,
            "cache_content": self.cache_content,
            "snapshot_dir": self.snapshot_dir
        }


class IncrementalUpdater:
    """增量更新检测器"""

    def __init__(
        self,
        project_root: Path,
        config: IncrementalConfig = None
    ):
        """初始化增量更新器

        Args:
            project_root: 项目根目录
            config: 配置
        """
        self.project_root = Path(project_root)
        self.config = config or IncrementalConfig()

        # 快照目录
        self.snapshot_dir = self.project_root / self.config.snapshot_dir
        self.snapshot_dir.mkdir(parents=True, exist_ok=True)

        # 索引文件
        self.index_file = self.snapshot_dir / "index.json"

        # 索引
        self.snapshots = self._load_index()

        logger.info(
            f"增量更新器初始化完成: {self.snapshot_dir}, "
            f"索引文件: {len(self.snapshots)} 个条目"
        )

    def _load_index(self) -> Dict[str, Dict]:
        """加载索引"""
        if self.index_file.exists():
            try:
                with open(self.index_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    # 将字典转换回 FileSnapshot 对象以供 snapshots 属性使用
                    return {path: FileSnapshot.from_dict(d) for path, d in data.items()}
            except Exception as e:
                logger.warning(f"加载索引失败 ({type(e).__name__}): {e}")
        return {}

    async def _save_index(self):
        """异步保存索引"""
        async with aiofiles.open(self.index_file, 'w', encoding='utf-8') as f:
            data = {path: snap.to_dict() for path, snap in self.snapshots.items()}
            await f.write(json.dumps(data, ensure_ascii=False, indent=2))

    async def take_snapshot(
        self,
        file_path: Union[str, List[str]],
        content: str = None,
        save: bool = True
    ) -> Union[FileSnapshot, Dict[str, FileSnapshot]]:
        """拍摄文件快照 (异步)"""
        if isinstance(file_path, list):
            tasks = [self._take_single_snapshot(path, save=False) for path in file_path]
            results = await asyncio.gather(*tasks)
            
            snapshots = {}
            for path, snap in zip(file_path, results):
                if snap:
                    snapshots[path] = snap
                    if save:
                        self.snapshots[path] = snap
            
            if save:
                await self._save_index()
            return snapshots
        
        return await self._take_single_snapshot(file_path, content, save=save)

    async def _take_single_snapshot(
        self,
        file_path: str,
        content: str = None,
        save: bool = True
    ) -> Optional[FileSnapshot]:
        """内部方法：拍摄单个文件快照 (异步)"""
        # 处理绝对路径
        path_obj = Path(file_path)
        if path_obj.is_absolute():
            try:
                file_path = str(path_obj.relative_to(self.project_root))
            except ValueError:
                file_path = path_obj.name

        abs_path = self.project_root / file_path

        if not abs_path.exists():
            logger.warning(f"文件不存在: {abs_path}")
            return None

        # 计算文件信息 (stat 是阻塞的, 但通常很快)
        stat = abs_path.stat()
        size = stat.st_size
        mtime = stat.st_mtime

        # 异步读取内容
        if content is None:
            try:
                async with aiofiles.open(abs_path, mode='r', encoding='utf-8') as f:
                    content = await f.read()
            except Exception as e:
                logger.warning(f"异步读取文件失败 ({type(e).__name__}): {abs_path}, {e}")
                return None

        file_hash = hashlib.md5(content.encode()).hexdigest()

        snapshot = FileSnapshot(
            path=file_path,
            size=size,
            mtime=mtime,
            hash=file_hash,
            snapshot_time=datetime.now().timestamp(),
            content=content if self.config.cache_content else None
        )

        if save:
            self.snapshots[file_path] = snapshot
            await self._save_index()
            
        return snapshot

    async def take_project_snapshot(self, save: bool = True) -> Dict[str, FileSnapshot]:
        """拍摄项目所有文件快照 (异步)"""
        # 跳过这些目录
        skip_dirs = {'.git', 'node_modules', '__pycache__', '.venv', 'venv', '.superagent'}
        
        file_paths = []
        for path in self.project_root.rglob('*'):
            if path.is_file():
                skip = False
                for skip_dir in skip_dirs:
                    if skip_dir in path.parts:
                        skip = True
                        break
                if not skip:
                    rel_path = str(path.relative_to(self.project_root))
                    file_paths.append(rel_path)

        # 并发执行快照
        return await self.take_snapshot(file_paths, save=save)

    async def detect_changes(
        self,
        before: Union[str, FileSnapshot, List[str]],
        after: Union[str, FileSnapshot] = None
    ) -> Union[Optional[ChangeRecord], List[ChangeRecord]]:
        """检测文件变更 (异步)"""
        if isinstance(before, list):
            tasks = []
            for path in before:
                tasks.append(self._detect_async_change(path))
            return await asyncio.gather(*tasks)

        return await self._detect_async_change(before, after)

    async def _detect_async_change(
        self,
        before: Union[str, FileSnapshot, None],
        after: Union[str, FileSnapshot, None] = None
    ) -> Optional[ChangeRecord]:
        """内部异步方法：检测单个文件变更"""
        # 获取之前快照
        if isinstance(before, str):
            old_snapshot = self._get_snapshot(before)
        else:
            old_snapshot = before

        # 获取之后快照
        if after is None:
            if old_snapshot and isinstance(old_snapshot, FileSnapshot):
                new_snapshot = await self._take_single_snapshot(old_snapshot.path, save=False)
            else:
                new_snapshot = None
        elif isinstance(after, str):
            new_snapshot = await self._take_single_snapshot(after, save=False)
        else:
            new_snapshot = after

        if not old_snapshot and not new_snapshot:
            return None

        # 判断变更类型
        if not old_snapshot:
            change_type = "added"
            diff_ratio = 1.0
        elif not new_snapshot:
            change_type = "deleted"
            diff_ratio = 1.0
        elif old_snapshot.hash == new_snapshot.hash:
            return None  # 无变更
        else:
            change_type = "modified"
            diff_ratio = self._calculate_diff_ratio(
                old_snapshot, new_snapshot
            )

        record = ChangeRecord(
            path=new_snapshot.path if new_snapshot else old_snapshot.path,
            change_type=change_type,
            old_snapshot=old_snapshot,
            new_snapshot=new_snapshot,
            diff_ratio=diff_ratio
        )

        if change_type == "modified" and diff_ratio < self.config.incremental_threshold:
            record.diff = self._generate_diff(
                old_snapshot.content or "",
                new_snapshot.content or ""
            )

        return record

    async def detect_project_changes(
        self,
        before_snapshots: Dict[str, FileSnapshot] = None
    ) -> List[ChangeRecord]:
        """检测项目变更 (异步)"""
        if before_snapshots is None:
            before_snapshots = self.snapshots

        # 获取当前快照
        after_snapshots = await self.take_project_snapshot(save=False)

        tasks = []
        # 检测新增和修改的文件
        for path, new_snapshot in after_snapshots.items():
            if path in before_snapshots:
                old_snapshot = before_snapshots[path]
                if old_snapshot.hash != new_snapshot.hash:
                    tasks.append(self._detect_async_change(old_snapshot, new_snapshot))
            else:
                tasks.append(self._detect_async_change(before=None, after=new_snapshot))

        # 检测删除的文件
        for path in before_snapshots:
            if path not in after_snapshots:
                old_snapshot = before_snapshots[path]
                tasks.append(self._detect_async_change(old_snapshot, after=None))

        results = await asyncio.gather(*tasks)
        changes = [r for r in results if r]
        
        logger.info(f"检测到 {len(changes)} 个变更")
        return changes

    async def get_incremental_update(
        self,
        file_path: str,
        before: str = None,
        after: str = None
    ) -> Optional[Dict[str, Any]]:
        """获取增量更新 (异步)

        Args:
            file_path: 文件路径
            before: 之前快照(可选,默认使用索引中的快照)
            after: 之后快照(可选,默认使用当前文件状态)

        Returns:
            Dict: 增量更新信息
        """
        # 获取之前的快照(从索引或指定路径)
        old_snapshot = None
        if before is not None:
            if isinstance(before, str):
                old_snapshot = self._get_snapshot(before)
            else:
                old_snapshot = before
        else:
            # 默认使用索引中保存的快照
            old_snapshot = self._get_snapshot(file_path)

        # 获取之后的快照(当前文件状态或指定路径)
        if after is not None:
            if isinstance(after, str):
                new_snapshot = await self.take_snapshot(after, save=False)
            else:
                new_snapshot = after
        else:
            # 默认拍摄当前文件状态，但不保存到索引，以免破坏对比
            new_snapshot = await self.take_snapshot(file_path, save=False)

        if not old_snapshot and not new_snapshot:
            return None

        # 默认基础结构
        result = {
            "file_path": file_path,
            "diff_ratio": 0.0,
            "diff_size": 0,
            "use_incremental": False,
            "content": None
        }

        # 判断变更类型
        if not old_snapshot:
            # 新增文件
            result.update({
                "change_type": "added",
                "content": new_snapshot.content if new_snapshot else None,
                "diff_ratio": 1.0
            })
            return result

        if not new_snapshot:
            # 文件被删除
            result.update({
                "change_type": "deleted",
                "use_incremental": True,
                "diff_ratio": 1.0
            })
            return result

        if old_snapshot.hash == new_snapshot.hash:
            # 无变更
            result.update({
                "change_type": "unchanged",
                "diff_ratio": 0.0
            })
            return result

        # 文件被修改
        diff_ratio = self._calculate_diff_ratio(old_snapshot, new_snapshot)
        diff = self._generate_diff(
            old_snapshot.content or "",
            new_snapshot.content or ""
        )

        result.update({
            "change_type": "modified",
            "diff_ratio": diff_ratio,
            "diff_size": len(diff),
            "old_hash": old_snapshot.hash,
            "new_hash": new_snapshot.hash
        })

        if diff_ratio < self.config.incremental_threshold:
            # 差异小于阈值,使用增量更新
            result.update({
                "use_incremental": True,
                "diff": diff
            })
        else:
            # 差异大于阈值,使用完整内容
            result.update({
                "use_incremental": False,
                "content": new_snapshot.content
            })
            
        return result

    async def get_incremental_context(
        self, 
        file_paths: List[str] = None
    ) -> List[Dict[str, Any]]:
        """获取增量上下文 (异步)

        Args:
            file_paths: 文件路径列表(可选,默认所有)

        Returns:
            List[Dict]: 增量更新信息列表
        """
        if file_paths is None:
            file_paths = list(self.snapshots.keys())

        tasks = [self.get_incremental_update(path) for path in file_paths]
        results = await asyncio.gather(*tasks)
        
        return [r for r in results if r]

    async def apply_incremental_update(
        self,
        update: Dict[str, Any],
        content: str = None
    ) -> bool:
        """应用增量更新 (异步)

        Args:
            update: 增量更新信息
            content: 完整内容(用于增量更新时)

        Returns:
            bool: 是否成功
        """
        try:
            # 路径安全验证
            file_path = validate_path(Path(update["file_path"]), self.project_root)
        except (SecurityError, ValueError) as e:
            logger.error(f"不安全的更新路径: {update.get('file_path')}, {e}")
            return False

        if update["change_type"] == "deleted":
            # 删除文件
            if file_path.exists():
                try:
                    file_path.unlink()
                    logger.info(f"删除文件: {update['file_path']}")
                except Exception as e:
                    logger.error(f"删除文件失败 ({type(e).__name__}): {file_path}, {e}")
                    return False
            return True

        if update["change_type"] == "added":
            # 新增文件
            try:
                file_path.parent.mkdir(parents=True, exist_ok=True)
                async with aiofiles.open(file_path, 'w', encoding='utf-8') as f:
                    await f.write(update["content"])
                await self.take_snapshot(update["file_path"])
                logger.info(f"新增文件: {update['file_path']}")
                return True
            except Exception as e:
                logger.error(f"新增文件失败 ({type(e).__name__}): {file_path}, {e}")
                return False

        if update["change_type"] == "modified":
            try:
                if update.get("use_incremental"):
                    # 应用diff
                    if content and update.get("diff"):
                        new_content = self._apply_diff(
                            content,
                            update["diff"]
                        )
                        async with aiofiles.open(file_path, 'w', encoding='utf-8') as f:
                            await f.write(new_content)
                        await self.take_snapshot(update["file_path"])
                        logger.info(
                            f"应用增量更新: {update['file_path']}, "
                            f"差异: {update['diff_ratio']*100:.1f}%"
                        )
                        return True
                else:
                    # 使用完整内容
                    async with aiofiles.open(file_path, 'w', encoding='utf-8') as f:
                        await f.write(update["content"])
                    await self.take_snapshot(update["file_path"])
                    logger.info(f"应用完整更新: {update['file_path']}")
                    return True
            except Exception as e:
                logger.error(f"更新文件失败 ({type(e).__name__}): {file_path}, {e}")
                return False

        return False

    async def cleanup_old_snapshots(self) -> int:
        """清理过期的快照 (异步)"""
        from datetime import datetime as dt

        cutoff_time = dt.now().timestamp() - self.config.retention_days * 24 * 3600
        cleaned = 0

        for path, snap in list(self.snapshots.items()):
            if snap.snapshot_time < cutoff_time:
                del self.snapshots[path]
                cleaned += 1

        if cleaned > 0:
            await self._save_index()
            logger.info(f"清理了 {cleaned} 个旧快照")

        return cleaned

    async def get_change_summary_async(self) -> Dict[str, Any]:
        """获取变更摘要 (异步)"""
        changes = await self.detect_project_changes()
        
        added = [c.path for c in changes if c.change_type == "added"]
        modified = [c.path for c in changes if c.change_type == "modified"]
        deleted = [c.path for c in changes if c.change_type == "deleted"]
        
        changes_by_file = {c.path: c.change_type for c in changes}
        
        return {
            "added": added,
            "modified": modified,
            "deleted": deleted,
            "total_changes": len(changes),
            "changes_by_file": changes_by_file,
            "timestamp": datetime.now().isoformat()
        }

    def get_change_summary(self) -> Dict[str, Any]:
        """获取变更摘要 (同步 - 仅用于兼容性)"""
        # 注意：此方法在异步环境中会报错，仅保留接口
        import asyncio
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                # 如果在运行中的 event loop 中，这种调用是不安全的
                logger.warning("在运行中的 event loop 中同步调用 get_change_summary")
                return {"error": "synchronous call in async loop"}
            return loop.run_until_complete(self.get_change_summary_async())
        except Exception as e:
            logger.error(f"同步运行异步方法失败 ({type(e).__name__}): {e}")
            return {"error": f"could not run async method synchronously: {e}"}

    def _get_snapshot(self, file_path: str) -> Optional[FileSnapshot]:
        """获取已保存的快照"""
        # 处理绝对路径
        path_obj = Path(file_path)
        if path_obj.is_absolute():
            try:
                file_path = str(path_obj.relative_to(self.project_root))
            except ValueError:
                file_path = path_obj.name
        
        return self.snapshots.get(file_path)

    def _calculate_diff_ratio(self, old_val: Union[FileSnapshot, str], new_val: Union[FileSnapshot, str]) -> float:
        """计算差异比例"""
        old_content = old_val.content if isinstance(old_val, FileSnapshot) else old_val
        new_content = new_val.content if isinstance(new_val, FileSnapshot) else new_val
        
        if not old_content or not new_content:
            if not old_content and not new_content:
                return 0.0
            return 1.0
        
        import difflib
        matcher = difflib.SequenceMatcher(None, old_content, new_content)
        return 1.0 - matcher.ratio()

    def _generate_diff(self, old_text: str, new_text: str) -> str:
        """生成文本差异"""
        import difflib
        diff = difflib.unified_diff(
            old_text.splitlines(keepends=True),
            new_text.splitlines(keepends=True),
            fromfile='before',
            tofile='after'
        )
        return ''.join(diff)

    def _apply_diff(self, old_text: str, diff_text: str) -> str:
        """应用文本差异 (使用 difflib.unified_diff 生成的 diff)"""
        import difflib
        import re

        # 尝试使用 patch 逻辑
        lines = old_text.splitlines(keepends=True)
        diff_lines = diff_text.splitlines(keepends=True)
        
        # 简单的 patch 实现
        # 注意: unified_diff 的格式比较复杂, 这里实现一个健壮的解析器
        result = []
        i = 0
        
        # 跳过头部 (--- / +++)
        while i < len(diff_lines) and (diff_lines[i].startswith('---') or diff_lines[i].startswith('+++')):
            i += 1
            
        # 处理每个 hunk
        source_line = 0
        while i < len(diff_lines):
            line = diff_lines[i]
            if line.startswith('@@'):
                # 解析 hunk header: @@ -start,len +start,len @@
                match = re.match(r'@@ -(\d+),?(\d*) \+(\d+),?(\d*) @@', line)
                if match:
                    # 记录当前 hunk 之前的行
                    old_start = int(match.group(1))
                    # 补齐 hunk 之前的行
                    while source_line < old_start - 1 and source_line < len(lines):
                        result.append(lines[source_line])
                        source_line += 1
                i += 1
                continue
            
            if line.startswith(' '):
                # 上下文行
                result.append(line[1:])
                source_line += 1
            elif line.startswith('+'):
                # 新增行
                result.append(line[1:])
            elif line.startswith('-'):
                # 删除行
                source_line += 1
            
            i += 1
            
        # 补齐剩余行
        while source_line < len(lines):
            result.append(lines[source_line])
            source_line += 1
            
        return "".join(result)

class IncrementalUpdateManager:
    """增量更新管理器 - 集成封装"""
    def __init__(self, project_root: Union[str, Path]):
        self.project_root = Path(project_root)
        self.updater = IncrementalUpdater(self.project_root)

    async def before_agent_execution(self, files: List[str] = None) -> Dict[str, Any]:
        """Agent执行前的准备工作 (异步)"""
        if files:
            await self.updater.take_snapshot(files)
        else:
            await self.updater.take_project_snapshot()
        
        return await self.updater.get_change_summary_async()

    async def after_agent_execution(self, files: List[str] = None) -> Dict[str, Any]:
        """Agent执行后的变更检测 (异步)"""
        changes = await self.updater.detect_project_changes()
        if files:
            changes = [c for c in changes if c.path in files]
            
        return {
            "change_count": len(changes),
            "changes": [c.to_dict() for c in changes],
            "timestamp": datetime.now().isoformat()
        }

    async def get_updates(self, files: List[str] = None) -> List[ChangeRecord]:
        """获取文件更新 (异步)"""
        changes = await self.updater.detect_project_changes()
        if files:
            return [c for c in changes if c.path in files]
        return changes

    async def get_incremental_updates_for_context(self, files: List[str] = None) -> List[Dict[str, Any]]:
        """获取用于上下文的增量更新 (异步)"""
        return await self.updater.get_incremental_context(files)
