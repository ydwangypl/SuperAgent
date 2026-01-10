# autonomous-coding 借鉴内容清单 (融合版)

**分析日期**: 2026-01-11
**SuperAgent 版本**: v3.1
**参考项目**: [autonomous-coding by leonvanzyl](https://github.com/leonvanzyl/autonomous-coding)
**融合来源**: Claude 原分析 + Grok 建议

---

## 📋 融合方法论

### **整合原则**

1. **保留 SuperAgent 现有优势** (三层架构、多域支持、Worktree 隔离)
2. **采纳 autonomous-coding 核心机制** (feature_list.json、双代理、自动继续)
3. **利用现有依赖** (gitpython、conversation 层、monitoring 层)
4. **低成本高回报** (优先 1-2 天能实现的特性)

---

## 🎯 最终借鉴清单 (按优先级排序)

### **P0 - 第一周实现 (核心基础设施)**

---

## ✨ **#1. 结构化任务清单 (tasks.json)** 📋

**来源**: autonomous-coding 的 `feature_list.json` + Grok 建议

#### **核心价值**

- ✅ **可机读的持久状态追踪** - 解决当前 planning 层任务仅在内存的问题
- ✅ **断点续传** - 中断后读取 JSON 恢复
- ✅ **进度可视化** - `cat tasks.json` 即可查看
- ✅ **结合 3 层记忆** - 避免重复工作

#### **数据模型**

```json
{
  "project_name": "TodoApp",
  "total_tasks": 50,
  "completed": 15,
  "pending": 35,
  "failed": 0,
  "last_updated": "2025-01-15T14:30:00Z",
  "tasks": [
    {
      "id": "task-001",
      "description": "实现用户注册功能",
      "status": "pending",
      "assigned_agent": "backend-dev",
      "test_steps": [
        "创建注册 API 端点",
        "验证邮箱格式",
        "密码哈希处理",
        "返回 JWT token"
      ],
      "dependencies": [],
      "created_at": "2025-01-15T10:00:00Z",
      "started_at": null,
      "completed_at": null,
      "error": null
    }
  ]
}
```

#### **实现方案**

```python
# core/task_list_manager.py
from dataclasses import dataclass, asdict
from typing import List, Optional, Dict, Any
from datetime import datetime
from pathlib import Path
import json
import logging

logger = logging.getLogger(__name__)

@dataclass
class TaskItem:
    """任务项"""
    id: str                                     # 任务 ID
    description: str                            # 描述
    status: str = "pending"                     # pending | running | completed | failed
    assigned_agent: Optional[str] = None        # 分配的 Agent
    test_steps: List[str] = None               # 测试步骤
    dependencies: List[str] = None             # 依赖的任务 ID
    created_at: str = None
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    error: Optional[str] = None

    def __post_init__(self):
        if self.test_steps is None:
            self.test_steps = []
        if self.dependencies is None:
            self.dependencies = []
        if self.created_at is None:
            self.created_at = datetime.now().isoformat()

@dataclass
class TaskList:
    """任务列表"""
    project_name: str
    total_tasks: int
    completed: int = 0
    pending: int = 0
    failed: int = 0
    last_updated: str = None
    tasks: List[TaskItem] = None

    def __post_init__(self):
        if self.tasks is None:
            self.tasks = []
        if self.last_updated is None:
            self.last_updated = datetime.now().isoformat()

    def update_statistics(self):
        """更新统计信息"""
        self.completed = sum(1 for t in self.tasks if t.status == "completed")
        self.pending = sum(1 for t in self.tasks if t.status == "pending")
        self.failed = sum(1 for t in self.tasks if t.status == "failed")
        self.last_updated = datetime.now().isoformat()

    def save(self, path: Path):
        """保存到文件"""
        self.update_statistics()
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(asdict(self), f, indent=2, ensure_ascii=False)
        logger.info(f"✅ 任务列表已保存: {path}")

    @classmethod
    def load(cls, path: Path) -> 'TaskList':
        """从文件加载"""
        with open(path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        tasks = [TaskItem(**t) for t in data.pop('tasks', [])]
        return cls(tasks=tasks, **data)

    def get_next_pending(
        self,
        agent_type: Optional[str] = None
    ) -> Optional[TaskItem]:
        """获取下一个待执行任务

        Args:
            agent_type: 过滤特定 Agent 类型的任务
        """
        # 按依赖关系和优先级排序
        pending_tasks = [
            t for t in self.tasks
            if t.status == "pending"
            and (agent_type is None or t.assigned_agent == agent_type)
            and self._dependencies_satisfied(t)
        ]

        return pending_tasks[0] if pending_tasks else None

    def _dependencies_satisfied(self, task: TaskItem) -> bool:
        """检查依赖是否满足"""
        for dep_id in task.dependencies:
            dep_task = next((t for t in self.tasks if t.id == dep_id), None)
            if not dep_task or dep_task.status != "completed":
                return False
        return True

    def mark_progress(
        self,
        task_id: str,
        status: str,
        error: Optional[str] = None
    ):
        """标记任务进度"""
        for task in self.tasks:
            if task.id == task_id:
                task.status = status

                if status == "running":
                    task.started_at = datetime.now().isoformat()
                elif status in ["completed", "failed"]:
                    task.completed_at = datetime.now().isoformat()
                    if error:
                        task.error = error

                self.update_statistics()
                break

    def get_progress_report(self) -> Dict[str, Any]:
        """获取进度报告"""
        self.update_statistics()
        percentage = (self.completed / self.total_tasks * 100) if self.total_tasks > 0 else 0

        return {
            "project_name": self.project_name,
            "total": self.total_tasks,
            "completed": self.completed,
            "pending": self.pending,
            "failed": self.failed,
            "percentage": round(percentage, 1),
            "last_updated": self.last_updated
        }

class TaskListManager:
    """任务列表管理器"""

    def __init__(self, project_root: Path):
        self.project_root = project_root
        self.tasks_json_path = project_root / "tasks.json"
        self.task_list: Optional[TaskList] = None

    def create_from_plan(
        self,
        plan: 'Plan',
        project_name: str
    ) -> TaskList:
        """从计划创建任务列表

        Args:
            plan: planning 层生成的计划
            project_name: 项目名称
        """
        tasks = [
            TaskItem(
                id=f"task-{i:03d}",
                description=task.description,
                assigned_agent=task.assigned_agent,
                test_steps=task.test_steps if hasattr(task, 'test_steps') else [],
                dependencies=task.dependencies if hasattr(task, 'dependencies') else []
            )
            for i, task in enumerate(plan.tasks, 1)
        ]

        self.task_list = TaskList(
            project_name=project_name,
            total_tasks=len(tasks),
            tasks=tasks
        )

        self.save()
        return self.task_list

    def load_or_create(self) -> TaskList:
        """加载或创建任务列表"""
        if self.tasks_json_path.exists():
            logger.info(f"📂 加载现有任务列表: {self.tasks_json_path}")
            self.task_list = TaskList.load(self.tasks_json_path)
        else:
            logger.info("📝 创建新任务列表 (将在首次运行时生成)")
            self.task_list = None

        return self.task_list

    def save(self):
        """保存任务列表"""
        if self.task_list:
            self.task_list.save(self.tasks_json_path)

    def get_next_task(
        self,
        agent_type: Optional[str] = None
    ) -> Optional[TaskItem]:
        """获取下一个待执行任务"""
        if not self.task_list:
            self.load_or_create()

        if not self.task_list:
            return None

        return self.task_list.get_next_pending(agent_type)

    def update_task(
        self,
        task_id: str,
        status: str,
        error: Optional[str] = None
    ):
        """更新任务状态"""
        if not self.task_list:
            self.load_or_create()

        if self.task_list:
            self.task_list.mark_progress(task_id, status, error)
            self.save()

    def print_progress(self):
        """打印进度报告"""
        if not self.task_list:
            return

        report = self.task_list.get_progress_report()

        print(f"""
📊 任务进度报告: {report['project_name']}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
✅ 已完成: {report['completed']}
⏳ 待执行: {report['pending']}
❌ 失败: {report['failed']}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📈 总进度: {report['percentage']}%
🎯 完成度: {report['completed']}/{report['total']}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
""")
```

#### **集成到 Orchestration 层**

```python
# orchestration/orchestrator.py 修改
from core.task_list_manager import TaskListManager, TaskItem

class Orchestrator(BaseOrchestrator):
    def __init__(self, project_root: Path, ...):
        super().__init__(project_root, ...)
        self.task_list_manager = TaskListManager(project_root)

    async def execute_plan_incremental(self, plan: 'Plan'):
        """增量执行计划 (新方法)"""
        # 1. 创建或加载任务列表
        task_list = self.task_list_manager.load_or_create()

        if not task_list:
            # 首次运行,从计划创建
            task_list = self.task_list_manager.create_from_plan(
                plan=plan,
                project_name=plan.project_name
            )
        else:
            # 已有任务列表,继续执行
            print("🔄 检测到未完成任务,继续执行...")

        # 2. 增量执行任务
        while True:
            # 获取下一个任务
            task_item = self.task_list_manager.get_next_task()

            if not task_item:
                print("✅ 所有任务已完成!")
                break

            # 3. 执行任务
            print(f"📝 执行任务: {task_item.description}")

            task_item.status = "running"
            task_item.started_at = datetime.now().isoformat()
            self.task_list_manager.save()

            try:
                # 调用 execution 层
                result = await self._execute_task_item(task_item)

                # 调用 review 层验证
                review = await self._review_task_result(task_item, result)

                if review.get("approved", False):
                    # 任务完成
                    self.task_list_manager.update_task(
                        task_item.id,
                        "completed"
                    )

                    # 自动 commit (如果启用)
                    if self.config.auto_commit:
                        await self._commit_task(task_item, result)
                else:
                    # 任务失败
                    self.task_list_manager.update_task(
                        task_item.id,
                        "failed",
                        error=review.get("feedback")
                    )

            except Exception as e:
                logger.error(f"任务执行失败: {e}")
                self.task_list_manager.update_task(
                    task_item.id,
                    "failed",
                    error=str(e)
                )

            # 4. 打印进度
            self.task_list_manager.print_progress()

            # 5. 延迟后继续 (如果启用自动继续)
            if self.config.auto_continue:
                print(f"⏳ 等待 {self.config.continue_delay} 秒后继续...")
                await asyncio.sleep(self.config.continue_delay)
            else:
                break
```

#### **优先级**: ⭐⭐⭐⭐⭐ **P0 - 核心基础设施**
#### **工作量**: 1-2 天
#### **依赖**: 无 (新增文件)
#### **ROI**: 极高 - 解决当前最大痛点 (持久化状态)

---

## ✨ **#2. Git 自动提交 + 增量 commit** 🔄

**来源**: autonomous-coding 的自动 commit + Grok 建议

#### **核心价值**

- ✅ **每次会话留干净状态** - 结合现有 Worktree 隔离更强大
- ✅ **自动生成描述性 message** - 包含 task ID 和 summary
- ✅ **可追溯历史** - 每个 feature 独立 commit
- ✅ **利用现有依赖** - gitpython 已在项目依赖中

#### **实现方案**

```python
# orchestration/git_manager.py
import git
from pathlib import Path
from typing import List, Optional
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

class GitAutoCommitManager:
    """Git 自动提交管理器"""

    def __init__(
        self,
        project_root: Path,
        enabled: bool = True,
        commit_message_template: str = "feat: {task_id} {description}"
    ):
        self.project_root = project_root
        self.enabled = enabled
        self.commit_message_template = commit_message_template

        try:
            self.repo = git.Repo(project_root)
        except git.InvalidGitRepositoryError:
            logger.warning(f"项目不是 Git 仓库: {project_root}")
            self.repo = None

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
        if not self.enabled or not self.repo:
            return False

        try:
            # 1. Stage 变更文件
            for file_path in changed_files:
                full_path = self.project_root / file_path
                if full_path.exists():
                    self.repo.index.add([str(full_path)])
                    logger.debug(f"Staged: {file_path}")

            # 2. 检查是否有变更
            if not self.repo.index.diff("HEAD"):
                logger.warning(f"没有需要提交的变更: {task_id}")
                return False

            # 3. 生成 commit message
            commit_message = self._generate_commit_message(
                task_id,
                description,
                summary
            )

            # 4. 提交
            commit = self.repo.index.commit(
                commit_message,
                author_date=datetime.now().isoformat()
            )

            logger.info(f"✅ Git commit: {commit.hexsha[:7]} - {task_id}")
            return True

        except Exception as e:
            logger.error(f"Git commit 失败: {e}")
            return False

    def _generate_commit_message(
        self,
        task_id: str,
        description: str,
        summary: Optional[str]
    ) -> str:
        """生成 commit message

        格式:
        feat: task-001 实现用户注册功能

        详细描述...
        """
        message = self.commit_message_template.format(
            task_id=task_id,
            description=description
        )

        if summary:
            message += f"\n\n{summary}"

        return message

    async def commit_tasks_json(self):
        """提交 tasks.json 更新"""
        if not self.enabled or not self.repo:
            return

        try:
            tasks_json_path = self.project_root / "tasks.json"
            if tasks_json_path.exists():
                self.repo.index.add([str(tasks_json_path)])
                self.repo.index.commit(
                    f"chore: 更新任务进度 ({datetime.now().strftime('%Y-%m-%d %H:%M')})"
                )
                logger.debug("✅ 已提交 tasks.json")
        except Exception as e:
            logger.error(f"提交 tasks.json 失败: {e}")

    def get_commit_history(self, limit: int = 10) -> List[dict]:
        """获取提交历史"""
        if not self.repo:
            return []

        history = []
        for commit in list(self.repo.iter_commits(max_count=limit)):
            history.append({
                "hash": commit.hexsha[:7],
                "message": commit.message.strip(),
                "author": commit.author.name,
                "date": datetime.fromtimestamp(commit.committed_date).isoformat()
            })

        return history
```

#### **集成配置**

```python
# orchestration/models.py 添加配置
@dataclass
class OrchestrationConfig:
    """编排配置"""
    # ... 现有配置 ...

    # Git 自动提交配置
    auto_commit: bool = True                      # 启用自动提交
    commit_message_template: str = "feat: {task_id} {description}"
    commit_tasks_json: bool = True                # 自动提交 tasks.json 更新
```

#### **集成到 Orchestration 层**

```python
# orchestration/orchestrator.py 添加
from .git_manager import GitAutoCommitManager

class Orchestrator(BaseOrchestrator):
    def __init__(self, project_root: Path, config: OrchestrationConfig):
        super().__init__(project_root, config)
        self.git_manager = GitAutoCommitManager(
            project_root,
            enabled=config.auto_commit
        )

    async def _execute_task_item(
        self,
        task_item: TaskItem
    ) -> Dict[str, Any]:
        """执行任务项 (集成自动 commit)"""
        # 1. 执行任务
        result = await self.executor.execute(
            task=task_item.description,
            context=task_item.__dict__
        )

        # 2. 提取变更的文件
        changed_files = result.get("files", [])

        # 3. 自动 commit
        if changed_files:
            await self.git_manager.commit_task(
                task_id=task_item.id,
                description=task_item.description,
                changed_files=changed_files,
                summary=result.get("summary")
            )

        return result
```

#### **优先级**: ⭐⭐⭐⭐⭐ **P0 - 核心基础设施**
#### **工作量**: 1 天
#### **依赖**: gitpython (已有)
#### **ROI**: 极高 - 结合 Worktree 实现完美状态管理

---

## ✨ **#3. 单任务焦点模式** 🎯

**来源**: autonomous-coding 的强制单任务 + Grok 建议

#### **核心价值**

- ✅ **防上下文爆炸** - Claude Code 长任务容易失控
- ✅ **提升稳定性** - 小批量任务更可靠
- ✅ **更细粒度进度** - 每个 task 独立验证

#### **实现方案**

```python
# orchestration/models.py 添加配置
@dataclass
class OrchestrationConfig:
    """编排配置"""
    # ... 现有配置 ...

    # 单任务焦点配置
    max_parallel_tasks: int = 1                  # 最大并行任务数 (默认 1)
    max_files_per_task: int = 5                  # 单任务最大文件数
    force_incremental: bool = True               # 强制增量模式
```

```python
# orchestration/orchestrator.py 添加检查
class Orchestrator(BaseOrchestrator):
    async def _validate_task_scope(
        self,
        result: Dict[str, Any]
    ) -> tuple[bool, str]:
        """验证任务范围

        Returns:
            (is_valid, reason)
        """
        changed_files = result.get("files", [])

        # 检查文件数量
        if len(changed_files) > self.config.max_files_per_task:
            return False, (
                f"任务范围过大: 修改了 {len(changed_files)} 个文件 "
                f"(超过限制 {self.config.max_files_per_task})"
            )

        # 检查文件大小
        total_size = 0
        for file_path in changed_files:
            full_path = self.project_root / file_path
            if full_path.exists():
                total_size += full_path.stat().st_size

        # 如果单次修改超过 100KB,建议拆分
        if total_size > 100 * 1024:
            return False, (
                f"任务范围过大: 修改了 {total_size / 1024:.1f} KB "
                f"(建议拆分为更小的任务)"
            )

        return True, "OK"

    async def _execute_task_with_validation(
        self,
        task_item: TaskItem
    ) -> Dict[str, Any]:
        """执行任务并验证范围"""
        max_retries = 3

        for attempt in range(max_retries):
            result = await self._execute_task_item(task_item)

            # 验证范围
            is_valid, reason = await self._validate_task_scope(result)

            if is_valid:
                return result
            else:
                if attempt < max_retries - 1:
                    logger.warning(f"任务范围过大,重新拆分: {reason}")

                    # 重新生成更小的任务
                    task_item = await self._split_task(task_item, reason)
                else:
                    # 超过重试次数,标记为失败
                    raise ValueError(f"任务范围过大且无法拆分: {reason}")

        return result

    async def _split_task(
        self,
        task_item: TaskItem,
        reason: str
    ) -> TaskItem:
        """拆分任务为更小的子任务"""
        logger.info(f"🔄 拆分任务: {task_item.id}")

        # 使用 Executor 智能拆分
        prompt = f"""
以下任务范围过大,需要拆分为更小的子任务:

原任务: {task_item.description}
原因: {reason}

请将此任务拆分为 2-3 个更小的、可独立执行的子任务。
每个子任务应该:
1. 可以独立完成
2. 修改不超过 5 个文件
3. 代码量不超过 50 KB

返回 JSON 格式:
{{
  "subtasks": [
    {{"description": "...", "priority": 1}},
    {{"description": "...", "priority": 2}}
  ]
}}
"""

        result = await self.executor.execute(
            task="split_task",
            context={"task": task_item.__dict__},
            prompt=prompt
        )

        # 解析结果并更新任务
        subtasks = json.loads(result).get("subtasks", [])

        # 创建新的子任务
        new_task = TaskItem(
            id=f"{task_item.id}-sub-{len(subtasks)}",
            description=subtasks[0]["description"],
            assigned_agent=task_item.assigned_agent,
            dependencies=task_item.dependencies
        )

        # 将其余子任务添加到任务列表
        for i, subtask in enumerate(subtasks[1:], 1):
            self.task_list_manager.task_list.tasks.append(
                TaskItem(
                    id=f"{task_item.id}-sub-{i}",
                    description=subtask["description"],
                    assigned_agent=task_item.assigned_agent,
                    dependencies=[new_task.id]
                )
            )

        self.task_list_manager.save()

        return new_task
```

#### **优先级**: ⭐⭐⭐⭐ **P0 - 稳定性提升**
#### **工作量**: 1 天
#### **ROI**: 高 - 大幅提升长任务稳定性

---

### **P1 - 第二周实现 (用户体验增强)**

---

## ✨ **#4. 专用初始化流程 (Initializer Mode)** 🚀

**来源**: autonomous-coding 的 Initializer Agent + Grok 建议

#### **核心价值**

- ✅ **结构化起点** - 首次运行有清晰的初始化流程
- ✅ **问答式生成** - AI 辅导式 spec 生成
- ✅ **加载历史记忆** - 结合 CONTINUITY.md 避免从零开始
- ✅ **生成项目模板** - init.sh/run_dev.sh 一键启动

#### **实现方案**

```python
# orchestration/initializer.py
from typing import Dict, Any, Optional
from pathlib import Path
import questionary
import asyncio

class InitializerAgent:
    """初始化代理 (专用模式)"""

    def __init__(
        self,
        project_root: Path,
        executor,
        task_list_manager: TaskListManager
    ):
        self.project_root = project_root
        self.executor = executor
        self.task_list_manager = task_list_manager

    async def run_interactive(self) -> Dict[str, Any]:
        """运行交互式初始化"""
        print("🚀 SuperAgent 初始化向导\n")

        # 1. 检查是否有历史记忆
        continuity_path = self.project_root / "CONTINUITY.md"
        if continuity_path.exists():
            print(f"📚 检测到项目历史: {continuity_path}")
            resume = await questionary.confirm(
                "是否基于历史记录继续?",
                default=True
            ).ask_async()

            if resume:
                return await self._resume_from_history(continuity_path)

        # 2. 交互式问答
        spec = await self._collect_spec()

        # 3. 生成任务列表
        print("\n🔨 正在生成任务列表...")
        task_list = await self._generate_task_list(spec)

        # 4. 生成项目模板
        print("\n📝 正在生成项目模板...")
        await self._generate_project_templates(spec)

        # 5. 初始化 Git
        await self._initialize_git()

        print("\n✅ 初始化完成!")
        print(f"📊 已生成 {task_list.total_tasks} 个任务")
        print(f"💾 任务列表: {self.task_list_manager.tasks_json_path}")

        return {
            "success": True,
            "spec": spec,
            "total_tasks": task_list.total_tasks
        }

    async def _collect_spec(self) -> Dict[str, Any]:
        """收集项目规范"""
        print("📋 请回答以下问题以生成项目规范:\n")

        spec = {}

        # 基本信息
        spec["project_name"] = await questionary.text(
            "项目名称?",
            instruction="例如: TodoApp, BlogSystem"
        ).ask_async()

        spec["description"] = await questionary.text(
            "项目描述?",
            instruction="简要说明项目目标和用途"
        ).ask_async()

        spec["target_users"] = await questionary.text(
            "目标用户?",
            instruction="例如: 开发者, 学生, 企业用户"
        ).ask_async()

        # 核心功能
        print("\n🎯 添加核心功能 (至少 5 个,输入空行结束):")
        features = []
        while len(features) < 5 or await questionary.confirm(
            "继续添加功能?",
            default=False
        ).ask_async():
            feature = await questionary.text("功能描述:").ask_async()
            if not feature and len(features) >= 5:
                break

            if feature:
                priority = await questionary.select(
                    "优先级:",
                    choices=["High", "Medium", "Low"]
                ).ask_async()

                features.append({
                    "description": feature,
                    "priority": priority.lower()
                })

        spec["features"] = features

        # 技术栈
        print("\n🛠️  选择技术栈:")
        spec["tech_stack"] = {
            "frontend": await questionary.select(
                "前端框架:",
                choices=["React", "Vue", "Angular", "原生 HTML/CSS/JS"]
            ).ask_async(),

            "backend": await questionary.select(
                "后端框架:",
                choices=[
                    "Python (FastAPI)",
                    "Python (Django)",
                    "Node.js (Express)",
                    "Go",
                    "无需后端"
                ]
            ).ask_async(),

            "database": await questionary.select(
                "数据库:",
                choices=[
                    "PostgreSQL",
                    "MySQL",
                    "MongoDB",
                    "SQLite",
                    "无需数据库"
                ]
            ).ask_async()
        }

        return spec

    async def _generate_task_list(
        self,
        spec: Dict[str, Any]
    ) -> TaskList:
        """生成任务列表"""
        prompt = f"""
基于以下项目规范,生成详细的任务列表:

项目名称: {spec['project_name']}
描述: {spec['description']}
核心功能: {len(spec['features'])} 个
技术栈: {spec['tech_stack']}

要求:
1. 将每个功能拆分为 3-5 个可独立执行的任务
2. 每个任务包含清晰的测试步骤
3. 按优先级排序
4. 返回 JSON 格式

核心功能:
{chr(10).join([f"{i+1}. {f['description']} (优先级: {f['priority']})" for i, f in enumerate(spec['features'])])}

返回格式:
{{
  "project_name": "{spec['project_name']}",
  "tasks": [
    {{
      "id": "task-001",
      "description": "具体任务描述",
      "test_steps": ["步骤1", "步骤2"],
      "assigned_agent": "backend-dev"
    }}
  ]
}}
"""

        result = await self.executor.execute(
            task="generate_task_list",
            context={"spec": spec},
            prompt=prompt
        )

        # 解析结果
        data = json.loads(result)

        # 创建任务列表
        tasks = [
            TaskItem(
                id=t["id"],
                description=t["description"],
                test_steps=t.get("test_steps", []),
                assigned_agent=t.get("assigned_agent", "general")
            )
            for t in data["tasks"]
        ]

        task_list = TaskList(
            project_name=spec["project_name"],
            total_tasks=len(tasks),
            tasks=tasks
        )

        # 保存
        self.task_list_manager.task_list = task_list
        self.task_list_manager.save()

        return task_list

    async def _generate_project_templates(self, spec: Dict[str, Any]):
        """生成项目模板文件"""
        templates_dir = self.project_root / ".superagent" / "templates"
        templates_dir.mkdir(parents=True, exist_ok=True)

        # 1. 生成 init.sh
        init_sh = f"""#!/bin/bash
# SuperAgent 项目初始化脚本

echo "🚀 初始化 {spec['project_name']}..."

# 安装依赖
if [ -f "package.json" ]; then
    echo "📦 安装 Node.js 依赖..."
    npm install
fi

if [ -f "requirements.txt" ]; then
    echo "📦 安装 Python 依赖..."
    pip install -r requirements.txt
fi

# 初始化数据库 (如果需要)
# ...

echo "✅ 初始化完成!"
echo "💡 运行 './start_dev.sh' 启动开发服务器"
"""
        (templates_dir / "init.sh").write_text(init_sh)

        # 2. 生成 start_dev.sh
        start_dev_sh = f"""#!/bin/bash
# {spec['project_name']} 开发服务器启动脚本

echo "🎯 启动 {spec['project_name']} 开发服务器..."

# 根据技术栈启动
if [ -f "package.json" ]; then
    npm run dev
elif [ -f "app.py" ]; then
    python app.py
elif [ -f "main.go" ]; then
    go run main.go
fi
"""
        (templates_dir / "start_dev.sh").write_text(start_dev_sh)

        # 3. 复制到项目根目录
        import shutil
        shutil.copy(templates_dir / "init.sh", self.project_root / "init.sh")
        shutil.copy(templates_dir / "start_dev.sh", self.project_root / "start_dev.sh")

        print("✅ 已生成项目模板:")
        print("   - init.sh (初始化脚本)")
        print("   - start_dev.sh (开发服务器)")

    async def _initialize_git(self):
        """初始化 Git 仓库"""
        git_dir = self.project_root / ".git"
        if not git_dir.exists():
            print("🔧 初始化 Git 仓库...")
            subprocess.run(
                ["git", "init"],
                cwd=self.project_root,
                capture_output=True
            )

            # 创建 .gitignore
            gitignore = """# SuperAgent
.superagent/
tasks.json.bak

# Python
__pycache__/
*.pyc
.pytest_cache/

# Node.js
node_modules/
.env.local
"""
            (self.project_root / ".gitignore").write_text(gitignore)

            # 初始提交
            subprocess.run(
                ["git", "add", "."],
                cwd=self.project_root,
                capture_output=True
            )
            subprocess.run(
                ["git", "commit", "-m", "chore: 初始化项目"],
                cwd=self.project_root,
                capture_output=True
            )

            print("✅ Git 仓库已初始化")
        else:
            print("ℹ️  Git 仓库已存在")

    async def _resume_from_history(
        self,
        continuity_path: Path
    ) -> Dict[str, Any]:
        """从历史记录恢复"""
        print("📚 加载项目历史...")

        content = continuity_path.read_text(encoding='utf-8')

        # 解析 CONTINUITY.md 提取关键信息
        # ... (解析逻辑)

        return {
            "success": True,
            "resumed": True,
            "continuity_path": str(continuity_path)
        }
```

#### **集成到 CLI**

```python
# cli/superagent.py 添加
from orchestration.initializer import InitializerAgent

async def cmd_init(project_root: Path):
    """初始化项目"""
    task_list_manager = TaskListManager(project_root)
    initializer = InitializerAgent(
        project_root,
        executor=executor,
        task_list_manager=task_list_manager
    )

    await initializer.run_interactive()
```

#### **优先级**: ⭐⭐⭐⭐ **P1 - 用户体验**
#### **工作量**: 2-3 天
#### **ROI**: 高 - 大幅降低使用门槛

---

## ✨ **#5. 会话继续 + 进度反馈** 🔄

**来源**: autonomous-coding 的自动继续 + Grok 建议

#### **核心价值**

- ✅ **检测未完成任务** - 启动时提示是否继续
- ✅ **简洁进度报告** - 已完成 X/Y tasks (Z%)
- ✅ **利用现有 monitoring 层** - 无需重构

#### **实现方案**

```python
# orchestration/session_manager.py
from pathlib import Path
import questionary

class SessionManager:
    """会话管理器"""

    def __init__(
        self,
        project_root: Path,
        task_list_manager: TaskListManager
    ):
        self.project_root = project_root
        self.task_list_manager = task_list_manager

    async def check_and_prompt_resume(self) -> bool:
        """检查并提示是否继续未完成任务

        Returns:
            是否继续之前的任务
        """
        # 加载任务列表
        task_list = self.task_list_manager.load_or_create()

        if not task_list:
            return False

        # 检查是否有未完成任务
        if task_list.pending == 0:
            print("✅ 所有任务已完成!")
            return False

        # 显示进度报告
        report = task_list.get_progress_report()

        print(f"""
📊 检测到未完成任务

项目: {report['project_name']}
进度: {report['completed']}/{report['total']} ({report['percentage']}%)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
✅ 已完成: {report['completed']}
⏳ 待执行: {report['pending']}
❌ 失败: {report['failed']}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
""")

        # 提示是否继续
        resume = await questionary.confirm(
            "是否继续未完成的任务?",
            default=True
        ).ask_async()

        return resume

    def print_progress_simple(self):
        """打印简洁进度"""
        task_list = self.task_list_manager.load_or_create()

        if not task_list:
            return

        report = task_list.get_progress_report()

        print(
            f"📊 进度: {report['completed']}/{report['total']} "
            f"({report['percentage']}%)"
        )
```

#### **集成到启动流程**

```python
# cli/superagent.py
async def main():
    # ... 现有代码 ...

    # 检查是否有未完成任务
    session_manager = SessionManager(project_root, task_list_manager)
    should_resume = await session_manager.check_and_prompt_resume()

    if should_resume:
        # 继续执行
        await orchestrator.execute_plan_incremental(plan=None)
    else:
        # 新项目
        await cmd_init(project_root)
```

#### **优先级**: ⭐⭐⭐⭐ **P1 - 用户体验**
#### **工作量**: 1 天
#### **ROI**: 高 - 友好的进度反馈

---

### **P2 - 第三周实现 (安全与扩展)**

---

## ✨ **#6. 命令白名单安全机制** 🔒

**来源**: autonomous-coding 的 security.py + Grok 建议

#### **核心价值**

- ✅ **防止危险命令** - rm, dd, sudo 等
- ✅ **清晰审计日志** - 所有命令执行记录
- ✅ **为未来工具执行做准备** - Web Dashboard/云同步安全基础

#### **实现方案**

```python
# core/security_checker.py
from typing import Set, List, Tuple
import logging

logger = logging.getLogger(__name__)

class SecurityChecker:
    """安全检查器 (命令白名单)"""

    # 允许的命令
    ALLOWED_COMMANDS: Set[str] = {
        # 文件检查
        "ls", "cat", "head", "tail", "wc", "grep", "find",

        # 版本控制
        "git",

        # Node.js
        "npm", "node", "npx",

        # Python
        "python", "python3", "pip", "pytest", "poetry",

        # 进程管理
        "ps", "lsof", "sleep", "pkill",

        # 文本处理
        "sed", "awk", "sort", "uniq",

        # 压缩
        "tar", "gzip", "zip", "unzip"
    }

    # 禁止的命令
    BLOCKED_COMMANDS: Set[str] = {
        # 删除命令
        "rm", "rmdir", "del", "delete",

        # 磁盘操作
        "dd", "mkfs", "format", "fdisk",

        # 权限相关
        "chmod", "chown", "sudo", "su",

        # 数据传输
        "curl", "wget", "nc", "netcat",

        # 系统关键
        "reboot", "shutdown", "halt"
    }

    # 允许的参数 (按命令)
    ALLOWED_ARGS: dict = {
        "pkill": {"-f"},  # 仅允许按名称
        "npm": {
            "install", "run", "dev", "build",
            "test", "lint", "start"
        },
        "pip": {"install", "list", "freeze", "show"},
        "git": {
            "init", "clone", "add", "commit",
            "status", "log", "diff", "branch",
            "checkout", "merge", "pull", "push"
        }
    }

    # 禁止的参数 (按命令)
    BLOCKED_ARGS: dict = {
        "pkill": {"-9", "--force"},  # 禁止强制终止
        "git": {"--force", "--hard", "--amend"}  # 危险操作
    }

    @classmethod
    def validate_command(
        cls,
        cmd: List[str]
    ) -> Tuple[bool, str]:
        """验证命令

        Returns:
            (is_allowed, reason)
        """
        if not cmd:
            return False, "空命令"

        command_name = cmd[0]

        # 检查是否在禁止列表
        if command_name in cls.BLOCKED_COMMANDS:
            return False, f"命令 '{command_name}' 被禁止"

        # 检查是否在允许列表
        if command_name not in cls.ALLOWED_COMMANDS:
            return False, f"命令 '{command_name}' 不在白名单中"

        # 检查禁止的参数
        if command_name in cls.BLOCKED_ARGS:
            for arg in cmd[1:]:
                if arg in cls.BLOCKED_ARGS[command_name]:
                    return False, (
                        f"参数 '{arg}' 对命令 '{command_name}' 被禁止"
                    )

        # 检查允许的参数 (宽松模式)
        if command_name in cls.ALLOWED_ARGS:
            for arg in cmd[1:]:
                if arg.startswith("-") and arg not in cls.ALLOWED_ARGS[command_name]:
                    # 允许未知参数 (宽松模式)
                    logger.warning(f"未知参数: {arg}")

        # 记录命令执行
        logger.info(f"✅ 命令允许: {' '.join(cmd)}")

        return True, "OK"

    @classmethod
    def validate_path(
        cls,
        path: str,
        base_dir: Path
    ) -> Tuple[bool, str]:
        """验证路径安全性

        防止路径穿越攻击
        """
        try:
            # 解析路径
            full_path = (base_dir / path).resolve()

            # 检查是否在基础目录下
            base_dir_resolved = base_dir.resolve()

            try:
                full_path.relative_to(base_dir_resolved)
                return True, "OK"
            except ValueError:
                return False, f"路径穿越攻击: {path}"

        except Exception as e:
            return False, f"路径验证失败: {e}"
```

#### **集成到执行层**

```python
# execution/bash_executor.py 添加
from core.security_checker import SecurityChecker

class BashExecutor:
    async def execute_safe(self, cmd: List[str], cwd: Path):
        """安全执行 Bash 命令"""

        # 1. 验证命令
        allowed, reason = SecurityChecker.validate_command(cmd)
        if not allowed:
            raise SecurityError(f"命令被安全检查器阻止: {reason}")

        # 2. 验证路径
        if cwd:
            allowed, reason = SecurityChecker.validate_path(str(cwd), cwd)
            if not allowed:
                raise SecurityError(f"路径验证失败: {reason}")

        # 3. 执行命令
        return await self.execute(cmd, cwd=cwd)
```

#### **优先级**: ⭐⭐⭐⭐ **P2 - 安全增强**
#### **工作量**: 1 天
#### **ROI**: 高 - 立即提升安全性

---

## 📊 总结与优先级

### **实施路线图 (3 周)**

#### **第一周: P0 核心基础设施 (4-5 天)**

```
Day 1-2: tasks.json 实现
         └─ TaskListManager + 集成到 Orchestration

Day 3:   Git 自动提交
         └─ GitAutoCommitManager

Day 4:   单任务焦点模式
         └─ 任务范围验证 + 自动拆分

Day 5:   集成测试
```

#### **第二周: P1 用户体验增强 (5 天)**

```
Day 1-3: 初始化流程
         └─ InitializerAgent + 交互式 spec 生成

Day 4:   会话继续
         └─ SessionManager + 进度提示

Day 5:   CLI 集成 + 测试
```

#### **第三周: P2 安全与扩展 (5 天)**

```
Day 1:   命令白名单
         └─ SecurityChecker + 集成

Day 2-3: 自动继续机制
         └─ AutoContinueExecutor

Day 4:   /create-spec 命令 (可选)
         └─ 交互式规范生成

Day 5:   全面测试 + 文档
```

---

### **投资回报分析**

| # | 特性 | 工作量 | 优先级 | ROI | 依赖 |
|---|------|--------|--------|-----|------|
| **1** | tasks.json | 1-2 天 | P0 | ⭐⭐⭐⭐⭐ | 无 |
| **2** | Git 自动提交 | 1 天 | P0 | ⭐⭐⭐⭐⭐ | gitpython |
| **3** | 单任务焦点 | 1 天 | P0 | ⭐⭐⭐⭐ | tasks.json |
| **4** | 初始化流程 | 2-3 天 | P1 | ⭐⭐⭐⭐ | tasks.json |
| **5** | 会话继续 | 1 天 | P1 | ⭐⭐⭐⭐ | tasks.json |
| **6** | 命令白名单 | 1 天 | P2 | ⭐⭐⭐⭐ | 无 |
| **7** | 自动继续 | 1-2 天 | P2 | ⭐⭐⭐ | tasks.json |

---

### **核心洞察**

**融合后的方案**:

1. ✅ **保留 SuperAgent 现有架构** - 三层抽象、多域支持、Worktree 隔离
2. ✅ **采纳 autonomous-coding 核心机制** - tasks.json、双代理、自动 commit
3. ✅ **利用现有依赖和层** - gitpython、conversation、monitoring
4. ✅ **低成本高回报** - 优先 1-2 天实现的特性

**第一周就能实现 3 个 P0 特性!**

---

**文档版本**: v2.0 (融合版)
**最后更新**: 2026-01-11
**作者**: Claude (原分析) + Grok (建议) + 融合
