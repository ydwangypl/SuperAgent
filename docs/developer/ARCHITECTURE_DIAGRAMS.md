# SuperAgent 架构图

**版本**: 3.0
**日期**: 2026-01-10

---

## 1. 当前架构图 (Before)

```
┌─────────────────────────────────────────────────────────────┐
│                    SuperAgent v3.2 (当前)                    │
└─────────────────────────────────────────────────────────────┘

┌──────────────┐
│   CLI        │
│  (cli/)      │
└──────┬───────┘
       │
       ▼
┌──────────────┐
│ Conversation │
│  (对话管理)   │  ✅ 通用
└──────┬───────┘
       │
       ▼
┌──────────────┐
│  Planning    │
│  (计划生成)   │  ✅ 通用
└──────┬───────┘
       │
       ▼
┌──────────────┐
│Orchestration │
│  (编排层)     │  ⚠️  代码导向
└──────┬───────┘
       │
       ├─────────────────┐
       │                 │
       ▼                 ▼
┌──────────────┐  ┌──────────────┐
│  Execution   │  │   Review     │
│   (执行层)    │  │   (审查层)    │
│              │  │              │
│ ❌ 硬编码     │  │ ❌ 硬编码     │
│ 只支持代码    │  │ 只支持代码    │
└──────────────┘  └──────────────┘

问题:
1. Execution 硬编码为代码执行
2. Review 硬编码为代码审查
3. 无法扩展到其他领域
```

---

## 2. 目标架构图 (After)

```
┌─────────────────────────────────────────────────────────────┐
│                  SuperAgent v3.2 (重构后)                    │
└─────────────────────────────────────────────────────────────┘

┌──────────────┐
│   CLI        │
│  (cli/)      │
└──────┬───────┘
       │
       ▼
┌──────────────┐
│ Conversation │
│  (对话管理)   │  ✅ 保持不变
└──────┬───────┘
       │
       ▼
┌──────────────┐
│  Planning    │
│  (计划生成)   │  ✅ 保持不变
└──────┬───────┘
       │
       ▼
┌──────────────┐
│Orchestration │
│  (编排层)     │  ✅ 使用抽象接口
└──────┬───────┘
       │
       ▼
┌─────────────────────────────────────────┐
│         Core (抽象层) 🆕                │
│  ┌────────────────┐  ┌──────────────┐ │
│  │ Executor ABC   │  │ Reviewer ABC │ │
│  │  (执行器抽象)   │  │  (审查器抽象) │ │
│  └────────────────┘  └──────────────┘ │
└─────────────────┬─────────────────────┘
                  │
         ┌────────┴─────────┐
         │                  │
         ▼                  ▼
┌────────────────┐  ┌────────────────┐
│  Execution     │  │    Review      │
│   (执行层)      │  │    (审查层)     │
│                │  │                │
│ ┌────────────┐ │  │ ┌────────────┐ │
│ │CodeExecutor│ │  │ │CodeReviewer│ │ │
│ └────────────┘ │  │ └────────────┘ │
│ ┌────────────┐ │  │ ┌────────────┐ │
│ │WritingExec.│ │  │ │ContentRev. │ │ │ 🆕
│ └────────────┘ │  │ └────────────┘ │
│ ┌────────────┐ │  │ ┌────────────┐ │
│ │DesignExec. │ │  │ │DesignRev. │ │ │ 🆕
│ └────────────┘ │  │ └────────────┘ │
└────────────────┘  └────────────────┘

优势:
1. ✅ Core 层定义抽象接口
2. ✅ Execution 支持多种执行器
3. ✅ Review 支持多种审查器
4. ✅ 添加新领域无需修改核心代码
```

---

## 3. 模块依赖关系图

### 当前依赖 (Before)

```
Orchestrator
    │
    ├── depends on → CodeExecutor (具体实现) ❌
    │
    └── depends on → CodeReviewer (具体实现) ❌

问题: 依赖具体,违反依赖倒置原则
```

### 目标依赖 (After)

```
Orchestrator
    │
    ├── depends on → Executor (抽象接口) ✅
    │                   │
    │                   ├── implements → CodeExecutor
    │                   ├── implements → WritingExecutor 🆕
    │                   └── implements → DesignExecutor 🆕
    │
    └── depends on → Reviewer (抽象接口) ✅
                        │
                        ├── implements → CodeReviewer
                        ├── implements → ContentReviewer 🆕
                        └── implements → DesignReviewer 🆕

优势: 依赖抽象,符合依赖倒置原则
```

---

## 4. 类图

### 核心抽象类

```
┌─────────────────────────────────┐
│           <<abstract>>           │
│           Executor               │
├─────────────────────────────────┤
│ + execute(task: Task)           │
│ + can_handle(type: str): bool   │
│ + get_supported_types(): List   │
└─────────────────────────────────┘
            △
            │
            ├── implements
            │
    ┌───────┴────────┐
    │                │
    ▼                ▼
┌──────────┐  ┌─────────────┐
│ CodeExec.│  │ WritingExec.│
└──────────┘  └─────────────┘
```

```
┌─────────────────────────────────┐
│           <<abstract>>           │
│           Reviewer               │
├─────────────────────────────────┤
│ + review(artifact: Artifact)    │
│ + can_review(type: str): bool   │
│ + get_supported_types(): List   │
└─────────────────────────────────┘
            △
            │
            ├── implements
            │
    ┌───────┴────────┐
    │                │
    ▼                ▼
┌──────────┐  ┌─────────────┐
│CodeRev.  │  │ ContentRev. │
└──────────┘  └─────────────┘
```

---

## 5. 时序图

### 代码生成流程 (当前和重构后)

```
用户          Orchestrator   Executor    CodeExecutor
 │                │             │             │
 │─ 生成代码 ────>│             │             │
 │                │─ execute ──>│             │
 │                │             │─ can_handle? │
 │                │             │<─ yes ──────│
 │                │             │─ execute ──>│
 │                │             │             │
 │                │<─ result ───│<─ result ───│
 │<─ 代码 ────────│             │             │
```

### 内容写作流程 (新增)

```
用户          Orchestrator   Executor    WritingExecutor
 │                │             │                │
 │─ 写文章 ──────>│             │                │
 │                │─ execute ──>│                │
 │                │             │─ can_handle?   │
 │                │             │<─ yes ─────────│
 │                │             │─ execute ─────>│
 │                │             │                │
 │                │<─ result ───│<─ result ──────│
 │<─ 文章 ────────│             │                │
```

---

## 6. 包结构图

### 当前结构

```
superagent/
├── cli/
├── conversation/
├── planning/
├── orchestration/
├── execution/
│   └── executor.py (代码执行)
├── review/
│   ├── reviewer.py (代码审查)
│   └── ralph_wiggum.py (代码改进)
├── memory/
├── config/
└── utils/
```

### 重构后结构

```
superagent/
├── cli/
├── conversation/
├── planning/
├── orchestration/
├── core/ 🆕 (抽象层)
│   ├── executor.py (Executor ABC)
│   └── reviewer.py (Reviewer ABC)
├── execution/
│   ├── base_executor.py
│   ├── code_executor.py
│   ├── writing_executor.py 🆕
│   └── design_executor.py 🆕
├── review/
│   ├── base_reviewer.py
│   ├── code_reviewer.py
│   ├── content_reviewer.py 🆕
│   ├── design_reviewer.py 🆕
│   └── ralph_wiggum.py (通用化)
├── memory/
├── config/
└── utils/
```

---

## 7. 数据流图

### 当前数据流 (代码专用)

```
用户需求
    │
    ▼
对话管理 ──→ 意图识别
                │
                ▼
            计划生成
                │
                ▼
            编排
                │
        ┌───────┴───────┐
        │               │
        ▼               ▼
    代码执行        代码审查
        │               │
        └───────┬───────┘
                │
                ▼
            最终成果
```

### 目标数据流 (多领域支持)

```
用户需求
    │
    ▼
对话管理 ──→ 意图识别 (识别类型)
                │
                ▼
            计划生成 (通用)
                │
                ▼
            编排 (根据类型选择)
                │
        ┌───────┴────────┐
        │                │
        ▼                ▼
    执行层            审查层
        │                │
    ┌───┴───┐      ┌───┴───┐
    │       │      │       │
    ▼       ▼      ▼       ▼
  代码   写作   代码   内容
  执行   执行   审查   审查
    │       │      │       │
    └───┬───┘      └───┬───┘
        │               │
        └───────┬───────┘
                │
                ▼
            最终成果
```

---

## 8. 重构步骤图

```
第 1 阶段: 抽象层建立 (2-3 天)
    │
    ├─ 创建 core/ 目录
    ├─ 定义 Executor ABC
    ├─ 定义 Reviewer ABC
    └─ 单元测试
    │
    ▼
第 2 阶段: 现有代码迁移 (3-4 天)
    │
    ├─ CodeExecutor 实现 Executor
    ├─ CodeReviewer 实现 Reviewer
    ├─ Orchestrator 使用抽象接口
    └─ 保持向后兼容
    │
    ▼
第 3 阶段: 扩展性验证 (2-3 天)
    │
    ├─ 实现 WritingExecutor
    ├─ 实现 ContentReviewer
    └─ 集成测试
    │
    ▼
第 4 阶段: 清理和优化 (1-2 天)
    │
    ├─ 删除弃用代码
    ├─ 性能优化
    └─ 文档更新
    │
    ▼
完成 ✅
```

---

## 9. 扩展示例

### 添加"绘画"领域

```
步骤 1: 创建执行器
┌─────────────────────────────┐
│ class PaintingExecutor:      │
│     def execute(self, task): │
│         # 生成绘画            │
│         pass                 │
└─────────────────────────────┘

步骤 2: 创建审查器
┌─────────────────────────────┐
│ class PaintingReviewer:      │
│     def review(self, artifact)│
│         # 审查绘画            │
│         pass                 │
└─────────────────────────────┘

步骤 3: 注册到 Orchestrator
orchestrator = Orchestrator([
    CodeExecutor(),
    WritingExecutor(),
    PaintingExecutor(),  # 🆕 只需添加这一行
])

完成! ✅ 无需修改核心代码
```

---

**文档版本**: 3.0
**最后更新**: 2026-01-10
