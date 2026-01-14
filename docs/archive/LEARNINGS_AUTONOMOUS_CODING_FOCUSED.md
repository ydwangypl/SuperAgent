# autonomous-coding 独特价值分析

**分析日期**: 2026-01-11
**SuperAgent 版本**: v3.1
**参考项目**: [autonomous-coding by leonvanzyl](https://github.com/leonvanzyl/autonomous-coding)

---

## 🎯 核心问题

**SuperAgent 从 autonomous-coding 可以借鉴什么独特特性？**

---

## 📊 autonomous-coding 的核心竞争力

### **1. 双代理模式 (Two-Agent Pattern)** 🎭

#### **核心设计**

```
┌─────────────────────────────────────────────────────────┐
│ Initializer Agent (First Session)                       │
│                                                         │
│  输入: 应用规范 (app_spec.txt)                          │
│  ├─ 1. 分析应用规范                                      │
│  ├─ 2. 生成 feature_list.json (50-200个测试用例)         │
│  ├─ 3. 设置项目结构                                      │
│  ├─ 4. 初始化 Git 仓库                                   │
│  └─ 5. 保存 prompts/ 目录                               │
│                                                         │
│  输出: feature_list.json (源文件)                        │
└─────────────────────────────────────────────────────────┘
                        ↓
┌─────────────────────────────────────────────────────────┐
│ Coding Agent (Subsequent Sessions)                      │
│                                                         │
│  输入: feature_list.json                                │
│  循环:                                                  │
│  ├─ 1. 读取下一个待实现功能                              │
│  ├─ 2. 实现该功能                                        │
│  ├─ 3. 标记状态 (passing/failing)                       │
│  ├─ 4. 保存进度到 feature_list.json                      │
│  ├─ 5. 显示进度报告                                      │
│  └─ 6. 等待 3 秒 → 自动继续                              │
│                                                         │
│  直到: 所有功能实现完成                                   │
└─────────────────────────────────────────────────────────┘
```

#### **为什么有效？**

1. **职责清晰**
   - Initializer: 规划和设置
   - Coding: 实现和验证

2. **状态持久化**
   - `feature_list.json` 是单一事实来源
   - 每个功能都有明确状态
   - 随时可以恢复

3. **增量开发**
   - 一次实现一个功能
   - 进度可见
   - 失败可追溯

#### **SuperAgent 可以如何借鉴？**

```python
# 当前 SuperAgent: 单次执行所有任务
plan = orchestrator.create_plan(spec)
await orchestrator.execute_plan(plan)  # 全部执行完

# 借鉴后: 分阶段执行
# 阶段1: 初始化
feature_list = await initializer_agent.run(app_spec)

# 阶段2: 编码 (可多次执行)
while not feature_list.is_complete():
    await coding_agent.run_next_feature(feature_list)
    feature_list.save()  # 持久化进度
```

**价值**: ✅ 支持长时间任务 (数小时到数天)

---

### **2. feature_list.json 源文件模式** 📋

#### **文件结构**

```json
{
  "project_name": "TodoApp",
  "total_features": 50,
  "passing": 15,
  "failing": 0,
  "pending": 35,
  "features": [
    {
      "id": "feature-001",
      "description": "用户可以添加新的待办事项",
      "status": "passing",
      "assigned_to": null,
      "started_at": "2025-01-15T10:30:00",
      "completed_at": "2025-01-15T10:45:00",
      "error": null
    },
    {
      "id": "feature-002",
      "description": "用户可以标记待办事项为完成",
      "status": "pending",
      "assigned_to": null,
      "started_at": null,
      "completed_at": null,
      "error": null
    }
  ]
}
```

#### **核心价值**

1. **单一事实来源**
   - 所有进度信息集中在一个文件
   - 人类可读 (JSON)
   - 易于版本控制

2. **可恢复性**
   - 中断后读取文件恢复
   - 无需重新规划
   - 断点续传

3. **进度可见**
   ```bash
   cat feature_list.json | grep '"status"'
   # "status": "passing"  ← 已完成
   # "status": "pending"  ← 待执行
   ```

#### **SuperAgent 可以如何借鉴？**

**当前问题**:
- SuperAgent 的进度主要在内存中
- 中断后难以恢复
- 缺少可视化的进度跟踪

**借鉴方案**:

```python
# orchestration/feature_list.py
from dataclasses import dataclass
from typing import List
import json
from pathlib import Path

@dataclass
class Feature:
    id: str
    description: str
    status: str = "pending"  # pending | running | passing | failing
    started_at: str = None
    completed_at: str = None
    error: str = None

@dataclass
class FeatureList:
    project_name: str
    total_features: int
    passing: int = 0
    failing: int = 0
    pending: int = 0
    features: List[Feature] = None

    def save(self, path: Path):
        """保存到文件"""
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(asdict(self), f, indent=2, ensure_ascii=False)

    @classmethod
    def load(cls, path: Path) -> 'FeatureList':
        """从文件加载"""
        with open(path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        return cls(**data)

    def get_next_pending(self) -> Feature:
        """获取下一个待实现功能"""
        for feature in self.features:
            if feature.status == "pending":
                return feature
        return None

# 集成到 Orchestrator
class Orchestrator:
    def __init__(self, project_root: Path):
        self.feature_list_path = project_root / "feature_list.json"
        self.feature_list = None

    def create_feature_list(self, plan: Plan) -> FeatureList:
        """从计划创建功能列表"""
        features = [
            Feature(
                id=f"feature-{i:03d}",
                description=task.description
            )
            for i, task in enumerate(plan.tasks, 1)
        ]

        self.feature_list = FeatureList(
            project_name=plan.project_name,
            total_features=len(features),
            features=features
        )

        self.feature_list.save(self.feature_list_path)
        return self.feature_list

    def resume_from_feature_list(self) -> FeatureList:
        """从文件恢复"""
        self.feature_list = FeatureList.load(self.feature_list_path)
        return self.feature_list

    async def execute_next_feature(self):
        """执行下一个功能"""
        if not self.feature_list:
            self.resume_from_feature_list()

        feature = self.feature_list.get_next_pending()
        if not feature:
            print("✅ 所有功能已完成!")
            return

        # 实现功能
        feature.status = "running"
        feature.started_at = datetime.now().isoformat()

        try:
            await self._implement_feature(feature)
            feature.status = "passing"
            self.feature_list.passing += 1
        except Exception as e:
            feature.status = "failing"
            feature.error = str(e)
            self.feature_list.failing += 1

        feature.completed_at = datetime.now().isoformat()
        self.feature_list.pending -= 1

        # 保存进度
        self.feature_list.save(self.feature_list_path)

        # 显示进度
        self._print_progress()
```

**价值**: ✅ 可视化进度 + 断点续传

---

### **3. 自动会话继续 (Auto-Continue)** 🔄

#### **核心机制**

```python
# autonomous-coding 的继续逻辑
while True:
    # 1. 实现下一个功能
    next_feature = feature_list.get_next_pending()
    if not next_feature:
        break  # 完成

    # 2. 执行功能
    await implement_feature(next_feature)

    # 3. 更新进度
    feature_list.mark_progress(next_feature.id, "passing")
    feature_list.save()

    # 4. 显示进度
    print_progress(feature_list)

    # 5. 等待 3 秒后继续
    print("⏳ 等待 3 秒后继续...")
    await asyncio.sleep(3)

    # 6. 自动进入下一次循环
```

#### **为什么是 3 秒？**

1. **给用户时间观察**
   - 看到进度输出
   - 理解当前状态
   - 必要时按 Ctrl+C 中断

2. **避免 API 速率限制**
   - Claude API 有速率限制
   - 3 秒延迟降低风险

3. **保持节奏**
   - 不会太快失控
   - 不会太慢影响效率

#### **SuperAgent 可以如何借鉴？**

**当前问题**:
- SuperAgent 执行完所有任务才停止
- 无法中途暂停恢复
- 缺少进度反馈

**借鉴方案**:

```python
# orchestration/auto_continue.py
import asyncio
from typing import Callable, Optional

class AutoContinueExecutor:
    """自动继续执行器"""

    def __init__(
        self,
        delay_seconds: int = 3,
        on_progress: Optional[Callable] = None
    ):
        self.delay_seconds = delay_seconds
        self.on_progress = on_progress
        self._should_stop = False

    async def execute_with_continue(
        self,
        get_next_task: Callable,
        execute_task: Callable
    ):
        """执行任务并自动继续

        Args:
            get_next_task: 获取下一个任务的函数
            execute_task: 执行任务的函数
        """
        iteration = 0

        while not self._should_stop:
            iteration += 1

            # 1. 获取下一个任务
            task = get_next_task()
            if not task:
                print("✅ 所有任务已完成!")
                break

            # 2. 执行任务
            print(f"📍 执行任务 #{iteration}: {task.description}")
            success = await execute_task(task)

            # 3. 进度回调
            if self.on_progress:
                await self.on_progress(task, success)

            # 4. 显示进度
            self._print_progress()

            # 5. 延迟后继续
            if not self._should_stop:
                print(f"⏳ 等待 {self.delay_seconds} 秒后继续...")
                await asyncio.sleep(self.delay_seconds)

        print(f"🏁 执行完成! 总计: {iteration} 个任务")

    def stop(self):
        """停止自动继续"""
        self._should_stop = True
        print("⏹️  已请求停止...")

    def _print_progress(self):
        # 进度显示逻辑
        pass

# 使用示例
executor = AutoContinueExecutor(delay_seconds=3)

try:
    await executor.execute_with_continue(
        get_next_task=lambda: feature_list.get_next_pending(),
        execute_task=lambda task: orchestrator.implement_feature(task)
    )
except KeyboardInterrupt:
    executor.stop()
    print("⏸️  已暂停,运行相同命令可恢复")
```

**价值**: ✅ 长时间任务 + 随时可中断

---

### **4. /create-spec 交互式规范生成** 📝

#### **核心价值**

**问题**: 用户不知道如何写一个好的应用规范

**解决**: AI 辅助交互式生成

```markdown
# /create-spec 命令流程

## 1. 项目概述
Claude: "你想构建什么类型的应用?"
User:  "一个待办事项应用"

Claude: "主要解决什么问题?"
User:  "帮助用户管理日常任务"

Claude: "目标用户是谁?"
User:  "学生和上班族"

## 2. 核心功能
Claude: "列出 5-10 个核心功能"
User:  "1. 添加待办事项
       2. 标记完成
       3. 删除事项
       4. 分类管理
       5. 提醒功能"

## 3. 技术栈
Claude: "偏好什么技术栈?"
User:  "React + Node.js + MongoDB"

## 4. 生成规范
✅ prompts/app_spec.txt
✅ prompts/spec.json
```

#### **生成的规范文件**

```
prompts/
├── app_spec.txt              # 人类可读
└── spec.json                 # 机器可读
```

**app_spec.txt**:
```markdown
# 项目规范: TodoApp

## 项目概述
一个帮助用户管理日常任务的待办事项应用

## 核心功能
1. 添加待办事项
2. 标记完成状态
3. 删除事项
4. 分类管理
5. 提醒功能

## 技术栈
- 前端: React
- 后端: Node.js
- 数据库: MongoDB
```

**spec.json**:
```json
{
  "project_name": "TodoApp",
  "description": "帮助用户管理日常任务",
  "features": [
    {"id": "feature-001", "description": "添加待办事项", "priority": "high"},
    {"id": "feature-002", "description": "标记完成状态", "priority": "high"}
  ],
  "tech_stack": {
    "frontend": "React",
    "backend": "Node.js",
    "database": "MongoDB"
  }
}
```

#### **SuperAgent 可以如何借鉴？**

**当前问题**:
- SuperAgent 需要用户手动编写规范
- 没有引导流程
- 规范质量不一致

**借鉴方案**:

```python
# cli/commands/create_spec.py
import questionary
from pathlib import Path

async def cmd_create_spec(project_root: Path):
    """交互式创建项目规范"""

    print("📝 让我们一起创建项目规范...\n")

    # 1. 基本信息
    project_name = await questionary.text("项目名称?").ask_async()
    description = await questionary.text("项目描述?").ask_async()
    target_users = await questionary.text("目标用户?").ask_async()

    # 2. 核心功能
    print("\n🎯 添加核心功能 (至少 5 个)...")
    features = []
    while len(features) < 5 or await questionary.confirm("继续添加?").ask_async():
        feature = await questionary.text("功能描述:").ask_async()
        priority = await questionary.select(
            "优先级:",
            choices=["High", "Medium", "Low"]
        ).ask_async()

        features.append({
            "description": feature,
            "priority": priority.lower()
        })

    # 3. 技术栈
    print("\n🛠️  选择技术栈...")
    frontend = await questionary.select(
        "前端框架:",
        choices=["React", "Vue", "Angular", "原生 HTML/CSS/JS"]
    ).ask_async()

    backend = await questionary.select(
        "后端框架:",
        choices=["Python (FastAPI)", "Python (Django)", "Node.js", "Go", "无需后端"]
    ).ask_async()

    database = await questionary.select(
        "数据库:",
        choices=["PostgreSQL", "MySQL", "MongoDB", "SQLite", "无需数据库"]
    ).ask_async()

    # 4. 生成规范
    spec = {
        "project_name": project_name,
        "description": description,
        "target_users": target_users,
        "features": [
            {"id": f"feature-{i:03d}", **f}
            for i, f in enumerate(features, 1)
        ],
        "tech_stack": {
            "frontend": frontend,
            "backend": backend,
            "database": database
        }
    }

    # 5. 保存
    prompts_dir = project_root / "prompts"
    prompts_dir.mkdir(parents=True, exist_ok=True)

    # 保存 JSON
    import json
    with open(prompts_dir / "spec.json", 'w', encoding='utf-8') as f:
        json.dump(spec, f, indent=2, ensure_ascii=False)

    # 保存 Markdown
    spec_md = f"""# 项目规范: {project_name}

## 描述
{description}

## 目标用户
{target_users}

## 核心功能
{chr(10).join([f"{i+1}. **{f['description']}** (优先级: {f['priority']})" for i, f in enumerate(features)])}

## 技术栈
- 前端: {frontend}
- 后端: {backend}
- 数据库: {database}
"""

    with open(prompts_dir / "app_spec.txt", 'w', encoding='utf-8') as f:
        f.write(spec_md)

    print(f"\n✅ 规范已保存到: {prompts_dir}")
    print("   - spec.json")
    print("   - app_spec.txt")

    return spec
```

**价值**: ✅ 降低使用门槛 + 规范质量一致

---

### **5. 命令白名单机制** 🔒

#### **核心实现**

```python
# security.py
ALLOWED_COMMANDS = {
    # 文件检查
    "ls", "cat", "head", "tail", "wc", "grep",

    # 版本控制
    "git",

    # Node.js
    "npm", "node",

    # Python
    "python", "pip",

    # 进程管理
    "ps", "lsof", "sleep", "pkill"
}

def validate_command(cmd: list) -> tuple[bool, str]:
    """验证命令是否在白名单"""
    if not cmd:
        return False, "Empty command"

    command_name = cmd[0]

    if command_name not in ALLOWED_COMMANDS:
        return False, f"Command '{command_name}' not allowed"

    return True, "OK"
```

#### **核心价值**

1. **简单有效**
   - 白名单清晰
   - 易于维护
   - 无需复杂逻辑

2. **防止意外**
   - 阻止危险命令 (rm, dd, sudo)
   - 限制可执行范围
   - 审计日志清晰

3. **性能开销低**
   - O(1) 查找
   - 无额外依赖
   - 启动快速

#### **SuperAgent 可以如何借鉴？**

**当前问题**:
- SuperAgent 没有命令限制
- 任何 Bash 命令都可执行
- 存在安全风险

**借鉴方案**:

```python
# common/security.py 添加
from typing import Set, List, Tuple

class CommandWhitelist:
    """命令白名单"""

    ALLOWED: Set[str] = {
        # 文件检查
        "ls", "cat", "head", "tail", "wc", "grep", "find",

        # 版本控制
        "git",

        # Node.js
        "npm", "node", "npx",

        # Python
        "python", "python3", "pip", "pytest",

        # 进程管理
        "ps", "lsof", "sleep", "pkill"
    }

    BLOCKED: Set[str] = {
        # 危险命令
        "rm", "rmdir", "del", "delete",
        "mkfs", "format", "dd",
        "chmod", "chown",
        "sudo", "su",
        "curl", "wget"  # 防止数据泄露
    }

    @classmethod
    def validate(cls, cmd: List[str]) -> Tuple[bool, str]:
        """验证命令"""
        if not cmd:
            return False, "Empty command"

        command_name = cmd[0]

        if command_name in cls.BLOCKED:
            return False, f"Command '{command_name}' is blocked"

        if command_name not in cls.ALLOWED:
            return False, f"Command '{command_name}' not in whitelist"

        return True, "OK"

# 集成到执行层
async def execute_bash_safe(cmd: List[str]):
    """安全执行 Bash 命令"""
    allowed, reason = CommandWhitelist.validate(cmd)

    if not allowed:
        raise SecurityError(f"Command blocked: {reason}")

    # 执行命令
    return await execute_bash(cmd)
```

**价值**: ✅ 立即提升安全性

---

## 📊 总结: 5 大独特借鉴点

| # | 特性 | 价值 | 工作量 | 优先级 |
|---|------|------|--------|--------|
| **1** | **双代理模式** | 支持长时间任务 | 3-4 天 | ⭐⭐⭐⭐⭐ |
| **2** | **feature_list.json** | 可视化进度 + 断点续传 | 2 天 | ⭐⭐⭐⭐⭐ |
| **3** | **自动会话继续** | 长时间任务 + 随时可中断 | 1-2 天 | ⭐⭐⭐⭐⭐ |
| **4** | **/create-spec** | 降低使用门槛 | 2 天 | ⭐⭐⭐⭐ |
| **5** | **命令白名单** | 立即提升安全性 | 1 天 | ⭐⭐⭐⭐⭐ |

---

## 🗓️ 实施建议

### **第一周: P0 特性**

```
Day 1:   命令白名单 (1 天)
Day 2-3: feature_list.json (2 天)
Day 4-5: 自动会话继续 (2 天)
```

### **第二周: P1 特性**

```
Day 1-4: 双代理模式 (4 天)
Day 5:   /create-spec 命令 (1 天，预留缓冲)
```

---

## 🎯 核心洞察

**autonomous-coding 的独特价值在于:**

1. **极简设计哲学**
   - 用最少的代码实现核心功能
   - 每个特性都有明确价值
   - 易于理解和维护

2. **长时间任务专家**
   - feature_list.json 源文件
   - 自动会话继续
   - 随时可中断恢复

3. **低门槛设计**
   - /create-spec 交互式引导
   - 清晰的进度显示
   - 简单的命令行界面

4. **安全性优先**
   - 命令白名单
   - 简单有效
   - 性能开销低

**这正是 SuperAgent 可以直接借鉴的!**

---

**文档版本**: v1.0
**最后更新**: 2026-01-11
