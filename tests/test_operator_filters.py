#!/usr/bin/env python3
"""
高级干员筛选 功能测试（集成测试）
"""

import re
import pytest

from doctah_mcp.tools.operators import list_operators_advanced


@pytest.mark.integration
@pytest.mark.asyncio
async def test_advanced_filter_sniper_6star():
    """6星 狙击 远程位，应返回非空列表"""
    result = await list_operators_advanced(
        professions="狙击",
        rarities="6",
        positions="远程位",
        limit=50,
    )
    assert isinstance(result, str) and len(result) > 0
    # 匹配数量 > 0
    m = re.search(r"匹配干员\*\*: (\d+)", result)
    if not m:
        m = re.search(r"匹配干员\*\*:?(\s*)(\d+)", result)
    count_ok = (int(m.group(2 if m and m.lastindex == 2 else 1)) > 0) if m else ("**匹配干员**: 0" not in result)
    assert count_ok, f"unexpected result: {result[:300]}"
    # 至少包含 6★ 和 狙击 字样
    assert "6★" in result and "狙击" in result


@pytest.mark.integration
@pytest.mark.asyncio
async def test_advanced_filter_rhodes_island_casters_female():
    """罗德岛 + 术师 + 女性 + 5-6星，应返回包含若干代表性干员"""
    result = await list_operators_advanced(
        factions="罗德岛",
        professions="术师",
        genders="女,女性",
        rarities="6,5",
        limit=100,
    )
    assert isinstance(result, str) and len(result) > 0
    # 匹配数量 > 0
    assert "**匹配干员**: 0" not in result
    # 常见结果之一
    candidates = ["刻俄柏", "阿米娅", "炎狱炎熔", "妮芙", "烛煌"]
    assert any(name in result for name in candidates) 