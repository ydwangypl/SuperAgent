#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Git Worktree管理器

管理Git worktree的创建、切换、清理等操作
"""

import subprocess
import shutil
from pathlib import Path
from typing import Optional, List
import logging

from .models import WorktreeConfig


logger = logging.getLogger(__name__)


class GitWorktreeManager:
    """Git Worktree管理器"""

    def __init__(self, project_root: Path, config: Optional[WorktreeConfig] = None):
        """初始化Worktree管理器

        Args:
            project_root: 项目根目录
            config: Worktree配置
        """
        self.project_root = Path(project_root)
        self.config = config or WorktreeConfig()

        # 验证Git仓库
        if not self._is_git_repository():
            raise ValueError(f"{self.project_root} 不是一个Git仓库")

        self.worktree_base = self.project_root / self.config.worktree_base

    def create_worktree(
        self,
        task_id: str,
        branch_name: Optional[str] = None,
        from_branch: Optional[str] = None
    ) -> Path:
        """创建新的worktree"""
        from common.security import validate_git_ref, validate_path, SecurityError

        # 1. 确定并验证分支名称
        if not branch_name:
            branch_name = f"task-{task_id}"

        try:
            branch_name = validate_git_ref(branch_name)
        except SecurityError as e:
            logger.error(f"非法分支名称: {branch_name}, 错误: {e}")
            raise

        # 2. 确定并验证基础分支
        if not from_branch:
            from_branch = self.config.main_branch

        try:
            from_branch = validate_git_ref(from_branch)
        except SecurityError as e:
            logger.error(f"非法基础分支名称: {from_branch}, 错误: {e}")
            raise

        # 3. 确定并验证worktree路径
        raw_worktree_path = self.worktree_base / self.config.naming_pattern.format(
            task_id=task_id
        )

        try:
            worktree_path = validate_path(raw_worktree_path, self.worktree_base)
        except SecurityError as e:
            logger.error(f"非法worktree路径: {raw_worktree_path}, 错误: {e}")
            raise

        # 4. 如果worktree已存在,先清理
        if worktree_path.exists():
            logger.warning(f"Worktree已存在: {worktree_path}, 将先删除")
            self.remove_worktree(worktree_path)

        # 创建基础目录
        self.worktree_base.mkdir(parents=True, exist_ok=True)

        # 构建git worktree add命令
        cmd = [
            "git",
            "worktree",
            "add",
            str(worktree_path),
            f"{from_branch}",
            "-b",
            branch_name
        ]

        # 执行命令
        logger.info(f"创建worktree: {branch_name} at {worktree_path}")
        result = subprocess.run(
            cmd,
            cwd=self.project_root,
            capture_output=True,
            text=True,
            check=True
        )

        logger.debug(f"Git output: {result.stdout}")

        return worktree_path

    def remove_worktree(self, worktree_path: Path) -> bool:
        """移除worktree (增加安全性验证)"""
        from common.security import validate_path, SecurityError

        try:
            # 验证路径是否在允许的 worktree 基础目录下
            worktree_path = validate_path(worktree_path, self.worktree_base)
        except SecurityError as e:
            logger.error(f"安全拒绝：尝试移除未授权路径: {worktree_path}, 错误: {e}")
            return False

        if not worktree_path.exists():
            logger.warning(f"Worktree不存在: {worktree_path}")
            return False

        try:
            # 先删除Git worktree记录
            subprocess.run(
                ["git", "worktree", "remove", str(worktree_path)],
                cwd=self.project_root,
                capture_output=True,
                text=True,
                check=True
            )

            logger.info(f"已移除worktree: {worktree_path}")
            return True

        except subprocess.CalledProcessError as e:
            logger.error(f"移除worktree失败: {e.stderr}")

            # 如果git命令失败,尝试直接删除目录
            try:
                shutil.rmtree(worktree_path)
                logger.info(f"已强制删除目录: {worktree_path}")
                return True
            except Exception as e2:
                logger.error(f"删除目录失败: {e2}")
                return False

    def list_worktrees(self) -> List[dict]:
        """列出所有worktree

        Returns:
            List[dict]: worktree信息列表
        """
        try:
            result = subprocess.run(
                ["git", "worktree", "list", "--porcelain"],
                cwd=self.project_root,
                capture_output=True,
                text=True,
                check=True
            )

            worktrees = []
            current_worktree = {}

            for line in result.stdout.splitlines():
                if not line:
                    if current_worktree:
                        worktrees.append(current_worktree)
                        current_worktree = {}
                    continue

                parts = line.split(" ", 1)
                if len(parts) != 2:
                    continue

                key, value = parts
                current_worktree[key] = value

            # 添加最后一个worktree
            if current_worktree:
                worktrees.append(current_worktree)

            return worktrees

        except subprocess.CalledProcessError as e:
            logger.error(f"列出worktree失败: {e.stderr}")
            return []

    def prune_worktrees(self) -> bool:
        """清理无用的worktree记录

        Returns:
            bool: 是否成功
        """
        try:
            cmd = ["git", "worktree", "prune"]
            if self.config.force_prune:
                cmd.append("--force")

            subprocess.run(
                cmd,
                cwd=self.project_root,
                capture_output=True,
                text=True,
                check=True
            )

            logger.info("已清理worktree记录")
            return True

        except subprocess.CalledProcessError as e:
            logger.error(f"清理worktree失败: {e.stderr}")
            return False

    def get_worktree_branch(self, worktree_path: Path) -> Optional[str]:
        """获取worktree对应的分支名称

        Args:
            worktree_path: worktree路径

        Returns:
            Optional[str]: 分支名称,如果失败返回None
        """
        worktrees = self.list_worktrees()

        for wt in worktrees:
            if Path(wt.get("worktree", "")).resolve() == worktree_path.resolve():
                return wt.get("branch", None)

        return None

    def cleanup_all(self) -> int:
        """清理所有worktree

        Returns:
            int: 清理的worktree数量
        """
        if not self.worktree_base.exists():
            return 0

        count = 0
        for worktree_dir in self.worktree_base.iterdir():
            if worktree_dir.is_dir():
                if self.remove_worktree(worktree_dir):
                    count += 1

        # 清理基础目录
        if self.worktree_base.exists() and not list(self.worktree_base.iterdir()):
            self.worktree_base.rmdir()

        # Prune git记录
        self.prune_worktrees()

        logger.info(f"清理了 {count} 个worktree")
        return count

    def _is_git_repository(self) -> bool:
        """检查是否是Git仓库

        Returns:
            bool: 是否是Git仓库
        """
        git_dir = self.project_root / ".git"
        return git_dir.exists()
