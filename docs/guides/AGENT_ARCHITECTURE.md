# SuperAgent Agent 架构说明

> **版本**: v3.2+
> **更新日期**: 2026-01-14
> **目标读者**: 希望深入理解 SuperAgent 架构的开发者

---

## 📋 目录

1. [系统架构概览](#系统架构概览)
2. [Agent 核心架构](#agent-核心架构)
3. [数据模型](#数据模型)
4. [执行流程](#执行流程)
5. [Agent 生命周期](#agent-生命周期)
6. [Agent 注册机制](#agent-注册机制)
7. [Agent 工厂模式](#agent-工厂模式)
8. [Agent 调度器](#agent-调度器)
9. [Agent 协作机制](#agent-协作机制)
10. [架构设计原则](#架构设计原则)

---

## 🏗️ 系统架构概览

### 整体架构图

```
┌─────────────────────────────────────────────────────────┐
│                      SuperAgent 系统                      │
├─────────────────────────────────────────────────────────┤
│                                                           │
│  ┌─────────────┐      ┌──────────────┐                  │
│  │   Planner   │─────▶│  Dispatcher  │                  │
│  │  (规划器)    │      │  (调度器)     │                  │
│  └─────────────┘      └──────┬───────┘                  │
│                              │                           │
│                              ▼                           │
│                      ┌──────────────┐                    │
│                      │ AgentFactory │                    │
│                      │  (Agent工厂)  │                    │
│                      └──────┬───────┘                    │
│                              │                           │
│                              ▼                           │
│                      ┌──────────────┐                    │
│                      │AgentRegistry │                    │
│                      │ (注册中心)    │                    │
│                      └──────┬───────┘                    │
│                              │                           │
│         ┌────────────────────┼────────────────────┐      │
│         │                    │                    │      │
│         ▼                    ▼                    ▼      │
│  ┌──────────┐         ┌──────────┐        ┌──────────┐  │
│  │CodingAgent│        │TestAgent │        │ DocAgent │  │
│  │(代码生成)  │        │(测试生成)  │        │(文档生成)  │  │
│  └──────────┘         └──────────┘        └──────────┘  │
│         │                    │                    │      │
│         └────────────────────┼────────────────────┘      │
│                              │                           │
│                              ▼                           │
│                      ┌──────────────┐                    │
│                      │  BaseAgent   │                    │
│                      │  (Agent基类)  │                    │
│                      └──────────────┘                    │
└─────────────────────────────────────────────────────────┘
```

### 核心组件

1. **Planner (规划器)**: 负责任务分解和执行计划生成
2. **Dispatcher (调度器)**: 负责 Agent 分配和资源管理
3. **AgentFactory (工厂)**: 负责 Agent 实例化
4. **AgentRegistry (注册中心)**: 管理 Agent 元数据和映射
5. **BaseAgent (基类)**: 所有 Agent 的抽象基类
6. **具体 Agent**: CodingAgent, TestingAgent, DocumentationAgent 等

---

## 🎯 Agent 核心架构

### BaseAgent 类层次

```
BaseAgent (抽象基类)
    │
    ├─── 属性
    │    ├─── agent_id: str
    │    ├─── config: AgentConfig
    │    ├─── status: AgentStatus
    │    ├─── thoughts: List[AgentThought]
    │    ├─── steps: List[Dict[str, Any]]
    │    ├─── _current_logs: List[str]
    │    └─── _current_metrics: Dict[str, Any]
    │
    ├─── 抽象方法 (必须实现)
    │    ├─── name: property → str
    │    ├─── get_capabilities() → Set[AgentCapability]
    │    └─── execute_impl() → List[Artifact]
    │
    ├─── 核心方法
    │    ├─── execute() → AgentResult
    │    ├─── run() → AgentResult
    │    ├─── plan() → List[Dict[str, Any]]
    │    └─── validate_input() → bool
    │
    └─── 辅助方法
         ├─── add_thought()
         ├─── add_step()
         ├─── add_log()
         └─── set_metric()
```

### Agent 能力体系

```
AgentCapability (枚举)
    │
    ├─── CODE_GENERATION (代码生成)
    ├─── TESTING (测试)
    ├─── DOCUMENTATION (文档)
    ├─── REFACTORING (重构)
    ├─── ARCHITECTURE (架构)
    ├─── DEBUGGING (调试)
    └─── OPTIMIZATION (优化)
```

### Agent 类型体系

```
AgentType (枚举)
    │
    ├─── 核心管理与设计
    │    ├─── PRODUCT_MANAGEMENT (产品管理)
    │    ├─── DATABASE_DESIGN (数据库设计)
    │    └─── API_DESIGN (API设计)
    │
    ├─── 核心开发
    │    ├─── BACKEND_DEV (后端开发)
    │    ├─── FRONTEND_DEV (前端开发)
    │    ├─── FULL_STACK_DEV (全栈开发)
    │    └─── MINI_PROGRAM_DEV (小程序开发)
    │
    ├─── 质量与安全
    │    ├─── QA_ENGINEERING (QA工程)
    │    ├─── SECURITY_AUDIT (安全审计)
    │    └─── CODE_REVIEW (代码审查)
    │
    ├─── 运维与优化
    │    ├─── DEVOPS_ENGINEERING (DevOps工程)
    │    ├─── PERFORMANCE_OPTIMIZATION (性能优化)
    │    └─── INFRA_SETUP (基础设施)
    │
    └─── 专项处理
         ├─── TECHNICAL_WRITING (技术写作)
         ├─── CODE_REFACTORING (代码重构)
         ├─── DATA_MIGRATION (数据迁移)
         └─── UI_DESIGN (UI设计)
```

---

## 📦 数据模型

### 1. AgentContext (上下文)

```python
@dataclass
class AgentContext:
    """Agent 执行上下文"""
    task_id: str                    # 任务唯一标识
    step_id: str                    # 步骤标识
    project_root: str               # 项目根目录
    worktree_path: Optional[str]    # Git worktree 路径
    metadata: Dict[str, Any]        # 额外元数据
```

**用途**: 传递执行环境信息给 Agent

**示例**:
```python
context = AgentContext(
    task_id="task-123",
    step_id="step-1",
    project_root="/path/to/project",
    worktree_path="/path/to/worktree",
    metadata={"priority": "high", "deadline": "2026-01-15"}
)
```

### 2. AgentConfig (配置)

```python
@dataclass
class AgentConfig:
    """Agent 配置"""
    max_retries: int = 3            # 最大重试次数
    retry_delay: float = 1.0        # 重试延迟(秒)
    timeout: int = 300              # 超时时间(秒)
    save_intermediate: bool = True  # 是否保存中间结果
    enable_metrics: bool = True     # 是否启用指标收集
```

**用途**: 控制 Agent 行为

**示例**:
```python
config = AgentConfig(
    max_retries=5,
    retry_delay=2.0,
    timeout=600,
    save_intermediate=True,
    enable_metrics=True
)
```

### 3. AgentStatus (状态)

```python
class AgentStatus(str, Enum):
    """Agent 状态枚举"""
    IDLE = "idle"                   # 空闲
    WORKING = "working"             # 工作中
    COMPLETED = "completed"         # 已完成
    FAILED = "failed"               # 失败
    CANCELLED = "cancelled"         # 已取消
```

**状态转换图**:
```
IDLE ──▶ WORKING ──▶ COMPLETED
  │          │
  │          └───▶ FAILED
  │
  └───▶ CANCELLED
```

### 4. AgentResult (结果)

```python
@dataclass
class AgentResult:
    """Agent 执行结果"""
    agent_id: str                   # Agent ID
    task_id: str                    # 任务 ID
    step_id: str                    # 步骤 ID
    status: AgentStatus             # 执行状态
    success: bool                   # 是否成功
    artifacts: List[Artifact]       # 产出物列表
    logs: List[str]                 # 日志列表
    steps: List[Dict[str, Any]]     # 执行步骤
    metrics: Dict[str, Any]         # 指标数据
    error: Optional[str]            # 错误信息
    message: Optional[str]          # 结果消息
    started_at: Optional[datetime]  # 开始时间
    completed_at: Optional[datetime] # 完成时间
    duration_seconds: Optional[float] # 执行时长
```

**用途**: 封装 Agent 执行的完整结果

**示例**:
```python
result = AgentResult(
    agent_id="coding-agent-1",
    task_id="task-123",
    step_id="step-1",
    status=AgentStatus.COMPLETED,
    success=True,
    artifacts=[artifact1, artifact2],
    logs=["开始执行", "生成代码", "任务完成"],
    steps=[step1, step2, step3],
    metrics={"code_lines": 1250, "files": 5},
    error=None,
    message="任务执行成功",
    started_at=datetime(2026, 1, 14, 10, 0, 0),
    completed_at=datetime(2026, 1, 14, 10, 0, 5),
    duration_seconds=5.0
)
```

### 5. Artifact (工件)

```python
@dataclass
class Artifact:
    """Agent 产出物"""
    type: str                       # 工件类型
    path: str                       # 文件路径
    content: str                    # 文件内容
    metadata: Dict[str, Any]        # 元数据
    created_at: datetime = field(default_factory=datetime.now)
```

**工件类型**:
- `code`: 代码文件
- `documentation`: 文档文件
- `config`: 配置文件
- `test`: 测试文件
- `script`: 脚本文件
- `data`: 数据文件

**示例**:
```python
artifact = Artifact(
    type="code",
    path="src/api/users.py",
    content="def get_users():\n    return []",
    metadata={
        "language": "Python",
        "framework": "FastAPI",
        "lines": 10
    },
    created_at=datetime.now()
)
```

### 6. AgentThought (思考)

```python
@dataclass
class AgentThought:
    """Agent 思考过程"""
    step: int                       # 步骤编号
    thought: str                    # 思考内容
    action: Optional[str] = None    # 采取的行动
    result: Optional[str] = None    # 行动结果
    timestamp: datetime = field(default_factory=datetime.now)
```

**用途**: 记录 Agent 的思考过程,便于调试和审查

**示例**:
```python
thought = AgentThought(
    step=1,
    thought="分析用户需求",
    action="提取功能点和技术栈",
    result="发现 3 个核心功能: 用户管理、权限控制、数据导出"
)
```

### 7. AgentMetadata (元数据)

```python
@dataclass
class AgentMetadata:
    """Agent 元数据定义"""
    agent_type: AgentType           # Agent 类型
    impl_class: Type[BaseAgent]     # 实现类
    description: str                # 描述
    priority: int = 99              # 优先级 (1-99)
    max_concurrent: int = 5         # 最大并发数
    capabilities: List[str] = field(default_factory=list) # 能力列表
    keywords: List[str] = field(default_factory=list)     # 关键词
```

**用途**: 在 AgentRegistry 中注册 Agent 的元信息

**示例**:
```python
metadata = AgentMetadata(
    agent_type=AgentType.BACKEND_DEV,
    impl_class=CodingAgent,
    description="负责服务端业务逻辑、数据处理和系统集成",
    priority=3,
    max_concurrent=10,
    capabilities=["code_generation", "architecture"],
    keywords=[r"后端|backend|服务端|server"]
)
```

---

## 🔄 执行流程

### 1. 标准执行流程

```
┌──────────────────────────────────────────────────────┐
│                   Agent 执行流程                       │
└──────────────────────────────────────────────────────┘

1. 初始化阶段
   │
   ├─▶ 创建 Agent 实例
   │   agent = MyCustomAgent(agent_id="xxx")
   │
   └─▶ 配置 Agent 参数
       config = AgentConfig(max_retries=3)

2. 准备阶段
   │
   ├─▶ 创建上下文
   │   context = AgentContext(...)
   │
   └─▶ 准备输入
       task_input = {"description": "...", "tech_stack": [...]}

3. 执行阶段 (run() 方法)
   │
   ├─▶ 输入验证
   │   validate_input(task_input)
   │
   ├─▶ 重试循环 (max_retries 次)
   │   │
   │   ├─▶ 执行任务 (execute() 方法)
   │   │   │
   │   │   ├─▶ 规划步骤 (plan() 方法)
   │   │   │   steps = await plan(context, task_input)
   │   │   │
   │   │   ├─▶ 执行实现 (execute_impl() 方法)
   │   │   │   artifacts = await execute_impl(context, task_input)
   │   │   │
   │   │   └─▶ 构建结果
   │   │       result.artifacts = artifacts
   │   │       result.logs = self._current_logs
   │   │       result.metrics = self._current_metrics
   │   │
   │   └─▶ 检查结果
   │       if result.success: break
   │       else: 重试
   │
   └─▶ 保存中间结果 (可选)
       if config.save_intermediate:
           await _save_intermediate_result(context, result)

4. 完成阶段
   │
   ├─▶ 返回结果
   │   return result
   │
   └─▶ 更新状态
       agent.status = AgentStatus.COMPLETED
```

### 2. execute_impl() 内部流程

```
┌──────────────────────────────────────────────────────┐
│           execute_impl() 内部流程                      │
└──────────────────────────────────────────────────────┘

1. 解析输入
   │
   ├─▶ 提取参数
   │   description = task_input.get("description")
   │   tech_stack = task_input.get("tech_stack", [])
   │
   └─▶ 验证参数
       assert description, "description 不能为空"

2. 添加思考过程 (可选)
   │
   ├─▶ 记录分析思考
   │   self.add_thought(
   │       step=1,
   │       thought="分析用户需求",
   │       action="提取功能点和技术栈"
   │   )
   │
   └─▶ 记录设计思考
       self.add_thought(
           step=2,
           thought="设计系统架构",
           action="选择架构模式"
       )

3. 执行业务逻辑
   │
   ├─▶ 子任务 1
   │   result1 = await self._subtask1(input1)
   │   self.add_log(f"子任务 1 完成: {result1}")
   │
   ├─▶ 子任务 2
   │   result2 = await self._subtask2(input2)
   │   self.add_log(f"子任务 2 完成: {result2}")
   │
   └─▶ 子任务 3
       result3 = await self._subtask3(input3)
       self.add_log(f"子任务 3 完成: {result3}")

4. 生成工件
   │
   ├─▶ 创建工件列表
   │   artifacts = []
   │
   ├─▶ 添加工件
   │   artifact1 = Artifact(type="code", path="...", content="...")
   │   artifacts.append(artifact1)
   │
   └─▶ 返回工件
       return artifacts

5. 设置指标 (可选)
   │
   ├─▶ 计数指标
   │   self.set_metric("artifacts_count", len(artifacts))
   │
   └─▶ 性能指标
       self.set_metric("execution_time", time.time() - start_time)
```

### 3. 错误处理流程

```
┌──────────────────────────────────────────────────────┐
│                  错误处理流程                          │
└──────────────────────────────────────────────────────┘

execute_impl() 执行过程中发生异常

try:
    # 执行业务逻辑
    artifacts = await self._generate_artifacts(task_input)

except ValueError as e:
    # 输入验证错误
    │
    ├─▶ 记录错误日志
    │   self.add_log(f"输入验证失败: {e}", level="error")
    │
    └─▶ 重新抛出异常
       raise  # 让 BaseAgent.handle_error() 处理

except FileNotFoundError as e:
    # 文件不存在错误
    │
    ├─▶ 记录警告日志
    │   self.add_log(f"文件不存在: {e}", level="warning")
    │
    └─▶ 返回空列表
       return []  # 优雅降级

except asyncio.TimeoutError:
    # 超时错误
    │
    ├─▶ 记录错误日志
    │   self.add_log("执行超时", level="error")
    │
    └─▶ BaseAgent 自动处理
       # result.status = AgentStatus.FAILED
       # result.error = "执行超时"

except Exception as e:
    # 未预期错误
    │
    ├─▶ 记录错误日志
    │   self.add_log(f"未预期错误: {type(e).__name__}: {e}", level="error")
    │
    ├─▶ 记录详细堆栈
    │   logger.exception("详细错误信息:")
    │
    └─▶ 重新抛出异常
       raise  # 让 BaseAgent.handle_error() 处理
```

---

## 🔄 Agent 生命周期

### 状态转换详解

```
┌──────────────────────────────────────────────────────┐
│              Agent 生命周期状态机                      │
└──────────────────────────────────────────────────────┘

[创建]
  │
  ├─▶ BaseAgent.__init__()
  │   agent_id = "xxx"
  │   config = AgentConfig()
  │   status = AgentStatus.IDLE
  │
  ▼
┌─────────────┐
│    IDLE     │  ◀───┐
│   (空闲)     │      │
└──────┬──────┘      │
       │             │
       │ run()       │ 完成后
       │             │
       ▼             │
┌─────────────┐      │
│  WORKING    │      │
│  (工作中)    │──────┘
└──────┬──────┘
       │
       ├──────────┬──────────┬──────────┐
       │          │          │          │
   [成功]     [失败]     [取消]     [超时]
       │          │          │          │
       ▼          ▼          ▼          ▼
 ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐
 │COMPLETED│ │ FAILED  │ │CANCELLED│ │ FAILED  │
│ (已完成)  │ │ (失败)   │ │ (已取消)  │ │ (超时)   │
 └─────────┘ └─────────┘ └─────────┘ └─────────┘
```

### 生命周期钩子

```python
class MyAgent(BaseAgent):
    """带生命周期钩子的 Agent"""

    def on_start(self):
        """任务开始前的钩子"""
        self.add_log(f"任务开始: {self.agent_id}")
        # 初始化资源
        self._init_resources()

    async def execute_impl(self, context, task_input):
        """执行任务"""
        # 业务逻辑
        pass

    def on_complete(self):
        """任务完成后的钩子"""
        self.add_log(f"任务完成: {self.agent_id}")
        # 清理资源
        self._cleanup_resources()

    def on_error(self, error: Exception):
        """发生错误时的钩子"""
        self.add_log(f"任务错误: {error}", level="error")
        # 错误处理
        self._handle_error(error)
```

---

## 📋 Agent 注册机制

### AgentRegistry 架构

```
┌──────────────────────────────────────────────────────┐
│                AgentRegistry (注册中心)                │
├──────────────────────────────────────────────────────┤
│                                                       │
│  _metadata: Dict[AgentType, AgentMetadata]           │
│  │                                                    │
│  ├─── AgentType.PRODUCT_MANAGEMENT                   │
│  │    └──▶ AgentMetadata(                            │
│  │           agent_type=PRODUCT_MANAGEMENT,          │
│  │           impl_class=CodingAgent,                 │
│  │           description="产品需求分析...",           │
│  │           priority=1,                             │
│  │           max_concurrent=3,                       │
│  │           keywords=[r"需求|规划|prd"]             │
│  │       )                                            │
│  │                                                    │
│  ├─── AgentType.BACKEND_DEV                          │
│  │    └──▶ AgentMetadata(...)                        │
│  │                                                    │
│  └─── ... (其他 Agent 类型)                          │
│                                                       │
│  _initialized: bool = False                          │
│                                                       │
└──────────────────────────────────────────────────────┘
```

### 注册流程

```
1. 定义 Agent 类型
   │
   └─▶ common/models.py
       class AgentType(str, Enum):
           MY_CUSTOM_TYPE = "my_custom_type"

2. 实现 Agent 类
   │
   └─▶ execution/my_custom_agent.py
       class MyCustomAgent(BaseAgent):
           # ... 实现

3. 注册到 AgentRegistry
   │
   └─▶ orchestration/registry.py
       @classmethod
       def initialize(cls):
           agents.append(
               AgentMetadata(
                   AgentType.MY_CUSTOM_TYPE,
                   MyCustomAgent,
                   "我的自定义 Agent",
                   priority=10,
                   max_concurrent=5,
                   keywords=[r"自定义|custom"]
               )
           )

4. 初始化注册表
   │
   └─▶ AgentRegistry.initialize()
       # 自动调用(惰性初始化)
```

### 注册方法

```python
class AgentRegistry:
    """Agent 注册中心"""

    @classmethod
    def get_metadata(cls, agent_type: AgentType) -> Optional[AgentMetadata]:
        """获取 Agent 元数据"""
        cls.initialize()
        return cls._metadata.get(agent_type)

    @classmethod
    def get_impl_class(cls, agent_type: AgentType) -> Optional[Type[BaseAgent]]:
        """获取 Agent 实现类"""
        meta = cls.get_metadata(agent_type)
        return meta.impl_class if meta else None

    @classmethod
    def get_description(cls, agent_type: AgentType) -> str:
        """获取 Agent 描述"""
        meta = cls.get_metadata(agent_type)
        return meta.description if meta else "通用 Agent"

    @classmethod
    def get_priority(cls, agent_type: AgentType) -> int:
        """获取 Agent 优先级"""
        meta = cls.get_metadata(agent_type)
        return meta.priority if meta else 99

    @classmethod
    def get_max_concurrent(cls, agent_type: AgentType) -> int:
        """获取最大并发数"""
        meta = cls.get_metadata(agent_type)
        return meta.max_concurrent if meta else 5

    @classmethod
    def get_all_types(cls) -> List[AgentType]:
        """获取所有已注册的 Agent 类型"""
        cls.initialize()
        return list(cls._metadata.keys())

    @classmethod
    def from_string(cls, type_str: str) -> Optional[AgentType]:
        """从字符串转换到 AgentType"""
        try:
            return AgentType(type_str)
        except ValueError:
            # 模糊匹配
            type_str = type_str.lower().replace("_", "-")
            for atype in AgentType:
                if atype.value == type_str:
                    return atype
            return None

    @classmethod
    def get_keywords(cls, agent_type: AgentType) -> List[str]:
        """获取识别关键词"""
        meta = cls.get_metadata(agent_type)
        return meta.keywords if meta else []

    @classmethod
    def get_all_keywords(cls) -> Dict[AgentType, List[str]]:
        """获取所有 Agent 的关键词映射"""
        cls.initialize()
        return {atype: meta.keywords for atype, meta in cls._metadata.items()}
```

---

## 🏭 Agent 工厂模式

### AgentFactory 架构

```
┌──────────────────────────────────────────────────────┐
│                 AgentFactory (工厂)                   │
├──────────────────────────────────────────────────────┤
│                                                       │
│  create_agent()                                      │
│  │                                                    │
│  ├─▶ 1. 从 AgentRegistry 获取实现类                  │
│  │    impl_class = AgentRegistry.get_impl_class(    │
│  │        AgentType.BACKEND_DEV                     │
│  │    )                                             │
│  │                                                  │
│  ├─▶ 2. 验证实现类                                   │
│  │    if not impl_class:                            │
│  │        raise ValueError("不支持的Agent类型")      │
│  │                                                  │
│  ├─▶ 3. 生成 agent_id                               │
│  │    if not agent_id:                              │
│  │        agent_id = f"{agent_type}-{uuid[:6]}"     │
│  │                                                  │
│  ├─▶ 4. 创建 Agent 实例                             │
│  │    agent = impl_class(agent_id=agent_id,         │
│  │                      config=config)             │
│  │                                                  │
│  └─▶ 5. 返回 Agent                                  │
│       return agent                                  │
│                                                       │
└──────────────────────────────────────────────────────┘
```

### 工厂方法

```python
class AgentFactory:
    """Agent 工厂类"""

    @classmethod
    def create_agent(
        cls,
        agent_type: AgentType,
        agent_id: Optional[str] = None,
        config: Optional[AgentConfig] = None
    ) -> BaseAgent:
        """创建 Agent 实例

        Args:
            agent_type: Agent 类型
            agent_id: Agent ID (可选)
            config: Agent 配置 (可选)

        Returns:
            BaseAgent: Agent 实例

        Raises:
            ValueError: 如果 Agent 类型不支持

        Example:
            >>> agent = AgentFactory.create_agent(
            ...     AgentType.BACKEND_DEV,
            ...     agent_id="my-backend-agent"
            ... )
            >>> assert agent.name == "代码生成Agent"
        """
        # 1. 从注册中心获取类
        agent_class = AgentRegistry.get_impl_class(agent_type)

        if not agent_class:
            raise ValueError(f"不支持的Agent类型: {agent_type}")

        # 2. 生成 agent_id
        if not agent_id:
            short_id = uuid.uuid4().hex[:6]
            agent_id = f"{agent_type.value}-{short_id}"

        # 3. 创建实例
        agent = agent_class(agent_id=agent_id, config=config)
        logger.info(f"创建Agent: {agent_id} (类型: {agent_type.value})")
        return agent

    @classmethod
    def get_agent_capabilities(
        cls,
        agent_type: AgentType
    ) -> Set[AgentCapability]:
        """获取 Agent 能力

        Args:
            agent_type: Agent 类型

        Returns:
            Set[AgentCapability]: 能力集合
        """
        agent_class = AgentRegistry.get_impl_class(agent_type)
        if not agent_class:
            return set()

        try:
            return agent_class.get_capabilities()
        except Exception as e:
            logger.error(f"获取 Agent 能力失败: {e}")
            return set()

    @classmethod
    def get_supported_agent_types(cls) -> List[AgentType]:
        """获取支持的 Agent 类型列表

        Returns:
            List[AgentType]: Agent 类型列表
        """
        return AgentRegistry.get_all_types()

    @classmethod
    def is_agent_type_supported(cls, agent_type: AgentType) -> bool:
        """检查 Agent 类型是否支持

        Args:
            agent_type: Agent 类型

        Returns:
            bool: 是否支持
        """
        return AgentRegistry.get_impl_class(agent_type) is not None

    @classmethod
    async def create_agent_pool(
        cls,
        agent_types: Dict[AgentType, int],
        config: Optional[AgentConfig] = None
    ) -> Dict[str, BaseAgent]:
        """异步并发创建 Agent 池

        Args:
            agent_types: Agent 类型和数量的映射
            config: Agent 配置 (可选)

        Returns:
            Dict[str, BaseAgent]: Agent 实例映射

        Example:
            >>> pool = await AgentFactory.create_agent_pool(
            ...     {AgentType.BACKEND_DEV: 3, AgentType.QA_ENGINEERING: 2}
            ... )
            >>> assert len(pool) == 5
        """
        tasks = []
        for agent_type, count in agent_types.items():
            for i in range(count):
                agent_id = f"{agent_type.value}-{i + 1:02d}"
                tasks.append(cls._async_create_agent(agent_type, agent_id, config))

        results = await asyncio.gather(*tasks, return_exceptions=True)

        pool: Dict[str, BaseAgent] = {}
        for result in results:
            if isinstance(result, BaseAgent):
                pool[result.agent_id] = result
            elif isinstance(result, Exception):
                logger.error(f"并发创建 Agent 失败: {result}")

        logger.info(f"并发创建Agent池完成: {len(pool)} 个Agent")
        return pool

    @classmethod
    async def _async_create_agent(
        cls,
        agent_type: AgentType,
        agent_id: str,
        config: Optional[AgentConfig] = None
    ) -> BaseAgent:
        """内部异步创建辅助方法"""
        return cls.create_agent(agent_type, agent_id, config)
```

---

## 🎯 Agent 调度器

### AgentDispatcher 架构

```
┌──────────────────────────────────────────────────────┐
│               AgentDispatcher (调度器)                 │
├──────────────────────────────────────────────────────┤
│                                                       │
│  agent_resources: Dict[str, AgentResource]           │
│  │                                                    │
│  ├─── "backend_dev"                                  │
│  │    └──▶ AgentResource(                           │
│  │           agent_type="backend_dev",               │
│  │           max_concurrent=10,                      │
│  │           current_load=3,                         │
│  │           total_executions=150,                   │
│  │           successful_executions=145,              │
│  │           failed_executions=5,                    │
│  │           average_duration=2.5                    │
│  │       )                                            │
│  │                                                    │
│  └─── ... (其他 Agent 类型)                          │
│                                                       │
│  assignments: Dict[str, AgentAssignment]            │
│  │                                                    │
│  └─── task_id → AgentAssignment(                     │
│           agent_type="backend_dev",                  │
│           agent_id="backend_dev-abc123",              │
│           assigned_at=datetime(...)                  │
│       )                                               │
│                                                       │
│  _lock: asyncio.Lock                                 │
│  _resource_available: asyncio.Condition              │
│                                                       │
└──────────────────────────────────────────────────────┘
```

### 调度流程

```
1. 分配 Agent (assign_agent)
   │
   ├─▶ 1.1 确定 Agent 类型
   │    agent_type = task.inputs.get("agent_type")
   │
   ├─▶ 1.2 检查资源可用性
   │    while resource.current_load >= resource.max_concurrent:
   │        await _resource_available.wait()
   │
   ├─▶ 1.3 分配 Agent
   │    assignment = AgentAssignment(
   │        agent_type=agent_type,
   │        agent_id=f"{agent_type}-{uuid[:6]}",
   │        assigned_at=datetime.now()
   │    )
   │
   ├─▶ 1.4 更新资源状态
   │    resource.current_load += 1
   │    resource.total_executions += 1
   │
   └─▶ 1.5 返回分配结果
        return assignment

2. 执行任务 (execute_with_agent)
   │
   ├─▶ 2.1 分配 Agent
   │    assignment = await assign_agent(task)
   │
   ├─▶ 2.2 执行任务
   │    result = await task_executor.execute(task)
   │
   ├─▶ 2.3 释放 Agent
   │    await release_agent(task.task_id, success, duration)
   │
   └─▶ 2.4 返回结果
        return result

3. 释放 Agent (release_agent)
   │
   ├─▶ 3.1 减少资源负载
   │    resource.current_load -= 1
   │
   ├─▶ 3.2 更新统计信息
   │    if success:
   │        resource.successful_executions += 1
   │    else:
   │        resource.failed_executions += 1
   │
   ├─▶ 3.3 更新平均时长
   │    resource.average_duration = (
   │        (resource.average_duration * (total - 1) + duration) / total
   │    )
   │
   └─▶ 3.4 通知等待的任务
        _resource_available.notify_all()
```

### 调度方法

```python
class AgentDispatcher:
    """Agent 调度器"""

    async def assign_agent(
        self,
        task: TaskExecution,
        preferred_agent: Optional[str] = None,
        timeout: Optional[int] = 300
    ) -> Optional[AgentAssignment]:
        """为任务分配 Agent

        Args:
            task: 任务执行对象
            preferred_agent: 优先使用的 Agent 类型
            timeout: 等待超时时间(秒)

        Returns:
            Optional[AgentAssignment]: Agent 分配结果
        """
        async with self._resource_available:
            # 1. 确定 Agent 类型
            agent_type = preferred_agent or task.inputs.get("agent_type")

            if not agent_type:
                logger.error(f"无法确定任务 {task.task_id} 的Agent类型")
                return None

            # 2. 检查资源
            if agent_type not in self.agent_resources:
                logger.error(f"未找到Agent类型定义: {agent_type}")
                return None

            resource = self.agent_resources[agent_type]

            # 3. 等待资源可用
            start_time = datetime.now()
            while resource.current_load >= resource.max_concurrent:
                if timeout is not None:
                    elapsed = (datetime.now() - start_time).total_seconds()
                    if elapsed >= timeout:
                        logger.warning(f"等待超时: {task.task_id}")
                        return None
                    wait_time = timeout - elapsed
                    try:
                        await asyncio.wait_for(
                            self._resource_available.wait(),
                            timeout=wait_time
                        )
                    except asyncio.TimeoutError:
                        return None
                else:
                    await self._resource_available.wait()

            # 4. 分配 Agent
            assignment = AgentAssignment(
                agent_type=agent_type,
                agent_id=f"{agent_type}-{uuid.uuid4().hex[:6]}",
                assigned_at=datetime.now()
            )

            task.assignment = assignment
            task.status = TaskStatus.ASSIGNED
            resource.current_load += 1
            resource.total_executions += 1
            self.assignments[task.task_id] = assignment

            logger.info(f"任务 {task.task_id} -> {assignment.agent_id}")
            return assignment

    async def release_agent(
        self,
        task_id: str,
        success: bool = True,
        duration: float = 0.0
    ) -> None:
        """释放 Agent 资源

        Args:
            task_id: 任务 ID
            success: 任务是否成功
            duration: 执行时长(秒)
        """
        async with self._resource_available:
            if task_id not in self.assignments:
                logger.warning(f"未找到任务 {task_id} 的Agent分配")
                return

            assignment = self.assignments[task_id]
            agent_type = assignment.agent_type

            # 更新资源统计
            if agent_type in self.agent_resources:
                resource = self.agent_resources[agent_type]
                resource.current_load = max(0, resource.current_load - 1)

                if success:
                    resource.successful_executions += 1
                else:
                    resource.failed_executions += 1

                # 更新平均时长
                total_done = resource.successful_executions + resource.failed_executions
                if resource.average_duration is None:
                    resource.average_duration = duration
                elif total_done > 1:
                    resource.average_duration = (
                        (resource.average_duration * (total_done - 1) + duration) / total_done
                    )
                else:
                    resource.average_duration = duration

            # 移除分配记录
            del self.assignments[task_id]

            # 通知等待的任务
            self._resource_available.notify_all()

            logger.info(f"已释放任务 {task_id} 的Agent资源")

    async def execute_with_agent(
        self,
        task: TaskExecution,
        preferred_agent: Optional[str] = None
    ) -> TaskExecution:
        """使用分配的 Agent 执行任务

        Args:
            task: 任务执行对象
            preferred_agent: 优先使用的 Agent 类型

        Returns:
            TaskExecution: 更新后的任务执行对象
        """
        # 分配 Agent
        assignment = await self.assign_agent(task, preferred_agent)

        if not assignment:
            task.status = TaskStatus.FAILED
            task.error = "无法分配Agent资源"
            task.completed_at = datetime.now()
            return task

        start_time = datetime.now()
        success = False
        duration = 0.0

        try:
            # 执行任务
            if self.task_executor:
                result_task = await self.task_executor.execute(task)
                success = result_task.status == TaskStatus.COMPLETED
                return result_task
            else:
                # 模拟执行
                await asyncio.sleep(0.1)
                task.status = TaskStatus.COMPLETED
                task.completed_at = datetime.now()
                success = True
                return task

        except Exception as e:
            logger.exception(f"执行任务异常: {e}")
            task.status = TaskStatus.FAILED
            task.error = f"执行异常: {str(e)}"
            task.completed_at = datetime.now()
            success = False
            return task

        finally:
            # 计算时长
            duration = (datetime.now() - start_time).total_seconds()
            # 释放 Agent 资源
            await self.release_agent(task.task_id, success=success, duration=duration)

    async def execute_batch(
        self,
        tasks: List[TaskExecution],
        max_concurrent: int = 3
    ) -> List[TaskExecution]:
        """批量执行任务

        Args:
            tasks: 任务列表
            max_concurrent: 总最大并行任务数

        Returns:
            List[TaskExecution]: 更新后的任务列表
        """
        logger.info(f"批量执行 {len(tasks)} 个任务, 总并发限制: {max_concurrent}")

        # 按优先级排序
        priority_order = {
            ExecutionPriority.CRITICAL: 0,
            ExecutionPriority.HIGH: 1,
            ExecutionPriority.NORMAL: 2,
            ExecutionPriority.LOW: 3
        }

        sorted_tasks = sorted(
            tasks,
            key=lambda t: priority_order.get(t.priority, 2)
        )

        # 使用信号量限制总并发
        semaphore = asyncio.Semaphore(max_concurrent)

        async def execute_one(task: TaskExecution):
            async with semaphore:
                return await self.execute_with_agent(task)

        # 并发执行所有任务
        results = await asyncio.gather(
            *[execute_one(task) for task in sorted_tasks],
            return_exceptions=True
        )

        # 处理结果
        final_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                task = sorted_tasks[i]
                task.status = TaskStatus.FAILED
                task.error = f"未捕获的任务执行异常: {str(result)}"
                task.completed_at = datetime.now()
                final_results.append(task)
            else:
                final_results.append(result)

        return final_results

    def get_statistics(self) -> Dict[str, Dict[str, Any]]:
        """获取 Agent 统计信息

        Returns:
            Dict[str, Dict[str, Any]]: Agent 统计信息
        """
        stats = {}

        for agent_type, resource in self.agent_resources.items():
            current, max_c = self.get_agent_load(agent_type)

            stats[agent_type] = {
                "current_load": current,
                "max_concurrent": max_c,
                "utilization": f"{(current / max_c * 100):.1f}%" if max_c > 0 else "0%",
                "total_executions": resource.total_executions,
                "successful_executions": resource.successful_executions,
                "failed_executions": resource.failed_executions,
                "average_duration": resource.average_duration
            }

        return stats
```

---

## 🤝 Agent 协作机制

### 协作模式

#### 1. 串行协作

```python
# Agent A 完成后,Agent B 开始
result_a = await agent_a.execute(context, input_a)
if result_a.success:
    result_b = await agent_b.execute(context, input_b)
    artifacts = result_a.artifacts + result_b.artifacts
```

#### 2. 并行协作

```python
# Agent A 和 Agent B 同时执行
results = await asyncio.gather(
    agent_a.execute(context, input_a),
    agent_b.execute(context, input_b)
)

artifacts = []
for result in results:
    if result.success:
        artifacts.extend(result.artifacts)
```

#### 3. 层次协作

```python
# 主 Agent 创建子 Agent
async def execute_impl(self, context, task_input):
    # 创建子 Agent
    sub_agent1 = AgentFactory.create_agent(AgentType.BACKEND_DEV)
    sub_agent2 = AgentFactory.create_agent(AgentType.QA_ENGINEERING)

    # 执行子 Agent
    result1 = await sub_agent1.execute(context, sub_input1)
    result2 = await sub_agent2.execute(context, sub_input2)

    # 合并结果
    return result1.artifacts + result2.artifacts
```

#### 4. 管道协作

```python
# Agent A 的输出作为 Agent B 的输入
result_a = await agent_a.execute(context, input_a)
if result_a.success:
    # 提取 Agent A 的输出
    output_a = extract_output(result_a.artifacts)

    # 作为 Agent B 的输入
    input_b = transform_input(output_a)
    result_b = await agent_b.execute(context, input_b)
```

---

## 🎨 架构设计原则

### 1. SOLID 原则

#### S - 单一职责原则

每个 Agent 只负责一个特定领域的任务:

```python
# ✅ 好的做法
class RequirementsAgent(BaseAgent):
    """只负责需求分析"""
    pass

class DatabaseAgent(BaseAgent):
    """只负责数据库设计"""
    pass

# ❌ 不好的做法
class FullStackAgent(BaseAgent):
    """做所有事情"""
    pass
```

#### O - 开闭原则

对扩展开放,对修改关闭:

```python
# 添加新 Agent 不需要修改 BaseAgent
class MyNewAgent(BaseAgent):
    """新 Agent"""
    pass

# 注册到 AgentRegistry
AgentRegistry.initialize()
```

#### L - 里氏替换原则

子类可以替换父类:

```python
# 所有 Agent 都可以统一处理
agents = [
    CodingAgent(),
    TestingAgent(),
    DocumentationAgent()
]

for agent in agents:
    result = await agent.execute(context, input)
    # 统一的处理方式
```

#### I - 接口隔离原则

接口专一,避免"胖接口":

```python
# BaseAgent 只定义核心方法
class BaseAgent(ABC):
    @abstractmethod
    async def execute_impl(self, context, task_input):
        pass

    # 其他方法都是可选的
```

#### D - 依赖倒置原则

依赖抽象而非具体实现:

```python
# 依赖 AgentType 抽象,而不是具体 Agent 类
def create_agent(agent_type: AgentType) -> BaseAgent:
    impl_class = AgentRegistry.get_impl_class(agent_type)
    return impl_class()
```

### 2. 其他设计原则

#### KISS (Keep It Simple, Stupid)

保持简单:

```python
# ✅ 简单的实现
async def execute_impl(self, context, task_input):
    artifacts = []
    artifact = Artifact(type="code", path="...", content="...")
    artifacts.append(artifact)
    return artifacts

# ❌ 复杂的实现
async def execute_impl(self, context, task_input):
    # 过度设计
    factory = ArtifactFactory.create(...)
    builder = ArtifactBuilder.builder() \
        .with_type(...) \
        .with_path(...) \
        .with_content(...) \
        .build()
    manager = ArtifactManager.getInstance()
    manager.register(builder)
    return manager.getAll()
```

#### DRY (Don't Repeat Yourself)

避免重复:

```python
# ✅ 提取公共逻辑
def _create_artifact(self, type, path, content):
    return Artifact(type=type, path=path, content=content)

# 使用
artifact1 = self._create_artifact("code", "path1", "content1")
artifact2 = self._create_artifact("doc", "path2", "content2")

# ❌ 重复代码
artifact1 = Artifact(type="code", path="path1", content="content1")
artifact2 = Artifact(type="doc", path="path2", content="content2")
```

#### YAGNI (You Aren't Gonna Need It)

只实现当前需要的功能:

```python
# ✅ 只实现当前需要
class MyAgent(BaseAgent):
    async def execute_impl(self, context, task_input):
        # 只实现当前需求
        pass

# ❌ 实现可能永远用不到的功能
class MyAgent(BaseAgent):
    async def execute_impl(self, context, task_input):
        # 当前需求
        pass

    def advanced_feature1(self):
        # 未来可能需要?实际从未使用
        pass

    def advanced_feature2(self):
        # 未来可能需要?实际从未使用
        pass
```

---

## 📚 相关资源

### 内部文档

- [Agent 开发指南](AGENT_DEVELOPMENT_GUIDE.md)
- [API 参考](AGENT_API_REFERENCE.md)
- [Agent 模板](AGENT_TEMPLATES.md)

### 外部资源

- [设计模式: 可复用面向对象软件的基础](https://www.amazon.com/Design-Patterns-Elements-Reusable-Object-Oriented/dp/0201633612)
- [Clean Code: 代码整洁之道](https://www.amazon.com/Clean-Code-Handbook-Software-Craftsmanship/dp/0132350882)
- [SOLID 原则](https://en.wikipedia.org/wiki/SOLID)

---

**文档版本**: v1.0
**最后更新**: 2026-01-14
**维护者**: SuperAgent v3.2+ 开发团队

---

**祝理解愉快!** 🎉
