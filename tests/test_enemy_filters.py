#!/usr/bin/env python3
"""
敌人高级筛选 功能测试（集成测试）
"""

import pytest
from doctah_mcp.tools.enemies import list_enemies_advanced


@pytest.mark.integration
@pytest.mark.asyncio
async def test_enemy_filter_basic():
    """普通 + 感染生物 + 近战 + 物理，应该有若干命中（如源石虫等）"""
    res = await list_enemies_advanced(
        enemy_level="普通",
        enemy_race="感染生物",
        attack_type="近战",
        damage_type="物理",
        limit=50,
    )
    assert isinstance(res, str) and len(res) > 0
    assert "**匹配敌人**: 0" not in res
    assert "源石虫" in res or "源石虫-" in res


@pytest.mark.integration
@pytest.mark.asyncio
async def test_enemy_filter_six_dims():
    """六维条件组合：生命值S 或 攻击S；应能返回非空列表"""
    res = await list_enemies_advanced(
        endure="S,S+",
        attack="S,S+",
        limit=50,
    )
    assert isinstance(res, str) and len(res) > 0
    assert "**匹配敌人**: 0" not in res 