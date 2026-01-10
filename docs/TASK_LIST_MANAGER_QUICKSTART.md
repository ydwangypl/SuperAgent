# TaskListManager 快速开始指南

**快速上手 tasks.json 结构化任务清单**

---

## 🚀 30 秒快速开始

```python
from core.task_list_manager import TaskListManager
from pathlib import Path

# 1. 创建管理器
manager = TaskListManager(Path("./your_project"))

# 2. 从 ExecutionPlan 创建任务列表
task_list = manager.create_from_plan(your_execution_plan)

# 3. 查看进度
manager.print_progress()
```

---

## 📋 常见用法

### **创建任务列表**

```python
# 从 ExecutionPlan 创建
task_list = manager.create_from_plan(plan)

# 手动创建
from core.task_list_manager import TaskItem, TaskList

task_list = TaskList(
    project_name="MyProject",
    total_tasks=3,
    tasks=[
        TaskItem(id="task-001", description="功能1"),
        TaskItem(id="task-002", description="功能2"),
        TaskItem(id="task-003", description="功能3")
    ]
)

manager.task_list = task_list
manager.save()
```

### **执行任务**

```python
# 获取下一个任务
task = manager.get_next_task()

# 标记为运行中
manager.update_task(task.id, "running")

# 执行任务...
result = await execute(task)

# 标记为完成
manager.update_task(task.id, "completed")

# 或标记为失败
manager.update_task(task.id, "failed", error="错误信息")
```

### **查看进度**

```python
# 方式 1: 打印报告
manager.print_progress()

# 方式 2: 获取详细状态
status = manager.get_status()
print(f"进度: {status['percentage']}%")

# 方式 3: 访问任务列表
task_list = manager.load_or_create()
print(f"已完成: {task_list.completed}/{task_list.total_tasks}")
```

### **断点续传**

```python
# 第一次运行
manager = TaskListManager(project_root)
manager.create_from_plan(plan)

# 执行一些任务...

# 程序中断...

# 第二次运行 (自动恢复)
manager2 = TaskListManager(project_root)
loaded_list = manager2.load_or_create()
print(f"恢复进度: {loaded_list.completed}/{loaded_list.total_tasks}")
```

---

## 🔧 高级用法

### **带依赖关系的任务**

```python
task_list = TaskList(
    project_name="MyProject",
    total_tasks=3,
    tasks=[
        TaskItem(
            id="task-001",
            description="设计数据库",
            status="completed"
        ),
        TaskItem(
            id="task-002",
            description="实现 API",
            dependencies=["task-001"]  # 依赖 task-001
        ),
        TaskItem(
            id="task-003",
            description="编写测试",
            dependencies=["task-002"]  # 依赖 task-002
        )
    ]
)

# get_next_pending() 会自动检查依赖
# task-002 可用 (task-001 已完成)
# task-003 不可用 (task-002 未完成)
```

### **Agent 类型过滤**

```python
# 为任务分配 Agent
for task in task_list.tasks:
    if "API" in task.description:
        task.assigned_agent = "backend-dev"
    elif "UI" in task.description:
        task.assigned_agent = "frontend-dev"

# 获取特定 Agent 的任务
backend_task = manager.get_next_task(agent_type="backend-dev")
```

### **带测试步骤的任务**

```python
task = TaskItem(
    id="task-001",
    description="实现用户注册",
    test_steps=[
        "创建注册 API 端点",
        "验证邮箱格式",
        "测试密码哈希",
        "验证 JWT token 生成"
    ]
)
```

---

## 📄 tasks.json 文件

### **文件位置**

```
your_project/
└── tasks.json
```

### **查看内容**

```bash
cat tasks.json
```

```json
{
  "project_name": "MyProject",
  "total_tasks": 3,
  "completed": 1,
  "pending": 2,
  "failed": 0,
  "last_updated": "2025-01-11T01:47:49.123456",
  "tasks": [...]
}
```

---

## 🎯 API 快速参考

### **TaskListManager 方法**

| 方法 | 说明 | 返回值 |
|------|------|--------|
| `create_from_plan(plan)` | 从 ExecutionPlan 创建 | TaskList |
| `load_or_create()` | 加载或创建任务列表 | TaskList or None |
| `save()` | 保存当前任务列表 | None |
| `get_next_task(agent_type)` | 获取下一个待执行任务 | TaskItem or None |
| `update_task(id, status, error)` | 更新任务状态 | None |
| `print_progress()` | 打印进度报告 | None |
| `get_status()` | 获取详细状态信息 | Dict |

### **TaskList 方法**

| 方法 | 说明 | 返回值 |
|------|------|--------|
| `save(path)` | 保存到文件 | None |
| `load(path)` (类方法) | 从文件加载 | TaskList |
| `get_next_pending(agent_type)` | 获取下一个待执行任务 | TaskItem or None |
| `mark_progress(id, status, error)` | 标记任务进度 | None |
| `get_progress_report()` | 获取进度报告 | Dict |
| `print_progress()` | 打印进度报告 | None |
| `update_statistics()` | 更新统计信息 | None |

---

## 💡 提示与最佳实践

### **1. 定期保存**

```python
# 每次更新后自动保存
manager.update_task(task_id, status)
manager.save()  # 自动保存
```

### **2. 错误处理**

```python
try:
    result = await execute_task(task)
    manager.update_task(task.id, "completed")
except Exception as e:
    manager.update_task(task.id, "failed", error=str(e))
```

### **3. 进度监控**

```python
# 定期打印进度
for i in range(len(tasks)):
    task = manager.get_next_task()
    await execute(task)
    manager.update_task(task.id, "completed")

    if (i + 1) % 5 == 0:
        manager.print_progress()  # 每 5 个任务打印一次
```

### **4. 任务状态**

```python
status = "pending"     # 待执行
status = "running"     # 执行中
status = "completed"   # 已完成
status = "failed"      # 失败
```

---

## 🔗 相关资源

- **API 文档**: [`core/task_list_manager.py`](../core/task_list_manager.py)
- **单元测试**: [`tests/unit/test_task_list_manager.py`](../tests/unit/test_task_list_manager.py)
- **演示脚本**: [`examples/task_list_simple_demo.py`](../examples/task_list_simple_demo.py)
- **实施报告**: [`docs/TASK_LIST_MANAGER_COMPLETION.md`](TASK_LIST_MANAGER_COMPLETION.md)

---

## 🆘 常见问题

### **Q: tasks.json 在哪里?**

A: 在项目根目录,与 `core/` 同级。

### **Q: 如何恢复中断的任务?**

A: 重新创建 TaskListManager 并调用 `load_or_create()`:

```python
manager = TaskListManager(project_root)
task_list = manager.load_or_create()  # 自动加载
```

### **Q: 如何查看所有任务?**

A: 加载任务列表并访问 `tasks` 属性:

```python
task_list = manager.load_or_create()
for task in task_list.tasks:
    print(f"{task.id}: {task.description} - {task.status}")
```

### **Q: 如何重置任务状态?**

A: 修改任务状态并保存:

```python
for task in task_list.tasks:
    if task.status == "failed":
        task.status = "pending"
        task.error = None

manager.save()
```

---

**文档版本**: v1.0
**最后更新**: 2026-01-11
