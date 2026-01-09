#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
智能文件读取器

提供智能文件读取功能,根据文件大小自动选择读取方式
"""

import logging
import aiofiles
import os
from pathlib import Path
from typing import Tuple, Optional, Dict, List, Any
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class FileReadStats:
    """文件读取统计"""
    file_path: str
    file_size: int
    read_mode: str  # "full", "summary", "skipped"
    lines_total: int = 0
    lines_read: int = 0
    compression_ratio: float = 0.0

    def to_dict(self) -> Dict:
        return {
            "file_path": self.file_path,
            "file_size": f"{self.file_size / 1024:.2f} KB",
            "read_mode": self.read_mode,
            "lines_total": self.lines_total,
            "lines_read": self.lines_read,
            "compression_ratio": f"{self.compression_ratio * 100:.1f}%"
        }


class SmartFileReader:
    """智能文件读取器"""

    # 配置
    SMALL_FILE_THRESHOLD = 10 * 1024  # 10KB以下全量读取
    SUMMARY_LINES = 10  # 摘要模式: 前10行 + 后10行
    MAX_SUMMARY_SIZE = 50 * 1024  # 最大摘要大小(50KB)

    def __init__(self):
        self.read_stats = []

    async def read(
        self,
        file_path: Path,
        mode: str = "auto"
    ) -> Tuple[str, FileReadStats]:
        """智能读取文件
        ... (保持文档字符串一致)
        """
        if not file_path.exists():
            raise FileNotFoundError(f"文件不存在: {file_path}")

        file_size = file_path.stat().st_size
        stats = FileReadStats(
            file_path=str(file_path),
            file_size=file_size,
            read_mode="unknown"
        )

        # 根据文件大小和模式选择读取方式
        if mode == "auto":
            if file_size <= self.SMALL_FILE_THRESHOLD:
                stats.read_mode = "full"
            else:
                stats.read_mode = "summary"
        elif mode == "full":
            stats.read_mode = "full"
        elif mode == "summary":
            stats.read_mode = "summary"
        elif mode == "skip":
            stats.read_mode = "skipped"
            self.read_stats.append(stats)
            return "", stats
        else:
            stats.read_mode = "full"

        # 执行读取
        if stats.read_mode == "full":
            content = await self._read_full(file_path, stats)
        elif stats.read_mode == "summary":
            content = await self._read_summary(file_path, stats)
        else:
            content = ""

        # 确保添加到统计列表 (即使子方法中有 return, 这里的 stats 也是引用传递并已被更新)
        if stats not in self.read_stats:
            self.read_stats.append(stats)
            
        return content, stats

    async def _read_full(self, file_path: Path, stats: FileReadStats) -> str:
        """全量读取 (异步实现)"""
        for encoding in ['utf-8', 'gbk', 'latin1']:
            try:
                async with aiofiles.open(file_path, mode='r', encoding=encoding) as f:
                    content = await f.read()
                    lines = content.split('\n')
                    stats.lines_total = len(lines)
                    stats.lines_read = len(lines)
                    stats.compression_ratio = 1.0
                    return content
            except UnicodeDecodeError:
                continue
        
        # 如果所有编码都失败，尝试二进制读取或报错
        logger.error(f"无法使用支持的编码读取文件: {file_path}")
        raise UnicodeDecodeError("utf-8", b"", 0, 1, "所有尝试的编码均失败")

    async def _read_summary(self, file_path: Path, stats: FileReadStats) -> str:
        """摘要读取 (优化版: 针对大文件避免全量加载)"""
        # 如果文件小于 100KB，全量读取也没关系，保持简单
        if stats.file_size < 100 * 1024:
            content = await self._read_full(file_path, stats)
            lines = content.split('\n')
            if len(lines) <= self.SUMMARY_LINES * 2:
                return content
            
            header = '\n'.join(lines[:self.SUMMARY_LINES])
            footer = '\n'.join(lines[-self.SUMMARY_LINES:])
            summary = f"{header}\n\n... (省略{len(lines) - self.SUMMARY_LINES * 2}行) ...\n\n{footer}"
            stats.lines_read = self.SUMMARY_LINES * 2
            stats.compression_ratio = stats.lines_read / stats.lines_total
            return summary

        # 针对超大文件，使用 seek 读取开头和结尾
        try:
            # 读取开头 4KB
            async with aiofiles.open(file_path, mode='r', encoding='utf-8', errors='ignore') as f:
                header_content = await f.read(4096)
                header_lines = header_content.split('\n')[:self.SUMMARY_LINES]
                header = '\n'.join(header_lines)

            # 读取结尾 4KB
            async with aiofiles.open(file_path, mode='rb') as f:
                await f.seek(0, os.SEEK_END)
                size = await f.tell()
                read_size = min(size, 4096)
                await f.seek(size - read_size, os.SEEK_SET)
                footer_bytes = await f.read()
                footer_content = footer_bytes.decode('utf-8', errors='ignore')
                footer_lines = footer_content.split('\n')[-self.SUMMARY_LINES:]
                footer = '\n'.join(footer_lines)

            # 估算总行数 (基于文件大小和平均行长)
            avg_line_len = len(header_content) / max(1, len(header_content.split('\n')))
            stats.lines_total = int(stats.file_size / max(1, avg_line_len))
            stats.lines_read = self.SUMMARY_LINES * 2
            stats.compression_ratio = stats.lines_read / max(1, stats.lines_total)

            return f"{header}\n\n... (大文件摘要，省略约 {stats.lines_total - stats.lines_read} 行) ...\n\n{footer}"
        except (OSError, IOError, UnicodeDecodeError) as e:
            logger.warning(f"大文件摘要读取失败 (IO或编码错误)，退回到全量读取: {e}")
            return await self._read_full(file_path, stats)
        except Exception as e:
            logger.warning(f"大文件摘要读取时遇到非预期错误 ({type(e).__name__})，退回到全量读取: {e}")
            return await self._read_full(file_path, stats)

    async def read_multiple(
        self,
        file_paths: list,
        mode: str = "auto"
    ) -> Tuple[Dict[str, Tuple[str, FileReadStats]], FileReadStats]:
        """批量读取多个文件 (异步并行)"""
        tasks = []
        for file_path in file_paths:
            tasks.append(self.read(Path(file_path), mode))
        
        results_list = await asyncio.gather(*tasks, return_exceptions=True)
        
        results = {}
        total_stats = FileReadStats(
            file_path="multiple",
            file_size=0,
            read_mode="mixed"
        )

        for i, res in enumerate(results_list):
            file_path = file_paths[i]
            if isinstance(res, Exception):
                logger.warning(f"读取文件失败: {file_path}, 错误类型: {type(res).__name__}, 内容: {res}")
                continue
            
            content, stats = res
            results[str(file_path)] = (content, stats)
            
            total_stats.file_size += stats.file_size
            total_stats.lines_total += stats.lines_total
            total_stats.lines_read += stats.lines_read

        if total_stats.lines_total > 0:
            total_stats.compression_ratio = total_stats.lines_read / total_stats.lines_total

        return results, total_stats

    def get_read_stats(self) -> List[FileReadStats]:
        """获取读取统计"""
        return self.read_stats

    def get_read_summary(self) -> List[Dict[str, Any]]:
        """获取读取摘要列表 (供测试和 UI 使用)"""
        return [s.to_dict() for s in self.read_stats]

    def get_summary_stats(self) -> Dict[str, Any]:
        """获取汇总统计"""
        if not self.read_stats:
            return {"total_files": 0}

        total_size = sum(s.file_size for s in self.read_stats)
        total_lines = sum(s.lines_total for s in self.read_stats)
        total_read = sum(s.lines_read for s in self.read_stats)
        summary_count = sum(1 for s in self.read_stats if s.read_mode == "summary")
        full_count = sum(1 for s in self.read_stats if s.read_mode == "full")

        return {
            "total_files": len(self.read_stats),
            "total_size_mb": total_size / (1024 * 1024),
            "total_lines": total_lines,
            "total_lines_read": total_read,
            "summary_mode_files": summary_count,
            "full_mode_files": full_count,
            "overall_compression_ratio": f"{total_read / max(1, total_lines) * 100:.1f}%"
        }
