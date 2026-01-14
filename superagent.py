#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
SuperAgent v3.2 启动脚本

直接运行: python superagent.py
"""

import sys
from pathlib import Path

# 添加项目根目录到路径
SUPERAGENT_ROOT = Path(__file__).parent
sys.path.insert(0, str(SUPERAGENT_ROOT))

if __name__ == "__main__":
    from cli.main import main
    main()
