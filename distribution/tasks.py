#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Celery 任务定义
"""

import asyncio
import logging
from typing import Dict, Any
from .celery_app import app
from orchestration.task_executor import TaskExecutor
from orchestration.models import TaskExecution, ExecutionContext

logger = logging.getLogger(__name__)

@app.task(name="distribution.tasks.execute_task")
def execute_task(task_data: Dict[str, Any], context_data: Dict[str, Any]) -> Dict[str, Any]:
    """执行单个任务的 Celery 任务包装器

    Args:
        task_data: 任务执行对象的字典表示
        context_data: 执行上下文的字典表示

    Returns:
        Dict[str, Any]: 序列化后的 TaskExecution 结果
    """
    async def _run():
        # 重建上下文和任务对象
        context = ExecutionContext.from_dict(context_data)
        task_execution = TaskExecution.from_dict(task_data)
        
        # 创建执行器
        executor = TaskExecutor(context)
        
        # 执行
        result_task = await executor.execute(task_execution)
        
        # 返回完整的序列化对象
        return result_task.to_dict()

    # 运行异步代码
    try:
        # 使用新的事件循环运行
        return asyncio.run(_run())
    except Exception as e:
        logger.error(f"Celery 任务执行失败 ({type(e).__name__}): {e}", exc_info=True)
        # 如果失败,至少返回基本的状态信息
        return {
            "status": "failed",
            "error": f"({type(e).__name__}) {str(e)}",
            "completed_at": datetime.now().isoformat()
        }
