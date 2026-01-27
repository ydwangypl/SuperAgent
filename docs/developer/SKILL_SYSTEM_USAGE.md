# SuperAgent v3.4.1 技能提取系统 - 使用指南

## 快速开始

### 1. 初始化技能管理器

```python
from pathlib import Path
from extensions.skills import SkillManager

# 初始化
manager = SkillManager(project_root=Path("."))
await manager.initialize()

# 查看统计信息
stats = manager.get_statistics()
print(f"总技能数: {stats['total_skills']}")
print(f"平均评分: {stats['average_score']}")
```

### 2. 集成到 Orchestrator

```python
from pathlib import Path
from orchestration.orchestrator import Orchestrator
from extensions.skills import SkillManager, SkillExtractionHook

# 创建技能管理器
skill_manager = SkillManager(project_root=Path("."))
await skill_manager.initialize()

# 创建技能提取 Hook
skill_hook = SkillExtractionHook(
    project_root=Path("."),
    skill_manager=skill_manager,
    enabled=True
)

# 创建编排器并注册 Hook
orchestrator = Orchestrator(
    project_root=Path("."),
    hooks=[skill_hook]
)

# 执行任务时自动提取技能
await orchestrator.execute_plan(plan)
```

### 3. 查询技能

```python
# 根据错误信息查找技能
skills = await manager.find_by_error("ImportError: No module named 'requests'")
for skill in skills:
    print(f"技能: {skill.name}")
    print(f"评分: {skill.scores.average}/10")
    print(f"解决方案: {skill.solution}")

# 根据关键词查找技能
skills = await manager.find_by_keyword("数据库")

# 获取技能建议
suggestions = await manager.get_suggestions(
    {"description": "用户认证", "error": None}
)
for suggestion in suggestions:
    print(suggestion)
```

## 验证安全功能

### 测试敏感信息脱敏

```python
from extensions.skills import SkillValidator

validator = SkillValidator()

# 测试密码脱敏
code = "db.connect('password=secret123')"
sanitized = validator.sanitize(code)
print(sanitized)
# 输出: db.connect('password={{REDACTED}}')

# 测试 API 密钥脱敏
code2 = "api_key=sk-1234567890"
sanitized2 = validator.sanitize(code2)
print(sanitized2)
# 输出: api_key={{REDACTED}}

# 测试危险操作检测
is_safe, warnings = validator.validate_safety("os.system('rm -rf /')")
print(f"安全: {is_safe}, 警告: {warnings}")
```

## 示例：完整工作流

```python
import asyncio
from pathlib import Path
from extensions.skills import SkillManager, SkillExtractor, SkillCard

async def main():
    # 1. 初始化
    manager = SkillManager(Path("."))
    await manager.initialize()

    # 2. 模拟一个任务执行结果
    task = {
        "type": "coding",
        "description": "解决 ImportError 问题",
        "id": "task_001"
    }
    result = {
        "success": True,
        "output": """
遇到 ImportError: No module named 'requests'
解决方案: pip install requests
验证: 安装后成功导入
        """
    }

    # 3. 评估是否提取技能
    extractor = SkillExtractor()
    gate_result = await extractor.evaluate(
        task=task,
        result=result,
        context={}
    )

    if gate_result.passed:
        print("✓ 通过质量门禁")

        # 4. 创建技能卡
        skill = SkillCard(
            skill_id=extractor.generate_skill_id(task),
            name="解决 ImportError 依赖缺失",
            category=gate_result.category,
            skill_type=gate_result.skill_type,
            scores=gate_result.scores,
            problem_scenario="ImportError: No module named 'requests'",
            solution="使用 pip install requests 安装依赖",
            code_example="pip install requests"
        )

        # 5. 保存技能
        success = await manager.save_skill(skill)
        if success:
            print(f"✓ 技能已保存: {skill.name}")
    else:
        print(f"✗ 未通过门禁: {gate_result.reason}")

if __name__ == "__main__":
    asyncio.run(main())
```

## 文件结构

```
.superagent/
└── skills/
    ├── skill_20260127_123456_abc123def.md  # 技能卡文件
    ├── skills_index.json                  # 全局索引
    └── error_patterns.json                # 错误模式索引
```

## 技能卡格式示例

```markdown
---
skill_id: skill_20260127_123456_abc123def
name: 解决 ImportError 依赖缺失
category: error_resolution
skill_type: solution

# Quality Scores
reusability: 8
generality: 7
clarity: 7
uniqueness: 5
avg_score: 6.8

# Retrieval Optimization
error_pattern: ImportError: No module named [\\w]+
error_tags: import, dependency
trigger_keywords: import, pip, install

# Metadata
source_task: task_001
source_agent: SuperAgent
created_at: 2024-01-27T12:34:56
usage_count: 0
version: 1.0
---

# 解决 ImportError 依赖缺失

## 问题场景
ImportError: No module named 'requests'

## 解决方案
使用 pip install requests 安装依赖

## 实施步骤
1. 打开终端
2. 运行: pip install requests
3. 验证安装: import requests

## 代码示例
```python
pip install requests
```

## 替代方案
- 使用 conda install requests
- 从源码编译安装
```

## 测试验证

运行测试验证系统功能：

```bash
# 快速测试
python tests/test_skills_core.py

# 完整 pytest 测试
pytest tests/test_skills_core.py -v

# 带覆盖率测试
pytest tests/test_skills_core.py --cov=extensions.skills --cov-report=html
```

预期输出：
- TestSkillModels: 3/3 passed
- TestSkillValidator: 4/4 passed
- TestSkillExtractor: 5/5 passed
- TestSkillEvaluator: 4/4 passed (阶段2)
- TestSkillContextAdapter: 2/2 passed (阶段2)
- Total: 18/18 passed

## 阶段 2 高级功能

### 1. 技能评分与淘汰 (SkillEvaluator)

```python
from extensions.skills import SkillEvaluator, SkillManager
from pathlib import Path

manager = SkillManager(project_root=Path("."))
evaluator = SkillEvaluator(skills_dir=Path(".superagent/skills"))

# 记录技能应用反馈
skill_id = "skill_20260127_123456_abc123def"
feedback = await evaluator.record_feedback(
    skill_id=skill_id,
    task_success=True,  # 任务成功
    context={"agent": "CodingAgent", "task_id": "task_001"}
)

# 更新技能评分（成功 +0.5，失败 -1.0）
skill = await manager.get_skill(skill_id)
updated_skill = evaluator.update_scores(skill, task_success=True)

# 检查是否应该淘汰
if evaluator.should_deprecate(updated_skill):
    await evaluator.deprecate_skill(updated_skill)
    print(f"技能 {skill.name} 已废弃（平均分 {updated_skill.scores.average}）")
```

**评分规则**:
- **成功**: reusability +0.5, clarity +0.5 (上限 10)
- **失败**: reusability -1.0, clarity -1.0, generality -0.5 (下限 1)
- **淘汰阈值**: 平均分 < 4.0

### 2. JIT 实时技能注入 (SkillContextAdapter)

```python
from extensions.skills import SkillContextAdapter, SkillManager
from pathlib import Path

manager = SkillManager(project_root=Path("."))
adapter = SkillContextAdapter(skill_manager=manager)

# 场景 1: 错误发生时自动注入相关技能
error_message = "ImportError: No module named 'requests'"

skills = await adapter.inject_on_error(error_message, max_skills=3)

for skill in skills:
    print(skill)
    # 输出:
    # ### 解决 ImportError 依赖缺失
    # **评分**: 8.5/10 (重用:9, 通用:8)
    # **使用次数**: 15
    # **问题**: ImportError: No module named 'requests'
    # **方案**: 使用 pip install requests 安装依赖...

# 场景 2: 根据任务描述注入技能建议
description = "需要实现用户认证功能"

skills = await adapter.inject_by_keyword(description, max_skills=2)

# 场景 3: 获取完整的上下文注入（用于 Agent Prompt）
context = {
    "description": "开发登录功能",
    "error": "AttributeError: 'User' object has no attribute 'password'"
}

injection = await adapter.get_context_injection(context, max_skills=3)

print(injection)
# 输出:
# ## 相关技能（基于错误匹配）
# ### 解决用户模型属性错误
# **评分**: 7.5/10 ...
#
# ## 相关技能（基于关键词）
# ### 实现用户密码加密
# **评分**: 8.0/10 ...
```

**压缩策略**:
- 只保留核心信息（名称、评分、使用次数）
- 问题场景截断到 100 字符
- 解决方案截断到 150 字符
- 代码示例 < 200 字符才包含

### 3. 完整工作流示例

```python
import asyncio
from pathlib import Path
from extensions.skills import (
    SkillManager, SkillExtractionHook, SkillEvaluator, SkillContextAdapter
)
from orchestration.orchestrator import Orchestrator

async def main():
    # 1. 初始化
    manager = SkillManager(Path("."))
    await manager.initialize()

    evaluator = SkillEvaluator(Path(".superagent/skills"))
    adapter = SkillContextAdapter(manager)

    # 2. 执行任务并自动提取技能
    hook = SkillExtractionHook(Path("."), manager, enabled=True)
    orchestrator = Orchestrator(Path("."), hooks=[hook])

    # 3. 模拟任务执行
    result = await orchestrator.execute_plan(plan)

    # 4. 记录反馈（如果使用了技能）
    if result.success:
        await evaluator.record_feedback(
            skill_id="used_skill_id",
            task_success=True,
            context={"task_id": result.task_id}
        )

    # 5. 实时技能注入（用于下一次任务）
    if result.error:
        skills = await adapter.inject_on_error(str(result.error))
        print("建议的技能:")
        for skill in skills:
            print(f"- {skill}")

if __name__ == "__main__":
    asyncio.run(main())
```

## API 参考

### SkillEvaluator

| 方法 | 参数 | 返回值 | 说明 |
|------|------|--------|------|
| `record_feedback()` | skill_id, task_success, context | Dict | 记录技能应用反馈 |
| `update_scores()` | skill, task_success | SkillCard | 更新技能评分 |
| `should_deprecate()` | skill | bool | 检查是否应淘汰 |
| `deprecate_skill()` | skill | None | 淘汰技能（标记版本） |

### SkillContextAdapter

| 方法 | 参数 | 返回值 | 说明 |
|------|------|--------|------|
| `inject_on_error()` | error_message, max_skills | List[str] | 错误匹配注入 |
| `inject_by_keyword()` | description, max_skills | List[str] | 关键词注入 |
| `get_context_injection()` | context, max_skills | str | 完整上下文注入 |
| `_compress_skill()` | skill | str | 压缩技能内容 |
| `_extract_keywords()` | text | List[str] | 提取关键词 |

## 阶段 3 高级功能

### 1. 记忆自动晋升 (EpisodicToProceduralPromoter)

```python
from extensions.skills import EpisodicToProceduralPromoter, SkillManager, SkillExtractor
from pathlib import Path
from memory.memory_manager import MemoryManager

# 初始化
manager = SkillManager(project_root=Path("."))
await manager.initialize()

extractor = SkillExtractor()
promoter = EpisodicToProceduralPromoter(
    skill_manager=manager,
    skill_extractor=extractor,
    min_occurrences=3  # 至少出现3次才晋升
)

# 场景 1: 从情节记忆列表晋升
episodic_memories = [
    {
        "content": "解决 ImportError: No module named 'requests'\n方案: pip install requests",
        "metadata": {
            "error": "ImportError: No module named 'requests'",
            "task_type": "coding",
            "success": True
        },
        "timestamp": "2024-01-28T00:00:00"
    },
    {
        "content": "修复 ImportError: No module named 'numpy'\nfix: pip install numpy",
        "metadata": {
            "error": "ImportError: No module named 'numpy'",
            "task_type": "coding",
            "success": True
        },
        "timestamp": "2024-01-28T01:00:00"
    },
    {
        "content": "再次解决 ImportError: No module named 'pandas'\nresolve: pip install pandas",
        "metadata": {
            "error": "ImportError: No module named 'pandas'",
            "task_type": "coding",
            "success": True
        },
        "timestamp": "2024-01-28T02:00:00"
    },
]

promoted_skills = await promoter.promote_from_memories(episodic_memories)

for skill in promoted_skills:
    print(f"晋升技能: {skill.name}")
    print(f"评分: {skill.scores.average}/10")
    print(f"使用次数: {skill.usage_count}")
    # 输出:
    # 晋升技能: 自动晋升: Error Import
    # 评分: 7.5/10
    # 使用次数: 3

# 场景 2: 从 MemoryManager 自动晋升
memory_manager = MemoryManager(project_root=Path("."))

promoted = await promoter.auto_promote_from_memory_manager(memory_manager)

print(f"从 {len(episodic_memories)} 条记忆中晋升了 {len(promoted)} 个技能")
```

**晋升策略**:
1. **模式识别**: 从情节记忆中识别重复模式
   - 错误类型模式（如 `ImportError`, `AttributeError`）
   - 编程模式（如 `function_definition`, `class_definition`）
   - 解决方案模式（如 "解决XXX问题"）

2. **频率阈值**: 至少出现 `min_occurrences` 次（默认3次）

3. **质量门禁**: 使用 `SkillExtractor` 评估是否满足质量标准

4. **去重**: 检查是否已存在相似技能，避免重复

**支持的签名类型**:
- `error_<ErrorType>` - 错误模式（如 `error_ImportError`）
- `import_pattern` - 导入语句模式
- `function_definition` - 函数定义模式
- `class_definition` - 类定义模式
- `async_function` - 异步函数模式
- `decorator_usage` - 装饰器使用模式
- `context_manager` - 上下文管理器模式
- `solution_<Keyword>` - 解决方案模式

### 2. 完整自动化工作流

```python
import asyncio
from pathlib import Path
from extensions.skills import (
    SkillManager, SkillExtractionHook, SkillEvaluator,
    SkillContextAdapter, EpisodicToProceduralPromoter
)
from memory.memory_manager import MemoryManager
from orchestration.orchestrator import Orchestrator

async def autonomous_skill_lifecycle():
    """完整的技能生命周期自动化"""

    # 1. 初始化所有组件
    manager = SkillManager(Path("."))
    await manager.initialize()

    memory_manager = MemoryManager(Path("."))

    extractor = SkillExtractor()
    evaluator = SkillEvaluator(Path(".superagent/skills"))
    adapter = SkillContextAdapter(manager)
    promoter = EpisodicToProceduralPromoter(manager, extractor)

    # 2. 执行任务并自动提取技能
    hook = SkillExtractionHook(Path("."), manager, enabled=True)
    orchestrator = Orchestrator(Path("."), hooks=[hook])

    result = await orchestrator.execute_plan(plan)

    # 3. 如果成功，记录正面反馈
    if result.success:
        # 记录到情节记忆
        await memory_manager.save_episodic_memory(
            content=f"成功完成任务: {result.task_id}",
            metadata={"task_id": result.task_id, "success": True}
        )

        # 如果使用了技能，更新评分
        if hasattr(result, 'used_skill_id'):
            await evaluator.record_feedback(
                skill_id=result.used_skill_id,
                task_success=True
            )

    # 4. 如果失败，实时注入相关技能
    if result.error:
        skills = await adapter.inject_on_error(str(result.error))
        if skills:
            print("💡 建议的技能:")
            for skill in skills:
                print(f"  - {skill}")

        # 记录失败到情节记忆
        await memory_manager.save_episodic_memory(
            content=f"任务失败: {result.error}",
            metadata={
                "task_id": result.task_id,
                "error": str(result.error),
                "success": False
            }
        )

    # 5. 定期从记忆晋升技能（如每天一次）
    promoted = await promoter.auto_promote_from_memory_manager(memory_manager)
    if promoted:
        print(f"✨ 自动晋升了 {len(promoted)} 个新技能")
        for skill in promoted:
            await manager.save_skill(skill)

    # 6. 定期淘汰低分技能（如每周一次）
    all_skills = await manager.get_all_skills()
    for skill in all_skills:
        if evaluator.should_deprecate(skill):
            await evaluator.deprecate_skill(skill)
            print(f"🗑️ 淘汰技能: {skill.name} (评分: {skill.scores.average})")

if __name__ == "__main__":
    asyncio.run(autonomous_skill_lifecycle())
```

### 3. API 参考

#### EpisodicToProceduralPromoter

| 方法 | 参数 | 返回值 | 说明 |
|------|------|--------|------|
| `promote_from_memories()` | episodic_memories | List[SkillCard] | 从记忆列表晋升 |
| `auto_promote_from_memory_manager()` | memory_manager | List[SkillCard] | 从 MemoryManager 晋升 |
| `_identify_repeating_patterns()` | memories | Dict | 识别重复模式 |
| `_extract_pattern_signature()` | memory | Optional[str] | 提取模式签名 |
