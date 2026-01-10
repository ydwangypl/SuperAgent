#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
TaskListManager 功能演示

展示 tasks.json 结构化任务清单的核心功能。
"""

import sys
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from core.task_list_manager import TaskItem, TaskList, TaskListManager


def demo_basic_usage():
    """演示基本使用"""
    import sys
    import io

    # 设置 UTF-8 编码输出
    if sys.platform == "win32":
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

    print("=" * 60)
    print("TaskListManager 基本功能演示")
    print("=" * 60)

    # 1. 创建任务列表管理器
    print("\n1️⃣  创建任务列表管理器")
    manager = TaskListManager(project_root)
    print(f"✅ 管理器已创建")
    print(f"   任务文件: {manager.tasks_json_path}")

    # 2. 模拟从 ExecutionPlan 创建任务列表
    print("\n2️⃣  从执行计划创建任务列表")

    # 模拟 ExecutionPlan
    class MockStep:
        def __init__(self, id, description, agent_type="general"):
            self.id = id
            self.description = description
            self.agent_type = agent_type

    class MockPlan:
        project_id = "TodoApp"
        steps = [
            MockStep("step-001", "设计数据库模型", "database-design"),
            MockStep("step-002", "实现用户注册 API", "backend-dev"),
            MockStep("step-003", "创建注册表单", "frontend-dev"),
            MockStep("step-004", "添加表单验证", "frontend-dev"),
            MockStep("step-005", "编写单元测试", "qa-engineering")
        ]

    plan = MockPlan()
    task_list = manager.create_from_plan(plan)

    print(f"✅ 已创建任务列表")
    print(f"   项目: {task_list.project_name}")
    print(f"   任务数: {task_list.total_tasks}")

    # 3. 显示初始进度
    print("\n3️⃣  初始进度")
    task_list.print_progress()

    # 4. 模拟执行任务
    print("\n4️⃣  执行任务...")

    # 执行第一个任务
    task_1 = manager.get_next_task()
    print(f"\n📝 执行任务: {task_1.description}")
    manager.update_task(task_1.id, "running")
    manager.update_task(task_1.id, "completed")
    print("✅ 任务完成")

    # 执行第二个任务
    task_2 = manager.get_next_task()
    print(f"\n📝 执行任务: {task_2.description}")
    manager.update_task(task_2.id, "running")
    manager.update_task(task_2.id, "completed")
    print("✅ 任务完成")

    # 5. 显示当前进度
    print("\n5️⃣  当前进度")
    manager.print_progress()

    # 6. 模拟任务失败
    print("\n6️⃣  模拟任务失败...")
    task_3 = manager.get_next_task()
    print(f"\n📝 执行任务: {task_3.description}")
    manager.update_task(task_3.id, "failed", error="组件渲染异常")
    print("❌ 任务失败")

    # 7. 显示最终状态
    print("\n7️⃣  最终状态")
    manager.print_progress()

    # 8. 获取详细状态
    print("\n8️⃣  详细状态信息")
    status = manager.get_status()
    print(f"初始化: {status['initialized']}")
    print(f"项目: {status['project_name']}")
    print(f"总任务: {status['total_tasks']}")
    print(f"已完成: {status['completed']}")
    print(f"待执行: {status['pending']}")
    print(f"失败: {status['failed']}")
    print(f"进度: {status['percentage']}%")

    # 9. 演示断点续传
    print("\n9️⃣  演示断点续传...")
    print("创建新的管理器实例...")

    # 新建管理器实例
    manager2 = TaskListManager(project_root)
    loaded_list = manager2.load_or_create()

    if loaded_list:
        print("✅ 成功从文件加载任务列表")
        print(f"   项目: {loaded_list.project_name}")
        print(f"   已完成: {loaded_list.completed}/{loaded_list.total_tasks}")
    else:
        print("❌ 未找到任务列表")

    print("\n" + "=" * 60)
    print("✅ 演示完成!")
    print("=" * 60)


def demo_advanced_features():
    """演示高级特性"""
    print("\n\n" + "=" * 60)
    print("🚀 TaskListManager 高级特性演示")
    print("=" * 60)

    manager = TaskListManager(project_root)

    # 1. 带依赖关系的任务
    print("\n1️⃣  创建带依赖关系的任务列表")

    task_list = TaskList(
        project_name="BlogSystem",
        total_tasks=5,
        tasks=[
            TaskItem(
                id="task-001",
                description="设计数据库模型",
                status="completed"
            ),
            TaskItem(
                id="task-002",
                description="实现文章模型",
                dependencies=["task-001"]
            ),
            TaskItem(
                id="task-003",
                description="实现用户模型",
                dependencies=["task-001"]
            ),
            TaskItem(
                id="task-004",
                description="创建文章 API",
                dependencies=["task-002"]
            ),
            TaskItem(
                id="task-005",
                description="创建用户 API",
                dependencies=["task-003"]
            )
        ]
    )

    manager.task_list = task_list
    print(f"✅ 创建了 {task_list.total_tasks} 个任务")
    print(f"   其中 {sum(1 for t in task_list.tasks if t.dependencies)} 个任务有依赖")

    # 2. 演示依赖解析
    print("\n2️⃣  依赖解析演示")
    print("任务依赖关系:")
    print("  task-001 (数据库模型) ✅ 已完成")
    print("    ├─ task-002 (文章模型) - 可执行")
    print("    └─ task-003 (用户模型) - 可执行")
    print("       ├─ task-004 (文章 API) - 等待 task-002")
    print("       └─ task-005 (用户 API) - 等待 task-003")

    # 获取下一个可执行任务
    next_task = manager.get_next_task()
    print(f"\n📌 下一个可执行任务: {next_task.description}")
    print(f"   ID: {next_task.id}")
    print(f"   依赖: {next_task.dependencies}")

    # 3. 演示 Agent 类型过滤
    print("\n3️⃣  Agent 类型过滤演示")

    # 更新任务,指定 Agent 类型
    for task in task_list.tasks:
        if "API" in task.description:
            task.assigned_agent = "backend-dev"
        elif "模型" in task.description:
            task.assigned_agent = "database-design"

    print(f"   backend-dev 任务: {sum(1 for t in task_list.tasks if t.assigned_agent == 'backend-dev')}")
    print(f"   database-design 任务: {sum(1 for t in task_list.tasks if t.assigned_agent == 'database-design')}")

    # 获取特定 Agent 的任务
    backend_task = manager.get_next_task(agent_type="backend-dev")
    print(f"\n📌 下一个 backend-dev 任务: {backend_task.description}")

    print("\n" + "=" * 60)
    print("✅ 高级特性演示完成!")
    print("=" * 60)


def demo_json_structure():
    """演示 JSON 结构"""
    print("\n\n" + "=" * 60)
    print("📄 tasks.json 文件结构演示")
    print("=" * 60)

    # 创建示例任务列表
    task_list = TaskList(
        project_name="DemoProject",
        total_tasks=2,
        tasks=[
            TaskItem(
                id="task-001",
                description="示例任务1",
                status="completed",
                assigned_agent="backend-dev",
                test_steps=["步骤1", "步骤2"],
                dependencies=[],
                metadata={"priority": "high"}
            ),
            TaskItem(
                id="task-002",
                description="示例任务2",
                status="pending",
                assigned_agent="frontend-dev"
            )
        ]
    )

    # 保存到临时文件
    import tempfile
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        temp_path = Path(f.name)

    task_list.save(temp_path)

    # 读取并显示 JSON
    print("\n📄 tasks.json 内容:")
    print("-" * 60)
    with open(temp_path, 'r', encoding='utf-8') as f:
        content = f.read()
        print(content)
    print("-" * 60)

    # 清理临时文件
    temp_path.unlink()

    print("\n✅ JSON 结构演示完成!")
    print("=" * 60)


if __name__ == "__main__":
    # 检查是否在正确的目录
    if not (project_root / "core").exists():
        print("❌ 错误: 请在 SuperAgent 项目根目录运行此脚本")
        sys.exit(1)

    try:
        # 运行演示
        demo_basic_usage()
        demo_advanced_features()
        demo_json_structure()

        print("\n\n🎉 所有演示完成!")
        print("\n💡 提示: tasks.json 文件已创建在项目根目录")
        print("   你可以查看该文件来了解任务列表的结构")

    except Exception as e:
        print(f"\n❌ 演示失败: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
