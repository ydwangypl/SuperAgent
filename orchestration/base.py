#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
编排器基类 (BaseOrchestrator)

为所有子编排器提供统一的接口和基础功能
"""

from abc import ABC
from pathlib import Path
from typing import Optional
from .models import OrchestrationConfig

class BaseOrchestrator(ABC):
    """
    编排器基类
    
    Extension Guide:
        1. 继承 BaseOrchestrator 类。
        2. 实现核心业务逻辑方法 (如 run(), execute_task() 等)。
        3. 如果需要自定义初始化逻辑，请务必调用 super().__init__(project_root, config)。
        4. 推荐在子类中注入特定的工具类 (如 AgentDispatcher, WorktreeManager 等)。

    Example:
        class MyCustomOrchestrator(BaseOrchestrator):
            def __init__(self, project_root, config=None, my_tool=None):
                super().__init__(project_root, config)
                self.my_tool = my_tool
            
            async def run(self, task_desc: str):
                # 实现具体的编排逻辑
                pass
    """

    def __init__(
        self, 
        project_root: Path, 
        config: Optional[OrchestrationConfig] = None
    ) -> None:
        """初始化编排器

        Args:
            project_root: 项目根目录
            config: 编排配置
        """
        self.project_root = Path(project_root)
        self.config = config or OrchestrationConfig()
