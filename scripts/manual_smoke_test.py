import asyncio
from pathlib import Path
from orchestration.models import TaskExecution, OrchestrationConfig, SingleTaskConfig, ExecutionContext, TaskStatus
from orchestration.task_executor import TaskExecutor
from memory.memory_manager import MemoryManager
from common.models import AgentType

async def manual_smoke_test():
    print("--- 开始人工全链路冒烟测试 ---")
    project_root = Path(".").absolute()
    
    # 1. 初始化记忆管理器
    memory_manager = MemoryManager(project_root / "temp_memory")
    
    # 2. 初始化任务执行器
    context = ExecutionContext(project_root=project_root)
    executor = TaskExecutor(context)
    
    # 3. 创建模拟任务
    task = TaskExecution(
        task_id="smoke-task-001",
        step_id="step-001",
        status=TaskStatus.PENDING,
        inputs={"files": ["smoke_test_file.txt"], "description": "测试任务: 创建一个测试文件"}
    )
    # 模拟 agent_type，因为 TaskExecution 可能没有这个字段或者它是可选的
    task.agent_type = AgentType.BACKEND_DEV
    
    print(f"准备执行任务: {task.task_id}")
    
    # 4. 存储记忆
    await memory_manager.save_episodic_memory(
        task_id=task.task_id,
        event="完成了人工冒烟测试",
        metadata={"success": True}
    )
    print("记忆已存储")
    
    # 5. 读取记忆
    # 注意: MemoryManager 的搜索方法叫 query_semantic_memory
    memories = await memory_manager.query_semantic_memory(category="general")
    print(f"查询到语义记忆条数: {len(memories)}")
    
    # 6. 存储语义记忆
    await memory_manager.save_semantic_memory(
        knowledge="SuperAgent 冒烟测试知识点",
        category="testing",
        tags=["smoke-test", "v3.2"]
    )
    print("语义记忆已存储")
    
    memories_testing = await memory_manager.query_semantic_memory(category="testing")
    print(f"查询到 testing 类别语义记忆条数: {len(memories_testing)}")

    print("--- 人工全链路冒烟测试完成 ---")

if __name__ == "__main__":
    asyncio.run(manual_smoke_test())
