# SuperAgent Agent 交互式教程

> **版本**: v3.2+
> **更新日期**: 2026-01-14
> **目标读者**: 希望通过实践学习 Agent 开发的开发者

---

## 📋 教程概览

本教程将通过 5 个渐进式的实践项目,带你从零开始掌握 SuperAgent Agent 开发。

### 教程路线图

```
第 1 课: Hello World Agent (入门)
    ↓
第 2 课: 文档生成 Agent (基础)
    ↓
第 3 课: 代码生成 Agent (进阶)
    ↓
第 4 课: 重构 Agent (高级)
    ↓
第 5 课: 组合 Agent (专家)
```

### 学习目标

完成本教程后,你将能够:
- ✅ 创建自定义 Agent
- ✅ 理解 Agent 架构
- ✅ 实现 Agent 协作
- ✅ 处理错误和异常
- ✅ 编写测试

---

## 📚 第 1 课: Hello World Agent (入门)

### 目标

创建一个简单的 Agent,返回 "Hello, World!" 消息。

### 步骤

#### 1.1 创建文件

在 `execution/` 目录下创建文件 `hello_agent.py`:

```bash
touch execution/hello_agent.py
```

#### 1.2 编写代码

复制以下代码到 `hello_agent.py`:

```python
#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Hello World Agent - 最简单的 Agent 示例
"""

from typing import List, Dict, Any, Set
from execution.base_agent import BaseAgent
from execution.models import (
    AgentCapability,
    AgentContext,
    Artifact
)


class HelloAgent(BaseAgent):
    """Hello World Agent"""

    @property
    def name(self) -> str:
        """返回 Agent 名称"""
        return "Hello World Agent"

    @classmethod
    def get_capabilities(cls) -> Set[AgentCapability]:
        """返回 Agent 能力"""
        return {AgentCapability.CODE_GENERATION}

    async def execute_impl(
        self,
        context: AgentContext,
        task_input: Dict[str, Any]
    ) -> List[Artifact]:
        """执行逻辑"""
        # 创建工件
        artifact = Artifact(
            type="documentation",
            path="hello.txt",
            content="Hello, World!",
            metadata={"source": "HelloAgent"}
        )

        return [artifact]
```

#### 1.3 注册 Agent

在 `orchestration/registry.py` 中添加注册:

```python
from execution.hello_agent import HelloAgent

# 在 initialize() 方法的 agents 列表中添加:
AgentMetadata(
    AgentType.HELLO_WORLD,  # 需要在 common/models.py 中定义
    HelloAgent,
    "Hello World 示例 Agent",
    priority=99,
    max_concurrent=5,
    keywords=[r"hello|测试|demo"]
)
```

#### 1.4 定义 Agent 类型

在 `common/models.py` 中添加:

```python
class AgentType(str, Enum):
    # ... 现有类型 ...
    HELLO_WORLD = "hello_world"  # 新增
```

#### 1.5 运行测试

创建测试文件 `tests/test_hello_agent.py`:

```python
import pytest
from execution.hello_agent import HelloAgent
from execution.models import AgentContext


@pytest.mark.asyncio
async def test_hello_agent():
    """测试 HelloAgent"""
    agent = HelloAgent(agent_id="test-hello")

    context = AgentContext(
        task_id="test-1",
        step_id="step-1",
        project_root="/tmp/test",
        worktree_path=None
    )

    result = await agent.execute(context, {})

    assert result.success is True
    assert len(result.artifacts) == 1
    assert result.artifacts[0].content == "Hello, World!"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
```

运行测试:

```bash
pytest tests/test_hello_agent.py -v
```

### 验收标准

- [ ] Agent 创建成功
- [ ] 测试通过
- [ ] 返回 "Hello, World!" 消息

---

## 📝 第 2 课: 文档生成 Agent (基础)

### 目标

创建一个 Agent,根据输入生成 Markdown 文档。

### 步骤

#### 2.1 创建文件

创建 `execution/doc_generator_agent.py`:

```python
#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
文档生成 Agent - 根据输入生成 Markdown 文档
"""

from typing import List, Dict, Any, Set
from datetime import datetime
from execution.base_agent import BaseAgent
from execution.models import (
    AgentCapability,
    AgentContext,
    Artifact
)


class DocGeneratorAgent(BaseAgent):
    """文档生成 Agent"""

    def __init__(self, agent_id: str = "doc-generator"):
        super().__init__(agent_id)
        self._template = """# {title}

{description}

## 功能特性

{features}

## 快速开始

```bash
# 安装
pip install -r requirements.txt

# 运行
python main.py
```

## 文档生成时间

{datetime}
"""

    @property
    def name(self) -> str:
        return "文档生成 Agent"

    @classmethod
    def get_capabilities(cls) -> Set[AgentCapability]:
        return {AgentCapability.DOCUMENTATION}

    def validate_input(self, task_input: Dict[str, Any]) -> bool:
        """验证输入"""
        required_fields = ["title", "description"]
        for field in required_fields:
            if field not in task_input:
                self.add_log(f"缺少必需字段: {field}", level="error")
                return False
        return True

    async def execute_impl(
        self,
        context: AgentContext,
        task_input: Dict[str, Any]
    ) -> List[Artifact]:
        """生成文档"""
        # 提取参数
        title = task_input.get("title", "未命名文档")
        description = task_input.get("description", "")
        features = task_input.get("features", [])

        # 添加思考过程
        self.add_thought(
            step=1,
            thought=f"分析文档需求: {title}",
            action=f"提取描述和功能列表"
        )

        # 格式化特性列表
        features_text = "\\n".join(f"- {f}" for f in features) if features else "- 待添加"

        # 生成内容
        content = self._template.format(
            title=title,
            description=description,
            features=features_text,
            datetime=datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        )

        self.add_thought(
            step=2,
            thought="生成 Markdown 文档",
            action=f"创建文档文件: {title}.md"
        )

        # 创建工件
        artifact = Artifact(
            type="documentation",
            path=f"docs/{title.lower().replace(' ', '_')}.md",
            content=content,
            metadata={
                "format": "markdown",
                "title": title,
                "features_count": len(features)
            }
        )

        self.add_log(f"文档生成完成: {artifact.path}")
        self.set_metric("document_length", len(content))

        return [artifact]
```

#### 2.2 测试 Agent

创建 `tests/test_doc_generator_agent.py`:

```python
import pytest
from execution.doc_generator_agent import DocGeneratorAgent
from execution.models import AgentContext


@pytest.mark.asyncio
async def test_doc_generator_basic():
    """测试基本文档生成"""
    agent = DocGeneratorAgent(agent_id="test-doc-gen")

    context = AgentContext(
        task_id="test-1",
        step_id="step-1",
        project_root="/tmp/test",
        worktree_path=None
    )

    task_input = {
        "title": "我的项目",
        "description": "这是一个测试项目",
        "features": ["功能1", "功能2", "功能3"]
    }

    result = await agent.execute(context, task_input)

    assert result.success is True
    assert len(result.artifacts) == 1
    assert "# 我的项目" in result.artifacts[0].content
    assert "功能1" in result.artifacts[0].content


@pytest.mark.asyncio
async def test_doc_generator_validation():
    """测试输入验证"""
    agent = DocGeneratorAgent(agent_id="test-doc-gen-2")

    context = AgentContext(
        task_id="test-2",
        step_id="step-1",
        project_root="/tmp/test",
        worktree_path=None
    )

    # 缺少必需字段
    task_input = {
        "title": "测试"
        # 缺少 description
    }

    result = await agent.execute(context, task_input)

    assert result.success is False


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
```

### 挑战任务

1. 添加目录(TOC)生成功能
2. 支持多种输出格式(Markdown, HTML, TXT)
3. 添加代码高亮支持

### 验收标准

- [ ] 正确生成 Markdown 文档
- [ ] 输入验证正常工作
- [ ] 测试通过
- [ ] 日志记录完整

---

## 💻 第 3 课: 代码生成 Agent (进阶)

### 目标

创建一个 Agent,根据需求生成 Python 代码框架。

### 步骤

#### 3.1 创建文件

创建 `execution/code_generator_agent.py`:

```python
#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
代码生成 Agent - 根据需求生成 Python 代码框架
"""

import re
from typing import List, Dict, Any, Set
from execution.base_agent import BaseAgent
from execution.models import (
    AgentCapability,
    AgentContext,
    Artifact
)


class CodeGeneratorAgent(BaseAgent):
    """代码生成 Agent"""

    @property
    def name(self) -> str:
        return "代码生成 Agent"

    @classmethod
    def get_capabilities(cls) -> Set[AgentCapability]:
        return {
            AgentCapability.CODE_GENERATION,
            AgentCapability.ARCHITECTURE
        }

    async def plan(
        self,
        context: AgentContext,
        task_input: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """规划代码生成步骤"""
        self.add_step("analyze", "分析需求", "需求列表")
        self.add_step("design", "设计结构", "目录结构")
        self.add_step("generate", "生成代码", "代码文件")
        return self.steps

    async def execute_impl(
        self,
        context: AgentContext,
        task_input: Dict[str, Any]
    ) -> List[Artifact]:
        """生成代码"""
        description = task_input.get("description", "")
        tech_stack = task_input.get("tech_stack", ["Python"])

        # 步骤 1: 分析需求
        self.add_thought(
            step=1,
            thought=f"分析需求: {description}",
            action="识别功能点"
        )

        features = self._extract_features(description)
        self.add_log(f"识别到 {len(features)} 个功能点")

        # 步骤 2: 设计结构
        self.add_thought(
            step=2,
            thought="设计项目结构",
            action="确定文件组织"
        )

        structure = self._design_structure(features)
        self.add_log(f"设计了 {len(structure)} 个文件")

        # 步骤 3: 生成代码
        self.add_thought(
            step=3,
            thought="生成代码文件",
            action=f"创建 {len(structure)} 个文件"
        )

        artifacts = []
        for file_info in structure:
            artifact = Artifact(
                type="code",
                path=file_info["path"],
                content=file_info["content"],
                metadata=file_info["metadata"]
            )
            artifacts.append(artifact)
            self.add_log(f"生成: {file_info['path']}")

        self.set_metric("files_count", len(artifacts))
        self.set_metric("features_count", len(features))

        return artifacts

    def _extract_features(self, description: str) -> List[str]:
        """从描述中提取功能点"""
        features = []

        # 基于关键词识别
        keywords_map = {
            "API": "REST API 接口",
            "数据库": "数据库连接和操作",
            "用户": "用户管理",
            "日志": "日志记录",
            "配置": "配置管理"
        }

        for keyword, feature in keywords_map.items():
            if keyword.lower() in description.lower():
                features.append(feature)

        return features or ["基本功能"]

    def _design_structure(self, features: List[str]) -> List[Dict[str, Any]]:
        """设计项目结构"""
        structure = []

        # 1. 主文件
        main_content = '''#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
主入口文件
"""

import logging
from src.app import create_app

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def main():
    """主函数"""
    app = create_app()
    logger.info("应用启动")
    # 应用逻辑


if __name__ == "__main__":
    main()
'''
        structure.append({
            "path": "main.py",
            "content": main_content,
            "metadata": {"type": "entry", "lines": len(main_content.split('\\n'))}
        })

        # 2. 应用文件
        app_content = '''#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
应用模块
"""


def create_app():
    """创建应用实例"""
    # TODO: 实现应用初始化
    return None
'''
        structure.append({
            "path": "src/app.py",
            "content": app_content,
            "metadata": {"type": "module", "lines": len(app_content.split('\\n'))}
        })

        # 3. 配置文件
        config_content = '''# 配置文件
DEBUG = True
SECRET_KEY = "your-secret-key"
DATABASE_URL = "sqlite:///app.db"
'''
        structure.append({
            "path": "config.py",
            "content": config_content,
            "metadata": {"type": "config", "lines": len(config_content.split('\\n'))}
        })

        # 4. README
        readme_content = f'''# 项目名称

## 功能特性

{chr(10).join(f"- {f}" for f in features)}

## 快速开始

```bash
# 安装依赖
pip install -r requirements.txt

# 运行
python main.py
```

## 开发

...
'''
        structure.append({
            "path": "README.md",
            "content": readme_content,
            "metadata": {"type": "documentation", "format": "markdown"}
        })

        return structure
```

#### 3.2 测试 Agent

创建 `tests/test_code_generator_agent.py`:

```python
import pytest
from execution.code_generator_agent import CodeGeneratorAgent
from execution.models import AgentContext


@pytest.mark.asyncio
async def test_code_generator():
    """测试代码生成"""
    agent = CodeGeneratorAgent(agent_id="test-code-gen")

    context = AgentContext(
        task_id="test-1",
        step_id="step-1",
        project_root="/tmp/test",
        worktree_path=None
    )

    task_input = {
        "description": "开发一个用户管理API,包含数据库和日志功能",
        "tech_stack": ["Python", "FastAPI"]
    }

    result = await agent.execute(context, task_input)

    assert result.success is True
    assert len(result.artifacts) >= 3
    assert any(a.path == "main.py" for a in result.artifacts)
    assert any(a.path == "README.md" for a in result.artifacts)


@pytest.mark.asyncio
async def test_code_generator_planning():
    """测试规划功能"""
    agent = CodeGeneratorAgent(agent_id="test-code-gen-2")

    context = AgentContext(
        task_id="test-2",
        step_id="step-1",
        project_root="/tmp/test",
        worktree_path=None
    )

    # 规划
    steps = await agent.plan(context, {"description": "测试"})

    assert len(steps) == 3
    assert steps[0]["step_id"] == "analyze"
    assert steps[1]["step_id"] == "design"
    assert steps[2]["step_id"] == "generate"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
```

### 挑战任务

1. 支持多种编程语言(Python, JavaScript, Java)
2. 生成单元测试代码
3. 添加依赖管理文件(requirements.txt, package.json)

### 验收标准

- [ ] 生成完整的代码框架
- [ ] 规划步骤正确
- [ ] 功能点识别准确
- [ ] 测试通过

---

## 🔧 第 4 课: 重构 Agent (高级)

### 目标

创建一个 Agent,分析代码并提供重构建议。

### 实现代码

```python
#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
代码重构 Agent - 分析代码并提供重构建议
"""

import ast
from typing import List, Dict, Any, Set
from execution.base_agent import BaseAgent
from execution.models import (
    AgentCapability,
    AgentContext,
    Artifact
)


class RefactoringAgent(BaseAgent):
    """代码重构 Agent"""

    @property
    def name(self) -> str:
        return "代码重构 Agent"

    @classmethod
    def get_capabilities(cls) -> Set[AgentCapability]:
        return {
            AgentCapability.REFACTORING,
            AgentCapability.CODE_GENERATION
        }

    async def execute_impl(
        self,
        context: AgentContext,
        task_input: Dict[str, Any]
    ) -> List[Artifact]:
        """分析代码并生成重构报告"""
        source_code = task_input.get("source_code", "")
        filename = task_input.get("filename", "code.py")

        self.add_thought(
            step=1,
            thought=f"分析代码: {filename}",
            action=f"代码行数: {len(source_code.split(chr(10)))}"
        )

        # 分析代码
        issues = self._analyze_code(source_code)
        self.add_log(f"发现 {len(issues)} 个问题")

        # 生成建议
        suggestions = self._generate_suggestions(issues)
        self.add_log(f"生成 {len(suggestions)} 条建议")

        # 生成报告
        report = self._create_report(filename, issues, suggestions)

        artifact = Artifact(
            type="documentation",
            path=f"reports/{filename}_refactoring_report.md",
            content=report,
            metadata={
                "format": "markdown",
                "issues_count": len(issues),
                "suggestions_count": len(suggestions)
            }
        )

        self.set_metric("issues_count", len(issues))
        self.set_metric("suggestions_count", len(suggestions))

        return [artifact]

    def _analyze_code(self, source_code: str) -> List[Dict[str, Any]]:
        """分析代码问题"""
        issues = []

        try:
            tree = ast.parse(source_code)

            # 检查函数长度
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef):
                    if len(node.body) > 20:
                        issues.append({
                            "type": "complexity",
                            "severity": "warning",
                            "message": f"函数 {node.name} 过长 ({len(node.body)} 行)",
                            "line": node.lineno
                        })

                    # 检查参数数量
                    if len(node.args.args) > 5:
                        issues.append({
                            "type": "complexity",
                            "severity": "info",
                            "message": f"函数 {node.name} 参数过多 ({len(node.args.args)} 个)",
                            "line": node.lineno
                        })

        except SyntaxError as e:
            issues.append({
                "type": "syntax",
                "severity": "error",
                "message": f"语法错误: {str(e)}",
                "line": e.lineno
            })

        return issues

    def _generate_suggestions(self, issues: List[Dict[str, Any]]) -> List[str]:
        """生成重构建议"""
        suggestions = []

        for issue in issues:
            if issue["type"] == "complexity":
                if "过长" in issue["message"]:
                    suggestions.append("考虑将函数拆分为更小的函数")
                if "参数过多" in issue["message"]:
                    suggestions.append("考虑使用对象封装多个参数")

        if not suggestions:
            suggestions.append("代码质量良好,暂无重构建议")

        return suggestions

    def _create_report(
        self,
        filename: str,
        issues: List[Dict[str, Any]],
        suggestions: List[str]
    ) -> str:
        """创建重构报告"""
        report = f"""# 代码重构报告

**文件**: {filename}
**生成时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## 问题汇总

发现 {len(issues)} 个问题:

"""

        for i, issue in enumerate(issues, 1):
            severity_emoji = {
                "error": "❌",
                "warning": "⚠️",
                "info": "ℹ️"
            }.get(issue["severity"], "•")

            report += f"{i}. {severity_emoji} **{issue['type']}**: {issue['message']} (行 {issue['line']})\\n\\n"

        report += "## 重构建议\\n\\n"
        for i, suggestion in enumerate(suggestions, 1):
            report += f"{i}. {suggestion}\\n"

        return report
```

### 挑战任务

1. 实现代码自动重构功能
2. 添加性能优化建议
3. 生成重构前后的对比报告

---

## 🎓 第 5 课: 组合 Agent (专家)

### 目标

创建一个组合 Agent,协调多个子 Agent 完成复杂任务。

### 实现代码

```python
#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
组合 Agent - 协调多个子 Agent 完成复杂任务
"""

import asyncio
from typing import List, Dict, Any, Set
from execution.base_agent import BaseAgent
from execution.models import (
    AgentCapability,
    AgentContext,
    Artifact
)
from orchestration.agent_factory import AgentFactory


class CompositeAgent(BaseAgent):
    """组合 Agent - 协调其他 Agent"""

    @property
    def name(self) -> str:
        return "组合 Agent"

    @classmethod
    def get_capabilities(cls) -> Set[AgentCapability]:
        return {
            AgentCapability.CODE_GENERATION,
            AgentCapability.DOCUMENTATION,
            AgentCapability.TESTING
        }

    async def plan(
        self,
        context: AgentContext,
        task_input: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """规划任务分解"""
        self.add_step("coordinate", "协调子 Agent", "任务结果")

        return self.steps

    async def execute_impl(
        self,
        context: AgentContext,
        task_input: Dict[str, Any]
    ) -> List[Artifact]:
        """协调子 Agent 执行任务"""
        description = task_input.get("description", "")
        tech_stack = task_input.get("tech_stack", ["Python"])

        self.add_thought(
            step=1,
            thought=f"分析任务: {description}",
            action="分解为子任务"
        )

        # 创建子 Agent
        code_agent = AgentFactory.create_agent(
            AgentType.BACKEND_DEV,
            agent_id=f"{self.agent_id}-code"
        )

        doc_agent = AgentFactory.create_agent(
            AgentType.TECHNICAL_WRITING,
            agent_id=f"{self.agent_id}-doc"
        )

        test_agent = AgentFactory.create_agent(
            AgentType.QA_ENGINEERING,
            agent_id=f"{self.agent_id}-test"
        )

        self.add_log("创建了 3 个子 Agent")

        # 并发执行子 Agent
        self.add_thought(
            step=2,
            thought="并发执行子 Agent",
            action="等待所有子任务完成"
        )

        results = await asyncio.gather(
            code_agent.execute(context, {
                "description": description,
                "tech_stack": tech_stack
            }),
            doc_agent.execute(context, {
                "title": description,
                "description": f"基于 {tech_stack} 的项目",
                "features": ["功能1", "功能2"]
            }),
            test_agent.execute(context, {
                "description": description,
                "tech_stack": tech_stack
            }),
            return_exceptions=True
        )

        # 合并结果
        all_artifacts = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                self.add_log(f"子任务 {i+1} 失败: {result}", level="error")
            elif result.success:
                all_artifacts.extend(result.artifacts)
                self.add_log(f"子任务 {i+1} 完成: {len(result.artifacts)} 个工件")
            else:
                self.add_log(f"子任务 {i+1} 失败: {result.error}", level="error")

        self.add_thought(
            step=3,
            thought="合并所有子任务结果",
            action=f"总共 {len(all_artifacts)} 个工件"
        )

        self.set_metric("subtasks_total", 3)
        self.set_metric("subtasks_success", sum(1 for r in results if not isinstance(r, Exception) and r.success))
        self.set_metric("total_artifacts", len(all_artifacts))

        return all_artifacts
```

### 测试代码

```python
@pytest.mark.asyncio
async def test_composite_agent():
    """测试组合 Agent"""
    agent = CompositeAgent(agent_id="test-composite")

    context = AgentContext(
        task_id="test-1",
        step_id="step-1",
        project_root="/tmp/test",
        worktree_path=None
    )

    task_input = {
        "description": "开发用户管理API",
        "tech_stack": ["Python", "FastAPI"]
    }

    result = await agent.execute(context, task_input)

    assert result.success is True
    assert len(result.artifacts) > 0
    assert result.metrics["subtasks_total"] == 3
```

### 挑战任务

1. 实现动态子 Agent 创建(根据任务需求)
2. 添加子任务依赖管理(串行执行某些任务)
3. 实现错误恢复机制(子任务失败时的处理)

---

## 📚 附录

### 常见问题

**Q: 如何调试 Agent?**

A: 使用日志记录和思考过程:

```python
self.add_log("调试信息")
self.add_thought(step=1, thought="思考过程", action="执行动作")
```

**Q: 如何处理长时间运行的任务?**

A: 使用异步操作和进度报告:

```python
async def execute_impl(self, context, task_input):
    for i, item in enumerate(items):
        # 处理 item
        self.add_log(f"进度: {i+1}/{len(items)}")
```

**Q: 如何优化 Agent 性能?**

A: 使用并发执行:

```python
results = await asyncio.gather(
    self._task1(),
    self._task2(),
    self._task3()
)
```

### 下一步

完成本教程后,你可以:
1. 阅读完整的 [Agent 开发指南](AGENT_DEVELOPMENT_GUIDE.md)
2. 查看 [API 参考](AGENT_API_REFERENCE.md)
3. 浏览 [Agent 模板](AGENT_TEMPLATES.md)
4. 为 SuperAgent 贡献你的 Agent

---

**恭喜你完成了交互式教程!** 🎉

你现在已经是 SuperAgent Agent 开发专家了!

**文档版本**: v1.0
**最后更新**: 2026-01-14
**维护者**: SuperAgent v3.2+ 开发团队
