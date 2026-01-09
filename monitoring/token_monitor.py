#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Token使用监控器

追踪和报告Token使用情况
"""

import json
import logging
import asyncio
import aiofiles
from typing import Dict, List, Any, Optional
from pathlib import Path
from dataclasses import dataclass, field, asdict
from datetime import datetime, timedelta
from collections import defaultdict
from common.monitoring import MetricsManager

logger = logging.getLogger(__name__)


@dataclass
class TokenUsageRecord:
    """Token使用记录"""
    timestamp: str
    agent_type: str
    task_id: str
    original_tokens: int
    compressed_tokens: int
    incremental_tokens: int
    files_processed: int
    files_incremental: int
    compression_method: str
    compression_ratio: float
    savings_ratio: float

    def to_dict(self) -> Dict:
        return asdict(self)


@dataclass
class TokenMonitorConfig:
    """Token监控配置"""
    enabled: bool = True
    log_file: str = ".superagent/token_usage.jsonl"  # 改为 jsonl 格式
    retention_days: int = 30
    track_compression_savings: bool = True
    track_incremental_savings: bool = True
    track_agent_usage: bool = True


class TokenMonitor:
    """Token使用监控器"""

    def __init__(
        self,
        project_root: Path = None,
        config: TokenMonitorConfig = None
    ):
        """初始化Token监控器

        Args:
            project_root: 项目根目录
            config: 配置
        """
        self.config = config or TokenMonitorConfig()
        self.project_root = Path(project_root) if project_root else Path.cwd()

        # 日志文件
        self.log_file = self.project_root / self.config.log_file
        self.log_file.parent.mkdir(parents=True, exist_ok=True)

        # 异步锁，确保写入顺序
        self._lock = asyncio.Lock()

        logger.info(f"Token监控器初始化完成: {self.log_file}")

    async def log_usage(
        self,
        agent_type: str,
        task_id: str,
        original_tokens: int,
        compressed_tokens: int = 0,
        incremental_tokens: int = 0,
        files_processed: int = 0,
        files_incremental: int = 0,
        compression_method: str = ""
    ) -> TokenUsageRecord:
        """记录Token使用情况 (异步版)

        Args:
            agent_type: Agent类型
            task_id: 任务ID
            original_tokens: 原始Token数
            compressed_tokens: 压缩后Token数
            incremental_tokens: 增量节省Token数
            files_processed: 处理的文件数
            files_incremental: 使用增量的文件数
            compression_method: 压缩方法

        Returns:
            TokenUsageRecord: 使用记录
        """
        if not self.config.enabled:
            return None

        # 计算压缩比和节省比
        if original_tokens > 0:
            compression_ratio = compressed_tokens / original_tokens
            savings_ratio = (original_tokens - compressed_tokens) / original_tokens
        else:
            compression_ratio = 0
            savings_ratio = 0

        record = TokenUsageRecord(
            timestamp=datetime.now().isoformat(),
            agent_type=agent_type,
            task_id=task_id,
            original_tokens=original_tokens,
            compressed_tokens=compressed_tokens,
            incremental_tokens=incremental_tokens,
            files_processed=files_processed,
            files_incremental=files_incremental,
            compression_method=compression_method,
            compression_ratio=compression_ratio,
            savings_ratio=savings_ratio
        )

        # 写入日志文件 (异步)
        await self._append_record(record)

        # 同时记录到 Prometheus 指标
        MetricsManager.record_token_usage(
            agent_type=agent_type,
            prompt=original_tokens,  # 这里简单映射，实际可能需要更细的分法
            completion=0
        )
        if original_tokens > compressed_tokens:
            MetricsManager.record_token_savings(
                agent_type=agent_type,
                savings=original_tokens - compressed_tokens,
                opt_type=compression_method or "compression"
            )

        logger.debug(
            f"Token使用记录: {agent_type}/{task_id}, "
            f"原始:{original_tokens}, 压缩:{compressed_tokens}, "
            f"节省:{savings_ratio*100:.1f}%"
        )

        return record

    async def _append_record(self, record: TokenUsageRecord):
        """追加记录到日志文件 (异步 JSONL)"""
        async with self._lock:
            try:
                async with aiofiles.open(self.log_file, 'a', encoding='utf-8') as f:
                    await f.write(json.dumps(record.to_dict(), ensure_ascii=False) + '\n')
            except (OSError, IOError) as e:
                logger.error(f"追加 Token 记录失败 (IO错误): {e}")
            except Exception as e:
                logger.error(f"追加 Token 记录时遇到非预期错误 ({type(e).__name__}): {e}")

    async def get_records(
        self,
        days: int = 7,
        agent_type: str = None
    ) -> List[Dict]:
        """获取使用记录 (异步版)"""
        if not self.log_file.exists():
            return []

        records = []
        cutoff = (datetime.now() - timedelta(days=days)).isoformat() if days > 0 else None

        try:
            async with aiofiles.open(self.log_file, 'r', encoding='utf-8') as f:
                async for line in f:
                    if not line.strip():
                        continue
                    try:
                        record = json.loads(line)
                        # 按时间过滤
                        if cutoff and record["timestamp"] < cutoff:
                            continue
                        # 按Agent类型过滤
                        if agent_type and record["agent_type"] != agent_type:
                            continue
                        records.append(record)
                    except json.JSONDecodeError:
                        continue
        except (OSError, IOError) as e:
            logger.error(f"读取 Token 记录失败 (IO错误): {e}")
        except Exception as e:
            logger.error(f"读取 Token 记录时遇到非预期错误 ({type(e).__name__}): {e}")

        return records

    async def get_summary(self, days: int = 7) -> Dict[str, Any]:
        """获取统计摘要 (异步版)"""
        records = await self.get_records(days)

        if not records:
            return {
                "period_days": days,
                "total_tasks": 0,
                "total_original_tokens": 0,
                "total_compressed_tokens": 0,
                "total_savings": 0,
                "overall_savings_ratio": 0,
                "by_agent": {}
            }

        # 按Agent汇总
        by_agent = defaultdict(lambda: {
            "tasks": 0,
            "original_tokens": 0,
            "compressed_tokens": 0,
            "savings_tokens": 0
        })

        for record in records:
            agent = record["agent_type"]
            by_agent[agent]["tasks"] += 1
            by_agent[agent]["original_tokens"] += record["original_tokens"]
            by_agent[agent]["compressed_tokens"] += record["compressed_tokens"]
            by_agent[agent]["savings_tokens"] += (
                record["original_tokens"] - record["compressed_tokens"]
            )

        # 计算总体统计
        total_original = sum(r["original_tokens"] for r in records)
        total_compressed = sum(r["compressed_tokens"] for r in records)
        total_savings = total_original - total_compressed

        # 构建Agent统计
        agent_stats = {}
        for agent, stats in by_agent.items():
            agent_stats[agent] = {
                "tasks": stats["tasks"],
                "original_tokens": stats["original_tokens"],
                "compressed_tokens": stats["compressed_tokens"],
                "savings_tokens": stats["savings_tokens"],
                "savings_ratio": (
                    stats["savings_tokens"] / stats["original_tokens"]
                    if stats["original_tokens"] > 0 else 0
                )
            }

        return {
            "period_days": days,
            "total_tasks": len(records),
            "total_original_tokens": total_original,
            "total_compressed_tokens": total_compressed,
            "total_savings": total_savings,
            "overall_savings_ratio": (
                total_savings / total_original
                if total_original > 0 else 0
            ),
            "by_agent": agent_stats
        }

    async def generate_report(self, days: int = 7) -> str:
        """生成文本报告 (异步版)

        Args:
            days: 最近几天

        Returns:
            str: 报告文本
        """
        summary = await self.get_summary(days)

        lines = [
            "=" * 60,
            "Token使用报告",
            f"统计周期: 最近{days}天",
            f"生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            "=" * 60,
            "",
            "总体统计",
            "-" * 40,
            f"总任务数: {summary['total_tasks']}",
            f"原始Token: {summary['total_original_tokens']:,}",
            f"压缩后Token: {summary['total_compressed_tokens']:,}",
            f"节省Token: {summary['total_savings']:,}",
            f"总体节省率: {summary['overall_savings_ratio']*100:.1f}%",
            "",
        ]

        if summary["by_agent"]:
            lines.append("按Agent统计")
            lines.append("-" * 40)

            for agent, stats in sorted(
                summary["by_agent"].items(),
                key=lambda x: x[1]["savings_tokens"],
                reverse=True
            ):
                lines.append(f"\n{agent}:")
                lines.append(f"  任务数: {stats['tasks']}")
                lines.append(f"  原始Token: {stats['original_tokens']:,}")
                lines.append(f"  节省Token: {stats['savings_tokens']:,}")
                lines.append(f"  节省率: {stats['savings_ratio']*100:.1f}%")

        lines.extend([
            "",
            "=" * 60,
            "报告结束",
            "=" * 60
        ])

        return '\n'.join(lines)

    async def export_to_csv(self, output_file: str = None, days: int = 7):
        """导出为CSV格式 (异步版)

        Args:
            output_file: 输出文件路径
            days: 最近几天
        """
        records = await self.get_records(days)

        if not records:
            logger.warning("没有可导出的记录")
            return

        output_file = output_file or f"token_usage_{days}d.csv"

        import csv
        import io

        # 在内存中构建 CSV
        output = io.StringIO()
        writer = csv.DictWriter(output, fieldnames=records[0].keys())
        writer.writeheader()
        writer.writerows(records)

        async with aiofiles.open(output_file, 'w', encoding='utf-8', newline='') as f:
            await f.write(output.getvalue())

        logger.info(f"Token使用记录已导出到: {output_file}")

    async def get_daily_stats(self, days: int = 7) -> Dict[str, Dict]:
        """获取每日统计 (异步版)

        Args:
            days: 最近几天

        Returns:
            Dict[日期, 统计]
        """
        records = await self.get_records(days)

        daily_stats = defaultdict(lambda: {
            "tasks": 0,
            "original_tokens": 0,
            "compressed_tokens": 0
        })

        for record in records:
            date = record["timestamp"][:10]  # 只取日期部分
            daily_stats[date]["tasks"] += 1
            daily_stats[date]["original_tokens"] += record["original_tokens"]
            daily_stats[date]["compressed_tokens"] += record["compressed_tokens"]

        # 按日期排序
        return dict(sorted(daily_stats.items()))

    async def get_trend(self, days: int = 7) -> Dict[str, Any]:
        """获取趋势数据 (异步版)

        Args:
            days: 最近几天

        Returns:
            Dict: 趋势数据
        """
        daily_stats = await self.get_daily_stats(days)

        if not daily_stats:
            return {"trend": [], "avg_savings": 0}

        trends = []
        total_savings_ratio = 0

        for date, stats in daily_stats.items():
            savings_ratio = (
                (stats["original_tokens"] - stats["compressed_tokens"]) /
                stats["original_tokens"]
                if stats["original_tokens"] > 0 else 0
            )
            trends.append({
                "date": date,
                "tasks": stats["tasks"],
                "original": stats["original_tokens"],
                "compressed": stats["compressed_tokens"],
                "savings_ratio": savings_ratio
            })
            total_savings_ratio += savings_ratio

        return {
            "trend": trends,
            "avg_savings": total_savings_ratio / len(trends) if trends else 0
        }

    async def cleanup(self):
        """清理旧记录 (异步版)
        
        按配置的 retention_days 保留记录，删除更早的记录。
        """
        if self.config.retention_days <= 0 or not self.log_file.exists():
            return

        cutoff = (datetime.now() - timedelta(days=self.config.retention_days)).isoformat()
        temp_file = self.log_file.with_suffix('.tmp')
        records_removed = 0

        async with self._lock:
            try:
                async with aiofiles.open(self.log_file, 'r', encoding='utf-8') as f_in:
                    async with aiofiles.open(temp_file, 'w', encoding='utf-8') as f_out:
                        async for line in f_in:
                            if not line.strip():
                                continue
                            try:
                                record = json.loads(line)
                                if record["timestamp"] >= cutoff:
                                    await f_out.write(line)
                                else:
                                    records_removed += 1
                            except json.JSONDecodeError:
                                continue
                
                # 替换原文件
                if records_removed > 0:
                    import os
                    os.replace(temp_file, self.log_file)
                    logger.info(f"清理了 {records_removed} 条旧的Token使用记录")
                else:
                    if temp_file.exists():
                        try:
                            import os
                            os.remove(temp_file)
                        except (OSError, IOError) as e:
                            logger.warning(f"清理 Token 临时文件失败: {e}")
            except (OSError, IOError) as e:
                logger.error(f"清理 Token 记录失败 (IO错误): {e}")
                if temp_file.exists():
                    try:
                        import os
                        os.remove(temp_file)
                    except:
                        pass
            except Exception as e:
                logger.error(f"清理 Token 记录时遇到非预期错误 ({type(e).__name__}): {e}")
                if temp_file.exists():
                    try:
                        import os
                        os.remove(temp_file)
                    except:
                        pass
