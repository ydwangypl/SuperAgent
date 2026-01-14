#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Worktree 编排器 (WorktreeOrchestrator)
负责隔离工作区的生命周期管理与同步
"""

import logging
import asyncio
import aiofiles
from pathlib import Path
from typing import Optional

from .base import BaseOrchestrator
from .models import TaskExecution, TaskStatus, OrchestrationConfig
from .worktree_manager import GitWorktreeManager
from common.security import validate_path
from common.exceptions import SecurityError

logger = logging.getLogger(__name__)


class WorktreeOrchestrator(BaseOrchestrator):
    """Worktree 业务逻辑封装"""

    def __init__(
        self,
        project_root: Path,
        worktree_manager: Optional[GitWorktreeManager] = None,
        config: Optional[OrchestrationConfig] = None
    ) -> None:
        super().__init__(project_root, config)
        self.worktree_manager = worktree_manager

    def _validate_path(self, path: str) -> Path:
        """验证路径安全性,防止路径穿越"""
        try:
            return validate_path(Path(path), self.project_root)
        except SecurityError as e:
            logger.error(f"路径验证失败: {e}")
            raise ValueError(f"Security error: {e}")

    async def create_for_task(self, task: TaskExecution, agent_type: str) -> None:
        """为任务创建隔离工作区"""
        if not self.worktree_manager:
            return

        # 审计优化: 定义需要隔离的 Agent 类型
        isolated_agents = [
            "backend-dev", "frontend-dev", "database-design",
            "full-stack-dev", "qa-engineering", "code-refactoring",
            "devops-engineering", "mini-program-dev"
        ]

        if agent_type in isolated_agents:
            try:
                worktree_path = await asyncio.to_thread(
                    self.worktree_manager.create_worktree,
                    task_id=task.task_id,
                    branch_name=f"task/{task.step_id}"
                )
                task.worktree_path = worktree_path
                logger.info(f"为任务 {task.task_id} 创建隔离工作区: {worktree_path}")
            except Exception as e:
                logger.warning(f"创建工作区失败 ({type(e).__name__}): {e}")

    async def sync_to_root(self, task: TaskExecution) -> None:
        """同步工作区更改到项目根目录"""
        if not task.worktree_path or not task.worktree_path.exists():
            return

        if task.status != TaskStatus.COMPLETED:
            return

        try:
            files_to_sync = task.result.get('files', []) if task.result else []
            if not files_to_sync:
                return

            for rel_path in files_to_sync:
                try:
                    # 验证路径安全性
                    dest_path = self._validate_path(rel_path)
                    src_path = task.worktree_path / rel_path

                    if src_path.exists() and src_path.is_file():
                        dest_path.parent.mkdir(parents=True, exist_ok=True)
                        async with aiofiles.open(src_path, 'rb') as src, \
                                   aiofiles.open(dest_path, 'wb') as dest:
                            await dest.write(await src.read())
                        logger.debug(f"已同步文件: {rel_path}")
                except (ValueError, SecurityError) as e:
                    logger.warning(f"跳过不安全或无效的路径 {rel_path}: {e}")
                    continue

            logger.info(f"任务 {task.task_id} 成果同步完成")
        except Exception as e:
            logger.error(f"同步任务 {task.task_id} 失败 ({type(e).__name__}): {e}")

    async def cleanup_all(self) -> int:
        """清理所有工作区"""
        if self.worktree_manager:
            return await asyncio.to_thread(self.worktree_manager.cleanup_all)
        return 0
