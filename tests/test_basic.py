#!/usr/bin/env python3
"""
Doctah-MCP 基本功能测试
"""

import pytest
import asyncio
from doctah_mcp import __version__
from doctah_mcp.client import PRTSWikiClient


def test_version():
    """测试版本号"""
    assert __version__ == "1.0.0"


def test_imports():
    """测试主要模块导入"""
    from doctah_mcp import search_operator, list_operators, search_enemy, list_enemies
    from doctah_mcp import PRTSWikiClient, create_server, run_server
    
    # 检查函数存在
    assert callable(search_operator)
    assert callable(list_operators)
    assert callable(search_enemy)
    assert callable(list_enemies)
    assert callable(create_server)
    assert callable(run_server)
    
    # 检查类存在
    assert PRTSWikiClient is not None


@pytest.mark.asyncio
async def test_prts_client_creation():
    """测试PRTS客户端创建"""
    client = PRTSWikiClient()
    assert client is not None
    
    # 测试基本属性
    assert hasattr(client, 'base_url')
    assert hasattr(client, 'search_api')


@pytest.mark.asyncio
async def test_operator_search_empty_name():
    """测试空名称的干员搜索"""
    from doctah_mcp import search_operator
    
    result = await search_operator("")
    assert "❌ 干员查询失败" in result
    assert "查询参数为空" in result


@pytest.mark.asyncio
async def test_enemy_search_empty_name():
    """测试空名称的敌人搜索"""
    from doctah_mcp import search_enemy
    
    result = await search_enemy("")
    assert "❌ 敌人查询失败" in result
    assert "查询参数为空" in result


@pytest.mark.integration
@pytest.mark.asyncio
async def test_operator_search_integration():
    """集成测试 - 实际干员搜索"""
    from doctah_mcp import search_operator
    
    # 测试查询银灰（一个常见干员）
    result = await search_operator("银灰", sections="基本信息")
    
    # 检查返回结果格式
    assert isinstance(result, str)
    assert len(result) > 0
    
    # 应该包含基本信息标志
    assert "干员" in result or "银灰" in result


@pytest.mark.integration  
@pytest.mark.asyncio
async def test_operator_list_integration():
    """集成测试 - 实际干员列表搜索"""
    from doctah_mcp import list_operators
    
    # 测试搜索阿米娅相关干员
    result = await list_operators("阿米娅")
    
    # 检查返回结果格式
    assert isinstance(result, str)
    assert len(result) > 0
    
    # 应该包含列表标志
    assert "干员搜索结果" in result or "干员列表" in result


def test_server_creation():
    """测试MCP服务器创建"""
    from doctah_mcp import create_server
    
    server = create_server("Test-Server")
    assert server is not None
    
    # 检查服务器属性
    assert hasattr(server, 'name')


if __name__ == "__main__":
    # 运行基本测试（非集成测试）
    pytest.main([__file__, "-v", "-m", "not integration"]) 