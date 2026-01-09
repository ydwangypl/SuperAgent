#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
分布式任务执行器

使用 Celery 将任务分发到工作节点执行
"""

import logging
import asyncio
from typing import List, Dict, Any, Optional
from datetime import datetime

from .models import TaskExecution, TaskStatus, ExecutionContext
from .task_executor import TaskExecutor
from config.settings import SuperAgentConfig

logger = logging.getLogger(__name__)

class DistributedTaskExecutor(TaskExecutor):
    """分布式任务执行器"""

    def __init__(self, context: ExecutionContext, config: SuperAgentConfig):
        """初始化分布式任务执行器

        Args:
            context: 执行上下文
            config: 全局配置
        """
        super().__init__(context)
        self.config = config
        self.use_distribution = config.distribution.enabled

    async def execute(
        self,
        task_execution: TaskExecution,
        timeout: int = 3600
    ) -> TaskExecution:
        """执行任务 (如果启用分布式则分发,否则本地执行)

        Args:
            task_execution: 任务执行对象
            timeout: 超时时间(秒)

        Returns:
            TaskExecution: 更新后的任务执行对象
        """
        if not self.use_distribution:
            return await super().execute(task_execution, timeout)

        logger.info(f"分发分布式任务: {task_execution.task_id}")
        
        # 更新状态
        task_execution.status = TaskStatus.RUNNING
        task_execution.started_at = datetime.now()
        
        try:
            # 导入 Celery 任务 (延迟导入避免循环依赖)
            from distribution.tasks import execute_task
            
            # 准备数据 (使用统一的序列化方法)
            task_data = task_execution.to_dict()
            context_data = self.context.to_dict()
            
            # 发送任务到 Celery
            celery_task = execute_task.delay(task_data, context_data)
            
            # 等待结果 (异步非阻塞等待)
            # 使用指数退避策略轮询
            start_time = datetime.now()
            wait_time = 0.5
            while not celery_task.ready():
                if (datetime.now() - start_time).total_seconds() > timeout:
                    # 尝试取消远程任务
                    celery_task.revoke(terminate=True)
                    raise asyncio.TimeoutError(f"分布式任务执行超时: {task_execution.task_id}")
                
                await asyncio.sleep(wait_time)
                # 指数增加等待时间,最大 2 秒 (高频轮询)
                wait_time = min(wait_time * 1.2, 2.0)
            
            # 获取执行结果 (已经是字典形式的 TaskExecution)
            result_dict = celery_task.get(timeout=timeout)
            
            # 使用 from_dict 更新当前任务状态
            remote_task = TaskExecution.from_dict(result_dict)
            
            # 更新本地任务对象的状态和结果
            task_execution.status = remote_task.status
            task_execution.completed_at = remote_task.completed_at or datetime.now()
            task_execution.result = remote_task.result
            task_execution.outputs = remote_task.outputs
            task_execution.error = remote_task.error
            task_execution.logs.extend(remote_task.logs)
            task_execution.logs.append("分布式任务执行同步完成")
            
            logger.info(f"分布式任务执行完成: {task_execution.task_id}, 状态: {task_execution.status.value}")
            
        except asyncio.TimeoutError as e:
            task_execution.status = TaskStatus.FAILED
            task_execution.completed_at = datetime.now()
            task_execution.error = f"超时: {str(e)}"
            task_execution.logs.append(f"分布式任务执行超时: {str(e)}")
            logger.error(f"分布式任务执行超时: {task_execution.task_id}")
        except ImportError as e:
            task_execution.status = TaskStatus.FAILED
            task_execution.completed_at = datetime.now()
            task_execution.error = f"分布式依赖缺失: {str(e)}"
            task_execution.logs.append(f"分布式任务分发失败 (ImportError): {str(e)}")
            logger.error(f"分布式任务分发失败, 无法加载 distribution.tasks: {e}")
        except Exception as e:
            task_execution.status = TaskStatus.FAILED
            task_execution.completed_at = datetime.now()
            task_execution.error = f"分布式执行异常 ({type(e).__name__}): {str(e)}"
            task_execution.logs.append(f"分布式任务执行遇到非预期异常: {str(e)}")
            logger.error(f"分布式任务执行失败: {task_execution.task_id}, 错误类型: {type(e).__name__}, 错误: {e}")
            
        return task_execution

    async def execute_batch(
        self,
        task_executions: List[TaskExecution],
        max_concurrent: int = 10
    ) -> List[TaskExecution]:
        """批量执行分布式任务

        Args:
            task_executions: 任务执行对象列表
            max_concurrent: 最大并发数

        Returns:
            List[TaskExecution]: 更新后的任务执行对象列表
        """
        if not self.use_distribution:
            return await super().execute_batch(task_executions, max_concurrent)

        logger.info(f"批量分发 {len(task_executions)} 个分布式任务")
        
        # 并发执行
        tasks = [self.execute(task) for task in task_executions]
        return await asyncio.gather(*tasks)
