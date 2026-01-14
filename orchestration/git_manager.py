#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Git 自动提交管理器 (GitAutoCommitManager)

自动为每个完成的任务创建 Git commit,实现增量版本控制。
结合 Worktree 隔离,实现完美的状态管理。
"""

import logging
import subprocess
from typing import List, Optional, Dict, Any
from datetime import datetime
from pathlib import Path

logger = logging.getLogger(__name__)


class GitAutoCommitManager:
    """Git 自动提交管理器

    为每个完成的任务自动创建 Git commit,包含:
    - 描述性的 commit message
    - 任务 ID 和摘要
    - 自动变更文件暂存
    """

    def __init__(
        self,
        project_root: Path,
        enabled: bool = True,
        commit_message_template: str = "feat: {task_id} {description}",
        auto_push: bool = False
    ):
        """初始化 Git 管理器

        Args:
            project_root: 项目根目录
            enabled: 是否启用自动提交
            commit_message_template: Commit message 模板
            auto_push: 是否自动推送到远程仓库
        """
        self.project_root = Path(project_root)
        self.enabled = enabled
        self.commit_message_template = commit_message_template
        self.auto_push = auto_push

        # 验证 Git 仓库
        self.repo = None
        if self.enabled:
            try:
                import git
                self.repo = git.Repo(self.project_root)
                logger.info("Git 仓库已初始化")
            except ImportError:
                logger.warning("gitpython 未安装,将使用 subprocess")
            except Exception as e:
                logger.warning(f"Git 仓库初始化失败: {e}")
                self.enabled = False

    async def commit_task(
        self,
        task_id: str,
        description: str,
        changed_files: List[str],
        summary: Optional[str] = None
    ) -> bool:
        """提交任务结果

        Args:
            task_id: 任务 ID
            description: 任务描述
            changed_files: 修改的文件列表
            summary: 执行摘要 (可选)

        Returns:
            是否成功提交
        """
        if not self.enabled:
            logger.debug("Git 自动提交未启用")
            return False

        if not changed_files:
            logger.warning(f"没有需要提交的变更: {task_id}")
            return False

        try:
            # 1. Stage 变更文件
            staged_count = await self._stage_files(changed_files)
            if staged_count == 0:
                logger.warning(f"没有文件被暂存: {task_id}")
                return False

            # 2. 生成 commit message
            commit_message = self._generate_commit_message(
                task_id,
                description,
                summary
            )

            # 3. 执行 commit
            commit_success = await self._create_commit(commit_message)

            if commit_success:
                logger.info(f"Git commit: {task_id} - {description[:50]}")

                # 4. 可选: 自动推送
                if self.auto_push:
                    await self._push_to_remote()

                return True
            else:
                return False

        except Exception as e:
            logger.error(f"Git commit 失败: {e}")
            return False

    async def commit_tasks_json(self) -> bool:
        """提交 tasks.json 更新

        Returns:
            是否成功提交
        """
        if not self.enabled:
            return False

        try:
            tasks_json_path = self.project_root / "tasks.json"
            if tasks_json_path.exists():
                # 暂存 tasks.json
                await self._stage_files(["tasks.json"])

                # 提交
                timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
                commit_message = f"chore: 更新任务进度 ({timestamp})"

                success = await self._create_commit(commit_message)
                if success:
                    logger.debug("已提交 tasks.json 更新")

                return success

        except Exception as e:
            logger.error(f"提交 tasks.json 失败: {e}")
            return False

    def _generate_commit_message(
        self,
        task_id: str,
        description: str,
        summary: Optional[str]
    ) -> str:
        """生成 commit message

        Args:
            task_id: 任务 ID
            description: 任务描述
            summary: 执行摘要

        Returns:
            格式化的 commit message
        """
        # 第一行: 标题 (使用模板)
        title = self.commit_message_template.format(
            task_id=task_id,
            description=description
        )

        # 限制标题长度 (50 字符)
        if len(title) > 50:
            title = title[:47] + "..."

        # 如果有摘要,添加详情
        if summary:
            commit_message = f"{title}\n\n{summary}"
        else:
            commit_message = title

        return commit_message

    async def _stage_files(self, files: List[str]) -> int:
        """暂存文件到 Git

        Args:
            files: 文件列表

        Returns:
            成功暂存的文件数量
        """
        staged_count = 0

        for file_path in files:
            try:
                full_path = self.project_root / file_path

                if not full_path.exists():
                    logger.warning(f"文件不存在,跳过: {file_path}")
                    continue

                # 使用 gitpython 或 subprocess
                if self.repo:
                    self.repo.index.add([str(full_path)])
                else:
                    # 使用 subprocess
                    # 获取相对路径
                    try:
                        rel_path = Path(file_path).relative_to(self.project_root)
                    except ValueError:
                        rel_path = file_path

                    subprocess.run(
                        ["git", "add", str(rel_path)],
                        cwd=self.project_root,
                        capture_output=True,
                        check=True
                    )

                staged_count += 1
                logger.debug(f"已暂存: {file_path}")

            except Exception as e:
                logger.error(f"暂存文件失败 {file_path}: {e}")

        return staged_count

    async def _create_commit(self, message: str) -> bool:
        """创建 Git commit

        Args:
            message: Commit message

        Returns:
            是否成功
        """
        try:
            if self.repo:
                # 使用 gitpython
                self.repo.index.commit(message)
            else:
                # 使用 subprocess
                subprocess.run(
                    ["git", "commit", "-m", message],
                    cwd=self.project_root,
                    capture_output=True,
                    check=True
                )

            return True

        except subprocess.CalledProcessError as e:
            logger.error(f"Git commit 失败: {e.stderr if e.stderr else str(e)}")
            return False
        except Exception as e:
            logger.error(f"Git commit 异常: {e}")
            return False

    async def _push_to_remote(self) -> bool:
        """推送到远程仓库

        Returns:
            是否成功
        """
        try:
            if self.repo:
                # 检查是否有远程仓库
                remotes = list(self.repo.remotes)
                if not remotes:
                    logger.debug("没有配置远程仓库")
                    return False

                # 推送
                origin = self.repo.remotes.origin
                origin.push()

            else:
                # 使用 subprocess
                result = subprocess.run(
                    ["git", "push"],
                    cwd=self.project_root,
                    capture_output=True
                )

                if result.returncode != 0:
                    logger.warning(f"Git push 失败: {result.stderr.decode()}")
                    return False

            logger.info("已推送到远程仓库")
            return True

        except Exception as e:
            logger.warning(f"推送失败: {e}")
            return False

    def get_commit_history(self, limit: int = 10) -> List[Dict[str, Any]]:
        """获取提交历史

        Args:
            limit: 返回的提交数量

        Returns:
            提交历史列表
        """
        history = []

        try:
            if self.repo:
                # 使用 gitpython
                for commit in list(self.repo.iter_commits(max_count=limit)):
                    history.append({
                        "hash": commit.hexsha[:7],
                        "message": commit.message.strip(),
                        "author": commit.author.name,
                        "date": datetime.fromtimestamp(commit.committed_date).isoformat()
                    })
            else:
                # 使用 subprocess
                # 尝试获取 log
                # 使用 --no-pager 确保不分页
                # 1. 尝试使用 rev-list 获取基本信息 (最可靠)
                result = subprocess.run(
                    ["git", "--no-pager", "rev-list", "--pretty=oneline", "-n", str(limit), "HEAD"],
                    cwd=self.project_root,
                    capture_output=True,
                    text=True,
                    encoding='utf-8',
                    errors='replace',
                    check=False
                )

                if result.returncode == 0 and result.stdout.strip():
                    lines = result.stdout.strip().split("\n")
                    for i in range(0, len(lines)):
                        line = lines[i].strip()
                        if line.startswith("commit "):
                            continue
                        parts = line.split(maxsplit=1)
                        if len(parts) >= 1:
                            history.append({
                                "hash": parts[0][:7],
                                "message": parts[1] if len(parts) > 1 else "no message",
                                "author": "unknown",
                                "date": "unknown"
                            })
                    if history:
                        return history

                # 2. 尝试使用 log --oneline
                result = subprocess.run(
                    ["git", "--no-pager", "log", "-n", str(limit), "--oneline"],
                    cwd=self.project_root,
                    capture_output=True,
                    text=True,
                    encoding='utf-8',
                    errors='replace',
                    check=False
                )

                if result.returncode == 0 and result.stdout.strip():
                    for line in result.stdout.strip().split("\n"):
                        if line:
                            parts = line.split(maxsplit=1)
                            if len(parts) >= 1:
                                history.append({
                                    "hash": parts[0],
                                    "message": parts[1] if len(parts) > 1 else "no message",
                                    "author": "unknown",
                                    "date": "unknown"
                                })
                    if history:
                        return history

                # 3. 尝试详细格式
                result = subprocess.run(
                    ["git", "--no-pager", "log", "-n", str(limit), "--pretty=format:%H|%s|%an|%ci"],
                    cwd=self.project_root,
                    capture_output=True,
                    text=True,
                    encoding='utf-8',
                    errors='replace',
                    check=False
                )

                if result.returncode == 0 and result.stdout.strip():
                    for line in result.stdout.strip().split("\n"):
                        if line:
                            parts = line.split("|")
                            if len(parts) >= 4:
                                history.append({
                                    "hash": parts[0][:7],
                                    "message": parts[1],
                                    "author": parts[2],
                                    "date": parts[3]
                                })
                    if history:
                        return history

                # 如果都失败了,进行最后的诊断
                check_head = subprocess.run(
                    ["git", "rev-parse", "HEAD"],
                    cwd=self.project_root,
                    capture_output=True,
                    text=True,
                    check=False
                )

                if check_head.returncode == 0:
                    count_res = subprocess.run(
                        ["git", "rev-list", "--count", "HEAD"],
                        cwd=self.project_root,
                        capture_output=True,
                        text=True,
                        check=False
                    )
                    count = count_res.stdout.strip() if count_res.returncode == 0 else "unknown"
                    logger.warning(
                        f"Git 仓库存在 HEAD (提交数: {count}) 但无法获取 log 详情. "
                        f"Root: {self.project_root}"
                    )
                else:
                    logger.warning(f"Git 仓库可能尚未初始化或没有提交. Root: {self.project_root}")

        except Exception as e:
            logger.error(f"获取提交历史失败: {e}")

        return history

    def get_status(self) -> Dict[str, Any]:
        """获取 Git 状态

        Returns:
            Git 状态信息
        """
        status = {
            "enabled": self.enabled,
            "repository_exists": False,
            "branch": None,
            "uncommitted_changes": False,
            "latest_commit": None
        }

        if not self.enabled:
            return status

        try:
            # 检查仓库是否存在
            status["repository_exists"] = (self.project_root / ".git").exists()

            if status["repository_exists"]:
                # 获取当前分支
                if self.repo:
                    status["branch"] = self.repo.active_branch.name
                else:
                    result = subprocess.run(
                        ["git", "branch", "--show-current"],
                        cwd=self.project_root,
                        capture_output=True,
                        text=True
                    )
                    status["branch"] = (
                        result.stdout.strip()
                        if (result.returncode == 0 and result.stdout)
                        else None
                    )

                # 获取最新提交
                history = self.get_commit_history(limit=1)
                if history:
                    status["latest_commit"] = history[0]

        except Exception as e:
            logger.error(f"获取 Git 状态失败: {e}")

        return status

    async def initialize_repository(self) -> bool:
        """初始化 Git 仓库

        Returns:
            是否成功初始化
        """
        try:
            # 检查是否已初始化
            if (self.project_root / ".git").exists():
                logger.info("Git 仓库已存在")
                return True

            # 初始化仓库
            subprocess.run(
                ["git", "init"],
                cwd=self.project_root,
                capture_output=True,
                check=True
            )

            logger.info("Git 仓库已初始化")

            # 创建 .gitignore (如果不存在)
            gitignore_path = self.project_root / ".gitignore"
            if not gitignore_path.exists():
                gitignore_content = """# SuperAgent
.superagent/
tasks.json.bak

# Python
__pycache__/
*.pyc
.pytest_cache/

# Node.js
node_modules/
.env.local

# IDE
.vscode/
.idea/
*.swp
*.swo
"""
                gitignore_path.write_text(gitignore_content, encoding='utf-8')

                # 添加 .gitignore
                subprocess.run(
                    ["git", "add", ".gitignore"],
                    cwd=self.project_root,
                    capture_output=True,
                    check=True
                )

            # 初始提交
            subprocess.run(
                ["git", "commit", "--allow-empty", "-m", "chore: 初始化 SuperAgent 项目"],
                cwd=self.project_root,
                capture_output=True,
                check=True
            )

            logger.info("已创建初始 Git commit")

            return True

        except subprocess.CalledProcessError as e:
            logger.error(f"初始化 Git 仓库失败: {e}")
            return False
        except Exception as e:
            logger.error(f"初始化异常: {e}")
            return False
