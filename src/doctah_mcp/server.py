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
from .tools import search_operator, search_enemy, list_operators, list_enemies, list_operators_advanced, list_enemies_advanced, recruit_by_tags, recruit_by_tags_grouped, recruit_by_tags_all, recruit_by_tags_suggest

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
    async def list_operators_advanced_mcp(
        keyword: Optional[str] = None,
        professions: Optional[str] = None,
        branches: Optional[str] = None,
        rarities: Optional[str] = None,
        positions: Optional[str] = None,
        genders: Optional[str] = None,
        obtains: Optional[str] = None,
        tags: Optional[str] = None,
        factions: Optional[str] = None,
        birthplaces: Optional[str] = None,
        races: Optional[str] = None,
        limit: int = 200,
    ) -> str:
        """
        干员多维筛选（参考 PRTS「干员一览」的筛选维度）
        
        示例：
        - professions="医疗,术师"  rarities="6,5"  positions="远程位"  tags="治疗,群攻"
        - factions="罗德岛" branches="速射手" genders="女性"
        """
        return await list_operators_advanced(
            keyword=keyword,
            professions=professions,
            branches=branches,
            rarities=rarities,
            positions=positions,
            genders=genders,
            obtains=obtains,
            tags=tags,
            factions=factions,
            birthplaces=birthplaces,
            races=races,
            limit=limit,
            wiki_client=wiki_client,
        )

    @mcp.tool()
    async def list_enemies_advanced_mcp(
        keyword: Optional[str] = None,
        enemy_level: Optional[str] = None,
        enemy_race: Optional[str] = None,
        attack_type: Optional[str] = None,
        damage_type: Optional[str] = None,
        endure: Optional[str] = None,
        attack: Optional[str] = None,
        defence: Optional[str] = None,
        move_speed: Optional[str] = None,
        attack_speed: Optional[str] = None,
        resistance: Optional[str] = None,
        limit: int = 200,
    ) -> str:
        """
        敌人多维筛选（参考 PRTS『敌人一览』）
        维度见网页：地位/种类/攻击方式/伤害类型 + 六维。
        """
        return await list_enemies_advanced(
            keyword=keyword,
            enemy_level=enemy_level,
            enemy_race=enemy_race,
            attack_type=attack_type,
            damage_type=damage_type,
            endure=endure,
            attack=attack,
            defence=defence,
            move_speed=move_speed,
            attack_speed=attack_speed,
            resistance=resistance,
            limit=limit,
            wiki_client=wiki_client,
        )

    @mcp.tool()
    async def recruit_by_tags_mcp(terms: str) -> str:
        """
        公招计算：给定词条（如 "资深干员, 术师, 群攻" 或 "先锋 费用回复"），返回可能出现的干员。
        """
        return await recruit_by_tags(terms, wiki_client)

    @mcp.tool()
    async def recruit_by_tags_grouped_mcp(terms: str) -> str:
        """
        公招计算（分组）：按“所选词条子集”分组展示可能出现的干员，类似网页的分块列表。
        """
        return await recruit_by_tags_grouped(terms, wiki_client)

    @mcp.tool()
    async def recruit_by_tags_all_mcp(terms: str) -> str:
        """
        公招计算（严格）：必须命中所有词条（AND）。
        """
        return await recruit_by_tags_all(terms, wiki_client)

    @mcp.tool()
    async def recruit_by_tags_suggest_mcp(terms: str, top_k: int = 10) -> str:
        """
        公招计算（建议组合）：自动搜索能产出结果的最佳子集组合，返回前 top_k 个组合。
        """
        return await recruit_by_tags_suggest(terms, top_k, wiki_client)

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