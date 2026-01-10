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
    print("=" * 60)
    print("TaskListManager 基本功能演示")
    print("=" * 60)

    # 1. 创建任务列表管理器
    print("\n[1] 创建任务列表管理器")
    manager = TaskListManager(project_root)
    print(f"OK 管理器已创建")
    print(f"   任务文件: {manager.tasks_json_path}")

    # 2. 模拟从 ExecutionPlan 创建任务列表
    print("\n[2] 从执行计划创建任务列表")

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

    print(f"OK 已创建任务列表")
    print(f"   项目: {task_list.project_name}")
    print(f"   任务数: {task_list.total_tasks}")

    # 3. 显示初始进度
    print("\n[3] 初始进度")
    task_list.print_progress()

    # 4. 模拟执行任务
    print("\n[4] 执行任务...")

    # 执行第一个任务
    task_1 = manager.get_next_task()
    print(f"\n执行任务: {task_1.description}")
    manager.update_task(task_1.id, "running")
    manager.update_task(task_1.id, "completed")
    print("OK 任务完成")

    # 执行第二个任务
    task_2 = manager.get_next_task()
    print(f"\n执行任务: {task_2.description}")
    manager.update_task(task_2.id, "running")
    manager.update_task(task_2.id, "completed")
    print("OK 任务完成")

    # 5. 显示当前进度
    print("\n[5] 当前进度")
    manager.print_progress()

    # 6. 模拟任务失败
    print("\n[6] 模拟任务失败...")
    task_3 = manager.get_next_task()
    print(f"\n执行任务: {task_3.description}")
    manager.update_task(task_3.id, "failed", error="组件渲染异常")
    print("X 任务失败")

    # 7. 显示最终状态
    print("\n[7] 最终状态")
    manager.print_progress()

    # 8. 获取详细状态
    print("\n[8] 详细状态信息")
    status = manager.get_status()
    print(f"初始化: {status['initialized']}")
    print(f"项目: {status['project_name']}")
    print(f"总任务: {status['total_tasks']}")
    print(f"已完成: {status['completed']}")
    print(f"待执行: {status['pending']}")
    print(f"失败: {status['failed']}")
    print(f"进度: {status['percentage']}%")

    # 9. 演示断点续传
    print("\n[9] 演示断点续传...")
    print("创建新的管理器实例...")

    # 新建管理器实例
    manager2 = TaskListManager(project_root)
    loaded_list = manager2.load_or_create()

    if loaded_list:
        print("OK 成功从文件加载任务列表")
        print(f"   项目: {loaded_list.project_name}")
        print(f"   已完成: {loaded_list.completed}/{loaded_list.total_tasks}")
    else:
        print("X 未找到任务列表")

    print("\n" + "=" * 60)
    print("演示完成!")
    print("=" * 60)


if __name__ == "__main__":
    # 检查是否在正确的目录
    if not (project_root / "core").exists():
        print("错误: 请在 SuperAgent 项目根目录运行此脚本")
        sys.exit(1)

    try:
        # 运行演示
        demo_basic_usage()

        print("\n\n所有演示完成!")
        print("\n提示: tasks.json 文件已创建在项目根目录")
        print("   你可以查看该文件来了解任务列表的结构")

    except Exception as e:
        print(f"\n演示失败: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
