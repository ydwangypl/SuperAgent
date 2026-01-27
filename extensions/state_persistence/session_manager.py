#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
会话状态管理器

管理多轮会话的状态持久化和恢复。
"""

import asyncio
import logging
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional
from enum import Enum

from .state_serializer import StateFileManager, JSONSerializer

logger = logging.getLogger(__name__)


class SessionStatus(Enum):
    """会话状态"""
    ACTIVE = "active"
    PAUSED = "paused"
    COMPLETED = "completed"
    ERROR = "error"


@dataclass
class SessionCheckpoint:
    """会话检查点"""
    session_id: str
    checkpoint_id: str
    timestamp: str
    task_status: Dict[str, str]
    memory_summary: Dict[str, Any]
    context_summary: str
    created_at: datetime = field(default_factory=datetime.now)


@dataclass
class RecoveryReport:
    """恢复报告"""
    session_id: str
    was_recovered: bool
    last_checkpoint: Optional[SessionCheckpoint]
    changes_since_checkpoint: List[str]
    recovered_state: Dict[str, Any]
    catchup_suggestions: List[str]


class SessionManager:
    """会话状态管理器"""

    def __init__(
        self,
        project_root: Path,
        state_dir: Path = None,
        auto_checkpoint_interval: int = 10
    ):
        self.project_root = Path(project_root)
        self.state_dir = state_dir or self.project_root / ".superagent" / "sessions"
        self.state_file_manager = StateFileManager(self.state_dir, JSONSerializer())
        self.auto_checkpoint_interval = auto_checkpoint_interval

        self._current_session_id: Optional[str] = None
        self._checkpoint_counter = 0
        self._last_checkpoint_time = None

    @property
    def current_session_id(self) -> Optional[str]:
        return self._current_session_id

    async def start_session(
        self,
        session_id: str = None,
        initial_state: Optional[Dict[str, Any]] = None
    ) -> str:
        """开始新会话"""
        self._current_session_id = session_id or datetime.now().strftime('%Y%m%d_%H%M%S')
        self._checkpoint_counter = 0
        self._last_checkpoint_time = datetime.now()

        # 保存初始状态
        state = initial_state or {}
        state["session_id"] = self._current_session_id
        state["status"] = SessionStatus.ACTIVE.value
        state["started_at"] = datetime.now().isoformat()
        state["checkpoints"] = []

        await self.state_file_manager.save_state(self._current_session_id, state)
        logger.info(f"会话已开始: {self._current_session_id}")

        return self._current_session_id

    async def create_checkpoint(
        self,
        task_status: Dict[str, str],
        memory_summary: Dict[str, Any],
        context_summary: str = ""
    ) -> SessionCheckpoint:
        """创建会话检查点"""
        if not self._current_session_id:
            raise RuntimeError("没有活动的会话")

        self._checkpoint_counter += 1
        checkpoint_id = f"cp_{self._checkpoint_counter}"

        checkpoint = SessionCheckpoint(
            session_id=self._current_session_id,
            checkpoint_id=checkpoint_id,
            timestamp=datetime.now().isoformat(),
            task_status=task_status,
            memory_summary=memory_summary,
            context_summary=context_summary
        )

        # 保存检查点到状态文件
        state = await self.state_file_manager.load_state(self._current_session_id)
        if state:
            if "checkpoints" not in state:
                state["checkpoints"] = []

            state["checkpoints"].append({
                "checkpoint_id": checkpoint_id,
                "timestamp": checkpoint.timestamp,
                "task_status": task_status,
                "memory_summary": memory_summary,
                "context_summary": context_summary
            })

            await self.state_file_manager.save_state(self._current_session_id, state)

        self._last_checkpoint_time = datetime.now()
        logger.info(f"检查点已创建: {checkpoint_id}")

        return checkpoint

    async def end_session(
        self,
        status: SessionStatus = SessionStatus.COMPLETED,
        final_state: Optional[Dict[str, Any]] = None
    ) -> None:
        """结束会话"""
        if not self._current_session_id:
            return

        state = await self.state_file_manager.load_state(self._current_session_id)
        if state:
            state["status"] = status.value
            state["ended_at"] = datetime.now().isoformat()
            if final_state:
                state["final_state"] = final_state

            await self.state_file_manager.save_state(self._current_session_id, state)

        logger.info(f"会话已结束: {self._current_session_id} (状态: {status.value})")
        self._current_session_id = None
        self._checkpoint_counter = 0

    async def recover_session(
        self,
        session_id: str
    ) -> RecoveryReport:
        """恢复会话"""
        state = await self.state_file_manager.load_state(session_id)
        if not state:
            return RecoveryReport(
                session_id=session_id,
                was_recovered=False,
                last_checkpoint=None,
                changes_since_checkpoint=[],
                recovered_state={},
                catchup_suggestions=[f"找不到会话 {session_id} 的状态文件"]
            )

        # 获取最后一个检查点
        checkpoints = state.get("checkpoints", [])
        last_checkpoint = None
        if checkpoints:
            last_checkpoint_data = checkpoints[-1]
            last_checkpoint = SessionCheckpoint(
                session_id=session_id,
                checkpoint_id=last_checkpoint_data["checkpoint_id"],
                timestamp=last_checkpoint_data["timestamp"],
                task_status=last_checkpoint_data["task_status"],
                memory_summary=last_checkpoint_data["memory_summary"],
                context_summary=last_checkpoint_data.get("context_summary", "")
            )

        # 计算需要恢复的状态
        recovered_state = {
            "session_id": session_id,
            "status": SessionStatus.ACTIVE.value,
            "restored_from": last_checkpoint.checkpoint_id if last_checkpoint else "initial",
            "restored_at": datetime.now().isoformat(),
            "tasks": last_checkpoint.task_status if last_checkpoint else state.get("tasks", {}),
            "memory": last_checkpoint.memory_summary if last_checkpoint else state.get("memory", {})
        }

        # 生成追赶建议
        catchup_suggestions = []
        if last_checkpoint:
            catchup_suggestions = [
                f"从检查点 {last_checkpoint.checkpoint_id} 恢复",
                f"检查点时间: {last_checkpoint.timestamp}",
                f"已完成的记忆: {len(last_checkpoint.memory_summary.get('memories', []))} 条"
            ]

        return RecoveryReport(
            session_id=session_id,
            was_recovered=True,
            last_checkpoint=last_checkpoint,
            changes_since_checkpoint=[],
            recovered_state=recovered_state,
            catchup_suggestions=catchup_suggestions
        )

    async def get_session_history(self, limit: int = 10) -> List[Dict[str, Any]]:
        """获取会话历史"""
        states = await self.state_file_manager.list_states()
        history = []

        for state_info in states[:limit]:
            state = await self.state_file_manager.load_state(state_info["session_id"])
            if state:
                history.append({
                    "session_id": state_info["session_id"],
                    "status": state.get("status", "unknown"),
                    "started_at": state.get("started_at", ""),
                    "ended_at": state.get("ended_at", ""),
                    "checkpoint_count": len(state.get("checkpoints", [])),
                    "modified_at": state_info["modified_at"]
                })

        return history

    async def should_auto_checkpoint(self, action_count: int) -> bool:
        """判断是否应该自动创建检查点"""
        if not self._current_session_id:
            return False

        # 检查动作数量
        if action_count >= self.auto_checkpoint_interval:
            return True

        # 检查时间间隔
        if self._last_checkpoint_time:
            elapsed = (datetime.now() - self._last_checkpoint_time).total_seconds()
            if elapsed >= 300:  # 5分钟
                return True

        return False
