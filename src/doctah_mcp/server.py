#!/usr/bin/env python3
"""
Doctah-MCP Server

明日方舟PRTS.wiki智能助手的MCP服务器实现。
提供干员、敌人信息查询等功能。
"""

import asyncio
import logging
from typing import Optional

from mcp.server.fastmcp import FastMCP
from .client import PRTSWikiClient
from .tools import search_operator, search_enemy, list_operators, list_enemies

# 配置日志
logger = logging.getLogger(__name__)


def create_server(name: str = "Doctah-MCP") -> FastMCP:
    """创建MCP服务器实例"""
    mcp = FastMCP(name)
    wiki_client = PRTSWikiClient()

    @mcp.tool()
    async def search_operator_mcp(name: str, sections: Optional[str] = None) -> str:
        """
        搜索明日方舟干员信息
        
        Args:
            name: 干员名称（支持中文、英文、代号）
            sections: 要查询的章节，用逗号分隔。如："天赋,技能"。不指定则返回所有内容
        """
        return await search_operator(name, sections, wiki_client)

    @mcp.tool()
    async def search_enemy_mcp(name: str, sections: Optional[str] = None) -> str:
        """
        搜索明日方舟敌人信息
        
        Args:
            name: 敌人名称
            sections: 要查询的章节，用逗号分隔。如："级别0,级别1"。不指定则返回所有内容
        """
        return await search_enemy(name, sections, wiki_client)

    @mcp.tool()
    async def list_enemies_mcp(name: str) -> str:
        """
        搜索相关敌人并返回敌人名称列表（模糊搜索）
        
        Args:
            name: 敌人名称关键词（支持模糊搜索，如"源石虫"会返回所有源石虫类型）
        """
        return await list_enemies(name, wiki_client)

    @mcp.tool()
    async def list_operators_mcp(name: str) -> str:
        """
        搜索相关干员并返回干员名称列表（模糊搜索）
        
        Args:
            name: 干员名称关键词（支持模糊搜索，如"阿米娅"、"医疗"、"罗德岛"等）
        """
        return await list_operators(name, wiki_client)

    @mcp.tool()
    async def get_stage_info(stage_code: str) -> str:
        """
        获取关卡信息（暂未实现，返回占位符）
        
        Args:
            stage_code: 关卡代码，如 "1-1"
        """
        return f"关卡 {stage_code} 信息查询功能正在开发中..."

    @mcp.tool()
    async def get_event_info(event_name: str) -> str:
        """
        获取活动信息（暂未实现，返回占位符）
        
        Args:
            event_name: 活动名称
        """
        return f"活动 {event_name} 信息查询功能正在开发中..."

    @mcp.tool()
    async def search_items(item_name: str) -> str:
        """
        搜索道具信息（暂未实现，返回占位符）
        
        Args:
            item_name: 道具名称
        """
        return f"道具 {item_name} 信息查询功能正在开发中..."

    @mcp.tool()
    async def get_daily_stages() -> str:
        """
        获取今日开放关卡（暂未实现，返回占位符）
        """
        return "今日开放关卡信息查询功能正在开发中..."

    return mcp


def run_server(transport: str = "stdio") -> None:
    """运行MCP服务器"""
    logger.info("启动 Doctah-MCP 服务器...")
    mcp = create_server()
    mcp.run(transport=transport)


def main() -> None:
    """主函数 - 兼容性入口"""
    logging.basicConfig(level=logging.INFO)
    run_server()


if __name__ == "__main__":
    main() 