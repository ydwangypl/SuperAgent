#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
日志配置
"""

import logging
from pathlib import Path


def setup_logging(log_level: str = "INFO"):
    """设置日志"""
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)

    logging.basicConfig(
        level=getattr(logging, log_level),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_dir / "superagent.log"),
            logging.StreamHandler()
        ]
    )
