#!/usr/bin/env python3
"""
Doctah-MCP 基本使用示例
演示如何使用Doctah-MCP进行干员和敌人查询
"""

import asyncio
from doctah_mcp import search_operator, list_operators, search_enemy, list_enemies


async def basic_operator_query():
    """基本干员查询示例"""
    print("=== 基本干员查询 ===")
    
    # 查询银灰的完整信息
    result = await search_operator("银灰")
    print("银灰完整信息:")
    print(result[:500] + "..." if len(result) > 500 else result)
    
    print("\n" + "="*50 + "\n")
    
    # 查询阿米娅的技能信息
    skills = await search_operator("阿米娅（医疗）", sections="技能")
    print("阿米娅（医疗）技能信息:")
    print(skills[:300] + "..." if len(skills) > 300 else skills)


async def operator_list_example():
    """干员列表搜索示例"""
    print("=== 干员列表搜索 ===")
    
    # 搜索所有医疗干员
    medical_ops = await list_operators("医疗")
    print("医疗相关干员:")
    print(medical_ops[:400] + "..." if len(medical_ops) > 400 else medical_ops)
    
    print("\n" + "="*30 + "\n")
    
    # 搜索阿米娅相关干员
    amiya_ops = await list_operators("阿米娅")
    print("阿米娅相关干员:")
    print(amiya_ops)


async def enemy_query_example():
    """敌人查询示例"""
    print("=== 敌人查询 ===")
    
    # 搜索源石虫类型敌人
    enemy_list = await list_enemies("源石虫")
    print("源石虫类型敌人:")
    print(enemy_list[:400] + "..." if len(enemy_list) > 400 else enemy_list)
    
    print("\n" + "="*30 + "\n")
    
    # 查询具体敌人信息
    enemy_info = await search_enemy("源石虫", sections="级别0")
    print("源石虫级别0信息:")
    print(enemy_info[:300] + "..." if len(enemy_info) > 300 else enemy_info)


async def batch_query_workflow():
    """批量查询工作流程示例"""
    print("=== 批量查询工作流程 ===")
    
    # 1. 先获取干员列表
    operators = await list_operators("罗德岛")
    print("步骤1 - 搜索罗德岛相关干员:")
    print(operators[:300] + "..." if len(operators) > 300 else operators)
    
    # 2. 模拟从列表中提取干员名称（实际使用中需要解析markdown）
    sample_operators = ["阿米娅", "凯尔希", "W"]
    
    print("\n步骤2 - 批量查询详细信息:")
    for op_name in sample_operators:
        try:
            info = await search_operator(op_name, sections="基本信息")
            print(f"\n--- {op_name} ---")
            print(info[:200] + "..." if len(info) > 200 else info)
        except Exception as e:
            print(f"查询 {op_name} 失败: {e}")


async def main():
    """主函数 - 运行所有示例"""
    print("🤖 Doctah-MCP 基本使用示例")
    print("="*60)
    
    try:
        await basic_operator_query()
        print("\n" + "="*60 + "\n")
        
        await operator_list_example()
        print("\n" + "="*60 + "\n")
        
        await enemy_query_example()
        print("\n" + "="*60 + "\n")
        
        await batch_query_workflow()
        
    except Exception as e:
        print(f"❌ 运行示例时出错: {e}")
        print("请确保网络连接正常，并且PRTS.wiki可以访问")
    
    print("\n🎉 示例运行完成!")


if __name__ == "__main__":
    asyncio.run(main()) 