#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
n8n 工作流执行器

实现 n8n 工作流自动化功能,用于生成、查询和管理 n8n 工作流。
"""

import json
import logging
import time
from typing import Any, Dict, List, Optional

from core.executor import Executor, Task, ExecutionResult, TaskStatus

from .n8n_knowledge_base import N8nKnowledgeBase, NodeInfo, WorkflowTemplate

logger = logging.getLogger(__name__)


class N8nExecutor(Executor):
    """
    n8n 工作流执行器

    用于:
    - 根据需求生成 n8n 工作流
    - 应用工作流模板
    - 查询节点信息
    - 验证工作流连接

    Example:
        >>> executor = N8nExecutor()
        >>> result = executor.execute(Task(
        ...     task_type="n8n_workflow",
        ...     description="创建 AI 聊天机器人",
        ...     context={"requirements": "需要支持微信接入"}
        ... ))
        >>> print(result.content)  # n8n 工作流 JSON
    """

    # 默认 n8n skill 路径
    DEFAULT_SKILL_PATH = r"C:\Users\Administrator\.claude\skills\n8n-skills"

    def __init__(
        self,
        name: str = "N8nExecutor",
        skill_path: str = None,
        auto_load: bool = True
    ):
        """
        初始化 n8n 执行器

        Args:
            name: 执行器名称
            skill_path: n8n skill 目录路径 (可选,使用默认路径)
            auto_load: 是否自动加载知识库
        """
        super().__init__(name)
        self.skill_path = skill_path or self.DEFAULT_SKILL_PATH
        self.knowledge_base = N8nKnowledgeBase(self.skill_path)

        if auto_load:
            self.knowledge_base.load_all()

        # 工作流生成配置
        self.default_position_step = 250  # 节点默认水平间距
        self.default_position_offset = 300  # 节点默认垂直间距

    def get_supported_types(self) -> List[str]:
        """
        获取支持的任务类型

        Returns:
            List[str]: 支持的任务类型列表
        """
        return [
            "n8n_workflow",      # 生成工作流
            "n8n_template",      # 应用模板
            "n8n_node_query",    # 查询节点
            "n8n_validate",      # 验证工作流
        ]

    def execute(self, task: Task) -> ExecutionResult:
        """
        执行 n8n 工作流任务

        Args:
            task: n8n 任务
                - task_type: 任务类型 (n8n_workflow/n8n_template/n8n_node_query/n8n_validate)
                - description: 任务描述/需求
                - context: 额外上下文
                - requirements: 任务要求列表

        Returns:
            ExecutionResult: 执行结果
        """
        start_time = time.time()

        try:
            if not self.validate_task(task):
                return ExecutionResult(
                    success=False,
                    content=None,
                    status=TaskStatus.FAILED,
                    error="Invalid task",
                    execution_time=time.time() - start_time
                )

            task_type = task.task_type

            if task_type == "n8n_workflow":
                return self._generate_workflow(task, start_time)
            elif task_type == "n8n_template":
                return self._apply_template(task, start_time)
            elif task_type == "n8n_node_query":
                return self._query_nodes(task, start_time)
            elif task_type == "n8n_validate":
                return self._validate_workflow(task, start_time)
            else:
                return ExecutionResult(
                    success=False,
                    content=None,
                    status=TaskStatus.FAILED,
                    error=f"Unknown task type: {task_type}",
                    execution_time=time.time() - start_time
                )

        except Exception as e:
            logger.error(f"N8n execution failed: {e}", exc_info=True)
            return ExecutionResult(
                success=False,
                content=None,
                status=TaskStatus.FAILED,
                error=str(e),
                execution_time=time.time() - start_time
            )

    def _generate_workflow(self, task: Task, start_time: float) -> ExecutionResult:
        """
        根据需求生成 n8n 工作流

        Args:
            task: 任务
            start_time: 开始时间

        Returns:
            ExecutionResult: 包含工作流 JSON
        """
        # 提取需求参数
        requirements = task.context.get("requirements", task.description)
        trigger_type = task.context.get("trigger", "webhook")
        output_type = task.context.get("output", "http")
        use_ai = task.context.get("use_ai", False)
        custom_nodes = task.context.get("nodes", [])

        logger.info(f"Generating n8n workflow: trigger={trigger_type}, output={output_type}, ai={use_ai}")

        # 1. 分析需求并选择节点
        node_requirements = {
            "trigger": trigger_type,
            "output": output_type,
            "ai": use_ai
        }
        recommended_nodes = self.knowledge_base.search_nodes_for_workflow(node_requirements)

        # 2. 构建工作流结构
        workflow = self._build_workflow(
            requirements=requirements,
            trigger_type=trigger_type,
            output_type=output_type,
            use_ai=use_ai,
            recommended_nodes=recommended_nodes,
            custom_nodes=custom_nodes,
            task=task
        )

        # 3. 验证工作流
        validation = self._validate_workflow_json(workflow)

        execution_time = time.time() - start_time

        return ExecutionResult(
            success=True,
            content={
                "workflow": workflow,
                "nodes_used": len(workflow.get("nodes", [])),
                "connections_used": len(workflow.get("connections", {})),
                "validation": validation
            },
            status=TaskStatus.COMPLETED,
            metadata={
                "task_description": task.description,
                "trigger_type": trigger_type,
                "output_type": output_type,
                "use_ai": use_ai,
                "recommended_nodes": [n.node_type for n in recommended_nodes[:5]]
            },
            execution_time=execution_time
        )

    def _build_workflow(
        self,
        requirements: str,
        trigger_type: str,
        output_type: str,
        use_ai: bool,
        recommended_nodes: List[NodeInfo],
        custom_nodes: List[Dict],
        task: Task
    ) -> Dict:
        """
        构建 n8n 工作流 JSON

        Args:
            requirements: 需求描述
            trigger_type: 触发器类型
            output_type: 输出类型
            use_ai: 是否使用 AI
            recommended_nodes: 推荐的节点列表
            custom_nodes: 自定义节点
            task: 原始任务

        Returns:
            Dict: n8n 工作流 JSON
        """
        nodes = []
        connections = {}
        position_y = 0

        # 1. 添加触发器
        trigger_node = self._create_trigger_node(trigger_type, position_y)
        if trigger_node:
            nodes.append(trigger_node)
            connections = {"main": [[]]}  # 初始化连接
            position_y += self.default_position_offset

        # 2. 添加处理节点
        if use_ai:
            ai_node = self._create_ai_node(position_y)
            if ai_node:
                nodes.append(ai_node)
                self._add_connection(connections, trigger_node, ai_node)
                position_y += self.default_position_offset

        # 3. 添加输出节点
        output_node = self._create_output_node(output_type, position_y)
        if output_node:
            nodes.append(output_node)
            last_node = nodes[-2] if len(nodes) >= 2 else trigger_node
            if last_node:
                self._add_connection(connections, last_node, output_node)

        # 4. 添加自定义节点
        for i, custom_node in enumerate(custom_nodes):
            node = self._create_custom_node(custom_node, position_y + i * self.default_position_offset)
            if node:
                nodes.append(node)

        # 构建工作流 JSON
        workflow = {
            "meta": {
                "instanceId": f"n8n-auto-{int(time.time())}"
            },
            "name": task.description[:50] if task.description else "Auto-generated Workflow",
            "nodes": nodes,
            "connections": connections,
            "settings": {
                "executionOrder": "v1"
            }
        }

        return workflow

    def _create_trigger_node(self, trigger_type: str, position_y: int) -> Optional[Dict]:
        """创建触发器节点"""
        trigger_map = {
            "webhook": {
                "type": "nodes-base.webhook",
                "name": "Webhook",
                "parameters": {
                    "httpMethod": {"value": "POST"},
                    "path": {"value": "webhook"},
                    "options": {}
                }
            },
            "schedule": {
                "type": "nodes-base.scheduleTrigger",
                "name": "Schedule",
                "parameters": {
                    "rule": {"value": {"interval": [{"field": "minutes", "value": 5}]}}
                }
            },
            "manual": {
                "type": "nodes-base.manualTrigger",
                "name": "Manual Trigger",
                "parameters": {}
            },
            "email": {
                "type": "nodes-base.emailReadImap",
                "name": "Email Trigger",
                "parameters": {}
            }
        }

        if trigger_type not in trigger_map:
            # 使用 webhook 作为默认
            trigger_type = "webhook"

        trigger_info = trigger_map[trigger_type]
        return {
            "name": trigger_info["name"],
            "type": trigger_info["type"],
            "typeVersion": 1,
            "position": [250, position_y],
            "parameters": trigger_info.get("parameters", {})
        }

    def _create_ai_node(self, position_y: int) -> Optional[Dict]:
        """创建 AI 节点"""
        # 尝试查找 OpenAI 节点
        openai_nodes = self.knowledge_base.find_nodes_by_keyword("OpenAI")
        if openai_nodes:
            node_type = openai_nodes[0].node_type
        else:
            node_type = "nodes-base.openAi"

        return {
            "name": "AI Agent",
            "type": node_type,
            "typeVersion": 1.3,
            "position": [250, position_y],
            "parameters": {
                "operation": "textCompletion",
                "model": {"value": "gpt-4"},
                "prompt": {"value": "={{ $json.input }}"},
                "options": {}
            }
        }

    def _create_output_node(self, output_type: str, position_y: int) -> Optional[Dict]:
        """创建输出节点"""
        output_map = {
            "http": {
                "type": "nodes-base.httpRequest",
                "name": "HTTP Request",
                "parameters": {
                    "method": {"value": "POST"},
                    "url": {"value": "https://example.com/api"},
                    "options": {},
                    "sendHeaders": {"value": True},
                    "headerParameters": {
                        "value": {
                            "parameters": [
                                {"name": "Content-Type", "value": "application/json"}
                            ]
                        }
                    },
                    "sendBody": {"value": True},
                    "bodyParameters": {
                        "value": {
                            "parameters": [
                                {"name": "result", "value": "={{ $json }}"}
                            ]
                        }
                    }
                }
            },
            "slack": {
                "type": "nodes-base.slack",
                "name": "Slack",
                "parameters": {
                    "channel": {"value": "#general"},
                    "text": {"value": "={{ $json }}"},
                    "options": {}
                }
            },
            "email": {
                "type": "nodes-base.email",
                "name": "Send Email",
                "parameters": {
                    "toEmail": {"value": "recipient@example.com"},
                    "subject": {"value": "Workflow Result"},
                    "text": {"value": "={{ $json }}"}
                }
            },
            "database": {
                "type": "nodes-base.mySql",
                "name": "Save to Database",
                "parameters": {
                    "operation": "insert",
                    "table": {"value": "results"},
                    "columns": {"value": {"parameters": []}}
                }
            }
        }

        if output_type not in output_map:
            output_type = "http"

        output_info = output_map[output_type]
        return {
            "name": output_info["name"],
            "type": output_info["type"],
            "typeVersion": 1,
            "position": [250, position_y],
            "parameters": output_info.get("parameters", {})
        }

    def _create_custom_node(self, config: Dict, position_y: int) -> Optional[Dict]:
        """创建自定义节点"""
        if not config.get("type"):
            return None

        return {
            "name": config.get("name", "Custom Node"),
            "type": config["type"],
            "typeVersion": config.get("version", 1),
            "position": [250, position_y],
            "parameters": config.get("parameters", {})
        }

    def _add_connection(self, connections: Dict, source: Dict, target: Dict) -> None:
        """添加节点连接"""
        source_name = source["name"]

        if "main" not in connections:
            connections["main"] = [[]]

        # 确保目标节点有连接记录
        if target["name"] not in connections:
            connections[target["name"]] = {"main": [[]]}

        # 添加连接
        for conn_type in connections:
            if conn_type != target["name"]:
                continue
            if "main" in connections[conn_type]:
                if len(connections[conn_type]["main"]) == 0:
                    connections[conn_type]["main"].append([])

    def _apply_template(self, task: Task, start_time: float) -> ExecutionResult:
        """
        应用工作流模板

        Args:
            task: 任务
            start_time: 开始时间

        Returns:
            ExecutionResult: 包含配置好的模板
        """
        # 提取模板 ID 和参数
        template_id = task.context.get("template_id", "")
        replacements = task.context.get("replacements", {})

        logger.info(f"Applying template: {template_id}")

        # 查找模板
        if template_id:
            template = self.knowledge_base.find_template(template_id)
        else:
            # 根据关键词查找
            keywords = task.context.get("keywords", task.description.split())
            templates = self.knowledge_base.find_template_by_keywords(keywords)
            template = templates[0] if templates else None

        if not template:
            return ExecutionResult(
                success=False,
                content=None,
                status=TaskStatus.FAILED,
                error=f"Template not found: {template_id}",
                execution_time=time.time() - start_time
            )

        # 应用替换
        workflow = template.workflow_json
        if replacements:
            workflow = self._apply_replacements(workflow, replacements)

        execution_time = time.time() - start_time

        return ExecutionResult(
            success=True,
            content={
                "template": {
                    "id": template.template_id,
                    "name": template.name,
                    "category": template.category,
                    "description": template.description
                },
                "workflow": workflow
            },
            status=TaskStatus.COMPLETED,
            metadata={
                "template_id": template.template_id,
                "node_count": template.node_count,
                "views": template.views
            },
            execution_time=execution_time
        )

    def _apply_replacements(self, workflow: Dict, replacements: Dict) -> Dict:
        """应用占位符替换"""
        # 深度替换工作流中的占位符
        workflow_str = json.dumps(workflow)

        for key, value in replacements.items():
            placeholder = f"{{{{ {key} }}}}"
            workflow_str = workflow_str.replace(placeholder, str(value))

        try:
            return json.loads(workflow_str)
        except json.JSONDecodeError:
            return workflow

    def _query_nodes(self, task: Task, start_time: float) -> ExecutionResult:
        """
        查询节点信息

        Args:
            task: 任务
            start_time: 开始时间

        Returns:
            ExecutionResult: 包含节点信息
        """
        query = task.context.get("query", "")
        query_type = task.context.get("type", "keyword")  # keyword/category/node_type

        logger.info(f"Querying nodes: query={query}, type={query_type}")

        nodes = []

        if query_type == "keyword":
            nodes = self.knowledge_base.find_nodes_by_keyword(query)
        elif query_type == "category":
            nodes = self.knowledge_base.find_nodes_by_category(query)
        elif query_type == "node_type":
            node = self.knowledge_base.get_node(query)
            if node:
                nodes = [node]
        else:
            # 默认按关键词搜索
            nodes = self.knowledge_base.find_nodes_by_keyword(query)

        # 转换为可序列化格式
        nodes_data = []
        for node in nodes:
            nodes_data.append({
                "node_type": node.node_type,
                "name": node.name,
                "category": node.category,
                "package": node.package,
                "description": node.description,
                "properties_count": len(node.properties),
                "input_types": node.input_types,
                "output_types": node.output_types
            })

        execution_time = time.time() - start_time

        return ExecutionResult(
            success=True,
            content={
                "query": query,
                "query_type": query_type,
                "count": len(nodes_data),
                "nodes": nodes_data
            },
            status=TaskStatus.COMPLETED,
            metadata={"query": query},
            execution_time=execution_time
        )

    def _validate_workflow(self, task: Task, start_time: float) -> ExecutionResult:
        """
        验证工作流

        Args:
            task: 任务
            start_time: 开始时间

        Returns:
            ExecutionResult: 包含验证结果
        """
        workflow = task.context.get("workflow", {})
        context = task.context.get("context", {})

        if not workflow:
            return ExecutionResult(
                success=False,
                content=None,
                status=TaskStatus.FAILED,
                error="No workflow provided",
                execution_time=time.time() - start_time
            )

        validation = self._validate_workflow_json(workflow)

        execution_time = time.time() - start_time

        return ExecutionResult(
            success=validation["valid"],
            content=validation,
            status=TaskStatus.COMPLETED,
            metadata={"node_count": len(workflow.get("nodes", []))},
            execution_time=execution_time
        )

    def _validate_workflow_json(self, workflow: Dict) -> Dict:
        """
        验证工作流 JSON

        Args:
            workflow: 工作流 JSON

        Returns:
            Dict: 验证结果
        """
        errors = []
        warnings = []
        checks = {
            "has_nodes": False,
            "has_connections": False,
            "has_trigger": False,
            "all_nodes_valid": True,
            "all_connections_valid": True
        }

        # 检查节点
        nodes = workflow.get("nodes", [])
        if not nodes:
            errors.append("Workflow has no nodes")
        else:
            checks["has_nodes"] = True
            checks["has_trigger"] = any(
                n.get("type") == "nodes-base.webhook" or
                n.get("type", "").startswith("trigger") or
                n.get("name", "").lower().find("trigger") >= 0
                for n in nodes
            )

            for node in nodes:
                if not node.get("type"):
                    errors.append(f"Node '{node.get('name')}' has no type")
                    checks["all_nodes_valid"] = False

                if not node.get("position"):
                    warnings.append(f"Node '{node.get('name')}' has no position")

        # 检查连接
        connections = workflow.get("connections", {})
        if not connections:
            warnings.append("Workflow has no connections")
        else:
            checks["has_connections"] = True

            for node_name, conn_data in connections.items():
                if isinstance(conn_data, dict):
                    for conn_type, conn_list in conn_data.items():
                        if conn_list and len(conn_list) > 0:
                            for conn in conn_list:
                                if conn and len(conn) > 0:
                                    # 检查连接目标是否存在
                                    for target in conn:
                                        if target and isinstance(target, dict):
                                            if not target.get("node"):
                                                errors.append(f"Connection has no target node")
                                                checks["all_connections_valid"] = False

        valid = len(errors) == 0

        return {
            "valid": valid,
            "errors": errors,
            "warnings": warnings,
            "checks": checks,
            "summary": {
                "node_count": len(nodes),
                "connection_count": sum(
                    len(v) for v in connections.values()
                    if isinstance(v, dict)
                ) if connections else 0
            }
        }

    def __repr__(self) -> str:
        return (
            f"N8nExecutor("
            f"name={self.name}, "
            f"skill_path={self.skill_path}, "
            f"nodes={len(self.knowledge_base.nodes)}, "
            f"templates={len(self.knowledge_base.templates)})"
        )
