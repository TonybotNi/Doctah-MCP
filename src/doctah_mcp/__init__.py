"""
Doctah-MCP: 明日方舟PRTS.wiki智能助手

一个基于Model Context Protocol (MCP)的明日方舟资料查询服务器，
为AI助手提供准确的游戏资料访问能力。

Features:
- 🎯 智能干员信息查询与列表搜索
- ⚔️ 敌人数据查询与分类识别  
- 🔍 页面内容验证确保准确性
- 📋 结构化输出便于AI理解
- 🚀 高性能异步处理
"""

__version__ = "1.0.0"
__author__ = "Mudrobot"
__email__ = "mudrobot@example.com"
__description__ = "明日方舟PRTS.wiki智能助手 - MCP服务器"
__url__ = "https://github.com/mudrobot/doctah-mcp"

# 导出主要组件
from .client import PRTSWikiClient
from .tools import search_operator, search_enemy, list_operators, list_enemies
from .server import create_server, run_server

__all__ = [
    "__version__",
    "__author__", 
    "__description__",
    "PRTSWikiClient",
    "search_operator",
    "search_enemy", 
    "list_operators",
    "list_enemies",
    "create_server",
    "run_server",
] 