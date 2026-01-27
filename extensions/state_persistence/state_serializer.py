#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
状态序列化器

负责将执行状态序列化和反序列化，支持多种格式。
"""

import asyncio
import json
import pickle
from abc import ABC, abstractmethod
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional
import logging

logger = logging.getLogger(__name__)


class StateSerializer(ABC):
    """状态序列化器基类"""

    @abstractmethod
    async def serialize(self, state: Dict[str, Any]) -> str:
        """序列化状态"""
        pass

    @abstractmethod
    async def deserialize(self, data: str) -> Dict[str, Any]:
        """反序列化状态"""
        pass


class JSONSerializer(StateSerializer):
    """JSON 格式序列化器"""

    async def serialize(self, state: Dict[str, Any]) -> str:
        """将状态序列化为 JSON 字符串"""
        # 添加元数据
        state["_metadata"] = {
            "serialized_at": datetime.now().isoformat(),
            "version": "1.0"
        }
        return json.dumps(state, ensure_ascii=False, indent=2)

    async def deserialize(self, data: str) -> Dict[str, Any]:
        """从 JSON 字符串反序列化状态"""
        try:
            state = json.loads(data)
            # 移除元数据
            state.pop("_metadata", None)
            return state
        except json.JSONDecodeError as e:
            logger.error(f"JSON 反序列化失败: {e}")
            raise


class PickleSerializer(StateSerializer):
    """Pickle 格式序列化器"""

    async def serialize(self, state: Dict[str, Any]) -> str:
        """将状态序列化为 Base64 编码的 pickle"""
        import base64
        pickle_data = pickle.dumps(state)
        return base64.b64encode(pickle_data).decode('utf-8')

    async def deserialize(self, data: str) -> Dict[str, Any]:
        """从 Base64 编码的 pickle 反序列化状态"""
        import base64
        try:
            pickle_data = base64.b64decode(data.encode('utf-8'))
            return pickle.loads(pickle_data)
        except Exception as e:
            logger.error(f"Pickle 反序列化失败: {e}")
            raise


class StateFileManager:
    """状态文件管理器"""

    def __init__(
        self,
        state_dir: Path,
        serializer: StateSerializer = None
    ):
        self.state_dir = Path(state_dir)
        self.serializer = serializer or JSONSerializer()
        self.state_dir.mkdir(parents=True, exist_ok=True)

    def get_state_path(self, session_id: str) -> Path:
        """获取状态文件路径"""
        return self.state_dir / f"state_{session_id}.json"

    async def save_state(
        self,
        session_id: str,
        state: Dict[str, Any]
    ) -> Path:
        """保存状态到文件"""
        path = self.get_state_path(session_id)
        serialized = await self.serializer.serialize(state)
        path.write_text(serialized, encoding='utf-8')
        logger.info(f"状态已保存: {path}")
        return path

    async def load_state(self, session_id: str) -> Optional[Dict[str, Any]]:
        """从文件加载状态"""
        path = self.get_state_path(session_id)
        if not path.exists():
            return None

        try:
            data = path.read_text(encoding='utf-8')
            state = await self.serializer.deserialize(data)
            logger.info(f"状态已加载: {path}")
            return state
        except Exception as e:
            logger.error(f"加载状态失败: {e}")
            return None

    async def delete_state(self, session_id: str) -> bool:
        """删除状态文件"""
        path = self.get_state_path(session_id)
        if path.exists():
            path.unlink()
            logger.info(f"状态已删除: {path}")
            return True
        return False

    async def list_states(self) -> list:
        """列出所有保存的状态"""
        states = []
        for f in self.state_dir.glob("state_*.json"):
            stat = f.stat()
            states.append({
                "session_id": f.stem.replace("state_", ""),
                "path": str(f),
                "modified_at": datetime.fromtimestamp(stat.st_mtime).isoformat(),
                "size": stat.st_size
            })
        return states

    async def cleanup_old_states(self, max_age_hours: int = 24) -> int:
        """清理过期的状态文件"""
        import time

        cutoff = time.time() - max_age_hours * 3600
        removed = 0

        for f in self.state_dir.glob("state_*.json"):
            if f.stat().st_mtime < cutoff:
                f.unlink()
                removed += 1

        logger.info(f"已清理 {removed} 个过期状态文件")
        return removed
