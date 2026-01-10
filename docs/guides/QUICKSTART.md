# SuperAgent v3.1 快速开始指南

## 🚀 快速安装

```bash
# 克隆项目
git clone https://github.com/your-org/SuperAgent.git
cd SuperAgent

# 安装依赖
pip install -r requirements.txt

# 验证安装
python -m superagent --version
```

## 📖 基础使用

### 1. 命令行界面

```bash
# 查看帮助
python -m superagent --help

# 查看记忆统计
python -m superagent memory stats

# 查看代码审查状态
python -m superagent review status

# 查看配置
python -m superagent config list
```

### 2. 智能意图识别

```python
from conversation import IntentRecognizer

recognizer = IntentRecognizer()
result = recognizer.recognize("开发一个博客系统")

print(f"主要意图: {result.primary_intent}")
print(f"置信度: {result.confidence}")
print(f"Agent类型: {[agent.value for agent in result.agent_types]}")
```

### 3. 智能规划

```python
from planning import SmartPlanner

planner = SmartPlanner()
plan = await planner.create_smart_plan(
    "开发一个电商网站",
    context={}
)

print(f"步骤数: {len(plan.steps)}")
print(f"估算时间: {plan.estimated_time}")

for step in plan.steps:
    print(f"  - {step.name} ({step.agent_type.value})")
```

### 4. 错误恢复

```python
from orchestration import ErrorRecoverySystem
from memory import MemoryManager

memory_manager = MemoryManager(project_root)
recovery_system = ErrorRecoverySystem(memory_manager)

try:
    # 执行任务
    result = execute_task()
except Exception as e:
    recovery_result = await recovery_system.handle_error(
        error=e,
        task_id="task-001",
        agent_type="backend-dev",
        retry_count=0
    )

    if recovery_result["should_retry"]:
        print(f"建议重试,延迟 {recovery_result['retry_delay']}秒")
```

## 💡 常见用例

### 用例1: 快速原型开发

```python
from conversation import ConversationManager
from planning import SmartPlanner

# 1. 智能识别意图
manager = ConversationManager()
result = manager.smart_recognize("开发一个登录页面")

# 2. 生成智能计划
planner = SmartPlanner()
plan = await planner.create_smart_plan("开发一个登录页面", {})

# 3. 执行计划
# ...
```

### 用例2: 复杂系统构建

```python
# 输入
user_input = "开发一个完整的电商系统,包含用户管理、商品管理、订单处理"

# 智能识别
result = recognizer.recognize(user_input)
# → 识别多个Agent类型

# 智能规划
plan = await planner.create_smart_plan(user_input, {})
# → 生成5-8个步骤,包含依赖关系

# 获取建议
suggestions = planner.get_plan_suggestions(user_input)
# → 复杂度评估,Agent推荐
```

### 用例3: 错误处理和恢复

```python
# 自动错误处理
try:
    await execute_task()
except Exception as e:
    # 错误分类
    error_type = ErrorClassifier.classify(str(e))
    severity = ErrorClassifier.estimate_severity(error_type, str(e))

    # 获取恢复策略
    strategy = RetryStrategy.get_strategy(error_type, severity, retry_count=0)

    # 查询历史修复方案
    recovery_result = await recovery_system.handle_error(e, task_id, agent_type)

    # 应用修复
    if recovery_result["should_retry"]:
        await retry_with_delay(recovery_result["retry_delay"])
```

## 📚 更多资源

- **完整文档**: [docs/](docs/)
- **使用示例**: [docs/USAGE_EXAMPLES.md](docs/USAGE_EXAMPLES.md)
- **架构文档**: [ARCHITECTURE_V3_FINAL.md](ARCHITECTURE_V3_FINAL.md)
- **API文档**: [docs/API.md](docs/API.md) (待生成)

## 🎯 下一步

1. 阅读 [ARCHITECTURE_V3_FINAL.md](ARCHITECTURE_V3_FINAL.md) 了解系统架构
2. 查看 [docs/USAGE_EXAMPLES.md](docs/USAGE_EXAMPLES.md) 学习更多示例
3. 运行测试: `python test_e2e_phase7.py`
4. 开始你的第一个项目!

---

**祝使用愉快! 🎉**
