#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
n8n 知识库加载器

负责加载和解析 n8n skills 知识库,提供节点信息、工作流模板和兼容性查询。
"""

import json
import logging
import os
from pathlib import Path
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


@dataclass
class NodeInfo:
    """节点信息"""
    node_type: str           # 节点类型 (如 "nodes-base.httpRequest")
    name: str                # 节点名称 (如 "HTTP Request")
    category: str            # 分类 (transform/input/output/trigger)
    package: str             # 所属包
    description: str         # 描述
    properties: List[Dict] = field(default_factory=list)  # 属性列表
    input_types: List[str] = field(default_factory=list)  # 输入类型
    output_types: List[str] = field(default_factory=list)  # 输出类型
    can_connect_to: List[str] = field(default_factory=list)  # 可连接的节点类型
    version: int = 1         # 版本


@dataclass
class WorkflowTemplate:
    """工作流模板"""
    template_id: str         # 模板ID
    name: str                # 模板名称
    category: str            # 分类 (ai-chatbots/social-media/data-processing/communication)
    description: str         # 描述
    views: int               # 查看次数
    node_count: int          # 节点数量
    connection_count: int    # 连接数量
    key_nodes: List[Dict] = field(default_factory=list)  # 关键节点
    workflow_json: Dict = field(default_factory=dict)    # 完整工作流JSON


@dataclass
class CompatibilityInfo:
    """兼容性信息"""
    source_type: str
    target_type: str
    score: int  # 0-100
    level: str  # "high"/"medium"/"low"/"incompatible"


class N8nKnowledgeBase:
    """
    n8n 知识库加载器

    加载 n8n skills 知识库,提供:
    - 节点信息查询
    - 工作流模板查询
    - 节点兼容性查询
    """

    # 默认 n8n skill 路径
    DEFAULT_SKILL_PATH = r"C:\Users\Administrator\.claude\skills\n8n-skills"

    # 节点分类目录
    CATEGORY_DIRS = {
        "transform": "transform",
        "input": "input",
        "output": "output",
        "trigger": "trigger",
        "organization": "organization",
        "misc": "misc"
    }

    def __init__(self, skill_path: str = None):
        """
        初始化知识库加载器

        Args:
            skill_path: n8n skill 目录路径 (可选,使用默认路径)
        """
        self.skill_path = Path(skill_path) if skill_path else Path(self.DEFAULT_SKILL_PATH)
        self.resources_path = self.skill_path / "resources"

        # 知识库数据
        self.nodes: Dict[str, NodeInfo] = {}  # node_type -> NodeInfo
        self.templates: List[WorkflowTemplate] = []  # 工作流模板列表
        self.compatibility: Dict[str, Dict[str, CompatibilityInfo]] = {}  # 兼容性矩阵

        # 加载状态
        self._loaded = False

    def load_all(self) -> bool:
        """
        加载所有知识库数据

        Returns:
            bool: 是否成功加载
        """
        try:
            logger.info(f"Loading n8n knowledge base from: {self.skill_path}")

            if not self.skill_path.exists():
                logger.warning(f"n8n skill path not found: {self.skill_path}")
                return False

            # 加载各部分数据
            self._load_nodes()
            self._load_templates()
            self._load_compatibility()

            self._loaded = True
            logger.info(
                f"n8n knowledge base loaded: "
                f"{len(self.nodes)} nodes, "
                f"{len(self.templates)} templates"
            )
            return True

        except Exception as e:
            logger.error(f"Failed to load n8n knowledge base: {e}", exc_info=True)
            return False

    def _load_nodes(self) -> None:
        """加载所有节点信息"""
        # 高优先级节点 (独立文件)
        priority_files = [
            ("transform", "transform/nodes-base.code.md"),
            ("transform", "transform/nodes-base.function.md"),
            ("transform", "transform/nodes-base.if.md"),
            ("transform", "transform/nodes-base.merge.md"),
            ("transform", "transform/nodes-base.gmail.md"),
            ("transform", "transform/nodes-base.openAi.md"),
            ("input", "input/nodes-base.airtable.md"),
            ("input", "input/nodes-base.github.md"),
            ("input", "input/nodes-base.googleSheets.md"),
            ("input", "input/nodes-base.mySql.md"),
            ("output", "output/nodes-base.discord.md"),
            ("output", "output/nodes-base.httpRequest.md"),
            ("output", "output/nodes-base.notion.md"),
            ("output", "output/nodes-base.slack.md"),
            ("trigger", "trigger/nodes-base.webhook.md"),
            ("trigger", "trigger/nodes-base.airtableTrigger.md"),
        ]

        for category, relative_path in priority_files:
            self._parse_node_file(category, relative_path)

        # 加载合并的低优先级节点
        merged_files = [
            ("transform", "transform/transform-merged-1.md"),
            ("transform", "transform/transform-merged-2.md"),
            ("transform", "transform/transform-merged-3.md"),
            ("input", "input/input-merged.md"),
            ("output", "output/output-merged.md"),
            ("trigger", "trigger/trigger-merged.md"),
        ]

        for category, relative_path in merged_files:
            self._parse_merged_node_file(category, relative_path)

        logger.debug(f"Loaded {len(self.nodes)} nodes")

    def _parse_node_file(self, category: str, relative_path: str) -> None:
        """解析单个节点文件"""
        file_path = self.resources_path / relative_path
        if not file_path.exists():
            logger.warning(f"Node file not found: {file_path}")
            return

        try:
            content = file_path.read_text(encoding="utf-8")
            node_info = self._extract_node_from_content(content, category)
            if node_info:
                self.nodes[node_info.node_type] = node_info
        except Exception as e:
            logger.warning(f"Failed to parse node file {file_path}: {e}")

    def _parse_merged_node_file(self, category: str, relative_path: str) -> None:
        """解析合并的节点文件 (包含多个节点)"""
        file_path = self.resources_path / relative_path
        if not file_path.exists():
            logger.warning(f"Merged node file not found: {file_path}")
            return

        try:
            content = file_path.read_text(encoding="utf-8")
            # 合并文件包含多个节点,按标题分隔
            nodes = self._extract_nodes_from_merged_content(content, category)
            for node in nodes:
                self.nodes[node.node_type] = node
        except Exception as e:
            logger.warning(f"Failed to parse merged node file {file_path}: {e}")

    def _extract_node_from_content(self, content: str, category: str) -> Optional[NodeInfo]:
        """从节点文档内容中提取节点信息"""
        # 提取节点类型
        node_type_match = content.split("## Basic Information")[0].strip()
        if not node_type_match.startswith("#"):
            return None

        name = node_type_match.lstrip("#").strip()

        # 提取节点类型
        node_type = ""
        if "Node Type:" in content:
            for line in content.split("\n"):
                if "Node Type:" in line:
                    node_type = line.split("Node Type:")[1].strip().strip("`")
                    break

        # 提取描述
        description = ""
        if "## Description" in content:
            desc_section = content.split("## Description")[1].split("##")[0].strip()
            description = desc_section.split("\n\n")[0].strip()

        # 提取属性
        properties = []
        if "## Core Properties" in content:
            props_section = content.split("## Core Properties")[1].split("##")[0]
            # 解析属性表格
            properties = self._parse_properties_table(props_section)

        # 提取连接信息
        input_types = []
        output_types = []
        if "## Connection Guide" in content:
            conn_section = content.split("## Connection Guide")[1].split("##")[0]
            input_types, output_types = self._parse_connection_guide(conn_section)

        return NodeInfo(
            node_type=node_type or f"nodes-base.{name.lower().replace(' ', '')}",
            name=name,
            category=category,
            package="n8n-nodes-base",
            description=description,
            properties=properties,
            input_types=input_types,
            output_types=output_types,
            can_connect_to=[]
        )

    def _extract_nodes_from_merged_content(self, content: str, category: str) -> List[NodeInfo]:
        """从合并内容中提取多个节点"""
        nodes = []
        lines = content.split("\n")
        current_node = None
        current_content = []

        for line in lines:
            # 检测新节点标题
            if line.startswith("## "):
                if current_node:
                    # 保存前一个节点
                    node_info = self._extract_node_from_content(
                        "\n".join(current_content), category
                    )
                    if node_info:
                        nodes.append(node_info)
                current_node = line.replace("## ", "").strip()
                current_content = [line]
            else:
                if current_node:
                    current_content.append(line)

        # 保存最后一个节点
        if current_node and current_content:
            node_info = self._extract_node_from_content("\n".join(current_content), category)
            if node_info:
                nodes.append(node_info)

        return nodes

    def _parse_properties_table(self, section: str) -> List[Dict]:
        """解析属性表格"""
        properties = []
        lines = section.split("\n")

        for line in lines:
            if "|" in line and "Property Name" not in line:
                parts = [p.strip() for p in line.split("|")[1:-1]]
                if len(parts) >= 5:
                    properties.append({
                        "name": parts[0],
                        "type": parts[1],
                        "required": "Yes" in parts[2],
                        "default": parts[3] if len(parts) > 3 else "",
                        "description": parts[4] if len(parts) > 4 else ""
                    })

        return properties

    def _parse_connection_guide(self, section: str) -> tuple:
        """解析连接指南"""
        input_types = []
        output_types = []

        lines = section.split("\n")
        in_input_section = False
        in_output_section = False

        for line in lines:
            if "Input Types:" in line:
                in_input_section = True
                in_output_section = False
                continue
            if "Output Types:" in line:
                in_input_section = False
                in_output_section = True
                continue
            if "Can Receive From" in line or "Can Connect To" in line:
                in_input_section = False
                in_output_section = False
                continue
            if line.startswith("## "):
                in_input_section = False
                in_output_section = False

            if in_input_section and "-" in line:
                input_types.append(line.strip().strip("-").strip())
            if in_output_section and "-" in line:
                output_types.append(line.strip().strip("-").strip())

        return input_types, output_types

    def _load_templates(self) -> None:
        """加载工作流模板"""
        templates_dir = self.resources_path / "templates"

        if not templates_dir.exists():
            logger.warning(f"Templates directory not found: {templates_dir}")
            return

        # 加载各分类模板
        category_dirs = ["ai-chatbots", "social-media", "data-processing", "communication"]

        for category in category_dirs:
            category_path = templates_dir / category
            if category_path.exists():
                self._parse_template_dir(category_path, category)

        logger.debug(f"Loaded {len(self.templates)} templates")

    def _parse_template_dir(self, path: Path, category: str) -> None:
        """解析模板目录"""
        for md_file in path.glob("*.md"):
            if md_file.name == "README.md":
                continue

            template = self._parse_template_file(md_file, category)
            if template:
                self.templates.append(template)

    def _parse_template_file(self, file_path: Path, category: str) -> Optional[WorkflowTemplate]:
        """解析单个模板文件"""
        try:
            content = file_path.read_text(encoding="utf-8")

            # 提取模板名称
            name = file_path.stem
            if name.startswith("__"):
                name = name.split("-", 1)[1] if "-" in name else name

            # 从内容中提取信息
            description = ""
            views = 0
            node_count = 0
            connection_count = 0
            key_nodes = []
            workflow_json = {}

            lines = content.split("\n")
            in_key_nodes = False
            in_connections = False
            in_workflow_json = False
            workflow_lines = []

            for i, line in enumerate(lines):
                if line.startswith("> **Category**:"):
                    # category already set
                    pass
                elif line.startswith("> **Views**:"):
                    views_str = line.split("**Views**:")[1].strip().replace(",", "")
                    try:
                        views = int(views_str)
                    except ValueError:
                        views = 0
                elif "Node count:" in line:
                    node_str = line.split("Node count:")[1].strip()
                    try:
                        node_count = int(node_str)
                    except ValueError:
                        node_count = 0
                elif "Connection count:" in line:
                    conn_str = line.split("Connection count:")[1].strip()
                    try:
                        connection_count = int(conn_str)
                    except ValueError:
                        connection_count = 0
                elif "### Key Nodes" in line:
                    in_key_nodes = True
                    in_connections = False
                    continue
                elif "### Connections" in line:
                    in_key_nodes = False
                    in_connections = True
                    continue
                elif "## Complete Workflow JSON" in line:
                    in_key_nodes = False
                    in_connections = False
                    in_workflow_json = True
                    continue
                elif line.startswith("## "):
                    in_key_nodes = False
                    in_connections = False
                    in_workflow_json = False

                if in_key_nodes and line.startswith("| Node Name"):
                    continue
                if in_key_nodes and "| --- |" in line:
                    continue
                if in_key_nodes and "| " in line:
                    parts = [p.strip() for p in line.split("|")[1:-1]]
                    if len(parts) >= 3:
                        key_nodes.append({
                            "name": parts[0],
                            "type": parts[1],
                            "category": parts[2] if len(parts) > 2 else ""
                        })

                if in_workflow_json and line.startswith("```"):
                    if line == "```":
                        in_workflow_json = False
                        # 尝试解析 JSON
                        json_str = "\n".join(workflow_lines).strip()
                        if json_str:
                            try:
                                workflow_json = json.loads(json_str)
                            except json.JSONDecodeError:
                                pass
                    else:
                        workflow_lines.append(line)
                elif in_workflow_json:
                    workflow_lines.append(line)

            return WorkflowTemplate(
                template_id=name,
                name=name,
                category=category,
                description=description,
                views=views,
                node_count=node_count,
                connection_count=connection_count,
                key_nodes=key_nodes,
                workflow_json=workflow_json
            )

        except Exception as e:
            logger.warning(f"Failed to parse template file {file_path}: {e}")
            return None

    def _load_compatibility(self) -> None:
        """加载兼容性矩阵"""
        matrix_file = self.resources_path / "compatibility-matrix.md"

        if not matrix_file.exists():
            logger.warning(f"Compatibility matrix not found: {matrix_file}")
            return

        try:
            content = matrix_file.read_text(encoding="utf-8")
            # 解析兼容性矩阵
            self._parse_compatibility_matrix(content)
        except Exception as e:
            logger.warning(f"Failed to parse compatibility matrix: {e}")

    def _parse_compatibility_matrix(self, content: str) -> None:
        """解析兼容性矩阵"""
        lines = content.split("\n")

        source_types = []
        matrix = {}
        current_row = None

        for line in lines:
            if "| --- |" in line:
                continue

            if "| Source \\ Target" in line or "| 源节点" in line:
                continue

            if "| " in line:
                parts = [p.strip() for p in line.split("|")[1:-1]]

                if not current_row and len(parts) > 1:
                    # 第一行: 目标节点类型
                    for p in parts[1:]:
                        if p and p not in ["-", "图例"]:
                            source_types.append(p)
                elif len(parts) > 1 and parts[0] and parts[0] not in ["-", "图例"]:
                    # 数据行: 源节点类型 + 兼容性
                    source_type = parts[0]
                    current_row = source_type
                    for i, p in enumerate(parts[1:]):
                        if i < len(source_types) and p:
                            target_type = source_types[i]
                            score, level = self._parse_compatibility_level(p)
                            matrix[f"{source_type}|{target_type}"] = CompatibilityInfo(
                                source_type=source_type,
                                target_type=target_type,
                                score=score,
                                level=level
                            )

        self.compatibility = matrix

    def _parse_compatibility_level(self, symbol: str) -> tuple:
        """解析兼容性符号"""
        symbol = symbol.strip()
        if "++" in symbol:
            return 80, "high"
        elif "+" in symbol:
            return 60, "medium"
        elif "~" in symbol:
            return 40, "low"
        elif "X" in symbol or "×" in symbol:
            return 0, "incompatible"
        return 50, "medium"

    # 查询方法

    def find_nodes_by_category(self, category: str) -> List[NodeInfo]:
        """
        按类别查找节点

        Args:
            category: 节点类别 (transform/input/output/trigger)

        Returns:
            List[NodeInfo]: 匹配的节点列表
        """
        return [n for n in self.nodes.values() if n.category == category]

    def find_nodes_by_keyword(self, keyword: str) -> List[NodeInfo]:
        """
        按关键词查找节点

        Args:
            keyword: 关键词

        Returns:
            List[NodeInfo]: 匹配的节点列表
        """
        keyword_lower = keyword.lower()
        return [
            n for n in self.nodes.values()
            if keyword_lower in n.name.lower() or keyword_lower in n.node_type.lower()
        ]

    def get_node(self, node_type: str) -> Optional[NodeInfo]:
        """
        获取指定类型的节点信息

        Args:
            node_type: 节点类型

        Returns:
            Optional[NodeInfo]: 节点信息 (不存在则返回 None)
        """
        return self.nodes.get(node_type)

    def find_templates_by_category(self, category: str) -> List[WorkflowTemplate]:
        """
        按类别查找工作流模板

        Args:
            category: 模板类别

        Returns:
            List[WorkflowTemplate]: 匹配的模板列表
        """
        return [t for t in self.templates if t.category == category]

    def find_template(self, template_id: str) -> Optional[WorkflowTemplate]:
        """
        按 ID 查找工作流模板

        Args:
            template_id: 模板 ID

        Returns:
            Optional[WorkflowTemplate]: 模板信息 (不存在则返回 None)
        """
        for t in self.templates:
            if t.template_id == template_id or template_id in t.template_id:
                return t
        return None

    def find_template_by_keywords(self, keywords: List[str]) -> List[WorkflowTemplate]:
        """
        按关键词查找工作流模板

        Args:
            keywords: 关键词列表

        Returns:
            List[WorkflowTemplate]: 匹配的模板列表
        """
        results = []
        keywords_lower = [k.lower() for k in keywords]

        for t in self.templates:
            match_score = 0
            for kw in keywords_lower:
                if kw in t.category.lower() or kw in t.name.lower():
                    match_score += 1
            if match_score > 0:
                results.append((t, match_score))

        # 按匹配度排序
        results.sort(key=lambda x: x[1], reverse=True)
        return [t for t, _ in results]

    def get_compatibility(self, source_type: str, target_type: str) -> Optional[CompatibilityInfo]:
        """
        查询节点兼容性

        Args:
            source_type: 源节点类型
            target_type: 目标节点类型

        Returns:
            Optional[CompatibilityInfo]: 兼容性信息
        """
        key = f"{source_type}|{target_type}"
        return self.compatibility.get(key)

    def search_nodes_for_workflow(self, requirements: Dict[str, Any]) -> List[NodeInfo]:
        """
        根据工作流需求搜索合适的节点

        Args:
            requirements: 需求字典
                - trigger: 触发类型 (webhook/schedule/manual)
                - input: 输入源 (http/api/database/file)
                - processing: 处理类型 (transform/filter/condition)
                - output: 输出类型 (http/file/database/notification)
                - ai: 是否需要 AI (True/False)

        Returns:
            List[NodeInfo]: 推荐的节点列表
        """
        recommendations = []

        # 触发器
        if requirements.get("trigger"):
            trigger_nodes = self.find_nodes_by_category("trigger")
            for node in trigger_nodes:
                if requirements["trigger"] in node.name.lower():
                    recommendations.append(node)

        # 输入
        if requirements.get("input"):
            input_nodes = self.find_nodes_by_category("input")
            for node in input_nodes:
                if requirements["input"] in node.name.lower():
                    recommendations.append(node)

        # 输出
        if requirements.get("output"):
            output_nodes = self.find_nodes_by_category("output")
            for node in output_nodes:
                if requirements["output"] in node.name.lower():
                    recommendations.append(node)

        # AI 节点
        if requirements.get("ai"):
            ai_nodes = self.find_nodes_by_keyword("AI")
            ai_nodes.extend(self.find_nodes_by_keyword("OpenAI"))
            ai_nodes.extend(self.find_nodes_by_keyword("LangChain"))
            recommendations.extend(ai_nodes)

        return recommendations

    def __repr__(self) -> str:
        return (
            f"N8nKnowledgeBase("
            f"path={self.skill_path}, "
            f"nodes={len(self.nodes)}, "
            f"templates={len(self.templates)})"
        )
