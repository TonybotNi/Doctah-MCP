#!/usr/bin/env python3
"""
敌人查询功能模块
提供敌人信息查询和列表搜索功能
"""

import asyncio
from typing import Optional
from ..client import PRTSWikiClient
from .utils import BASE_URL


async def search_enemy(name: str, sections: Optional[str] = None, wiki_client: Optional[PRTSWikiClient] = None) -> str:
    """
    搜索明日方舟敌人信息
    
    Args:
        name: 敌人名称
        sections: 要查询的章节，用逗号分隔。如："级别0,级别1"。不指定则返回所有内容
        wiki_client: 可选的客户端实例，如果不提供会自动创建
    """
    if not name:
        return """# ❌ 敌人查询失败

## 🔍 查询状态
- **状态**: 查询参数为空
- **错误类型**: EMPTY_QUERY

## 🎯 建议操作
请提供敌人名称进行查询。

---
💡 **提示**: 例如搜索"源石虫"等。
"""
    
    # 如果没有提供客户端，创建一个临时的
    client_provided = wiki_client is not None
    if not wiki_client:
        wiki_client = PRTSWikiClient()
    
    try:
        # 解析章节参数
        target_sections = None
        if sections:
            target_sections = [s.strip() for s in sections.split(',') if s.strip()]
        
        # 策略1：直接尝试访问敌人页面
        enemy_data = await wiki_client.parse_enemy_complete(name, target_sections)
        
        if not enemy_data:
            # 策略2：使用搜索API
            search_results = await wiki_client.search_pages(f"{name} 敌人")
            
            if not search_results:
                # 尝试直接搜索名称
                search_results = await wiki_client.search_pages(name)
            
            if not search_results:
                return f"""# ❌ 敌人查询失败

## 🔍 查询状态
- **状态**: 敌人不存在
- **查询名称**: {name}
- **错误类型**: ENEMY_NOT_FOUND

## 📋 可能的原因
1. **拼写错误**: 请检查敌人名称的拼写
2. **敌人不存在**: 该名称可能不是有效的明日方舟敌人

## 🎯 建议操作
1. 检查敌人名称拼写
2. 查看 [PRTS.wiki 敌人一览](https://prts.wiki/w/敌人一览) 确认敌人是否存在

## 🔗 相关链接
- [PRTS.wiki 敌人一览](https://prts.wiki/w/敌人一览)
- [PRTS.wiki 首页]({BASE_URL})

---
💡 **提示**: 这是一个标准化的"敌人不存在"响应，AI助手可以据此判断查询失败的原因。
"""
            
            # 找到最相关的敌人页面
            best_match = None
            for result in search_results:
                title = result['title']
                # 优先选择不包含子页面路径的结果
                if not any(substr in title for substr in ['/语音记录', '/敌人模型']):
                    best_match = result
                    break
            
            if not best_match:
                best_match = search_results[0]
            
            title = best_match['title']
            
            # 获取详细的敌人信息
            enemy_data = await wiki_client.parse_enemy_complete(title, target_sections)
        
        if not enemy_data:
            return f"""# ❌ 敌人查询失败

## 🔍 查询状态
- **状态**: 页面解析失败
- **查询名称**: {name}
- **错误类型**: ENEMY_PARSE_FAILED

## 📋 可能的原因
1. **页面格式不标准**: 该页面可能不是标准的敌人页面
2. **解析错误**: 页面结构发生变化导致解析失败

## 🎯 建议操作
1. 确认是否为有效的敌人页面
2. 检查页面是否正常加载

## 🔗 相关链接
- [PRTS.wiki 敌人一览](https://prts.wiki/w/敌人一览)
- [PRTS.wiki 首页]({BASE_URL})

---
💡 **提示**: 这是一个标准化的"敌人解析失败"响应。
"""
        
        # 格式化输出
        return wiki_client._format_enemy_info(enemy_data, target_sections)
        
    except Exception as e:
        return f"""# ❌ 敌人查询错误

## 🔍 查询状态
- **状态**: 系统错误
- **查询名称**: {name}
- **错误类型**: SYSTEM_ERROR
- **错误信息**: {str(e)}

## 🎯 建议操作
1. 重试查询
2. 检查网络连接
3. 联系管理员

---
💡 **提示**: 这是一个系统错误响应。
"""
    finally:
        # 如果是临时创建的客户端，确保清理资源
        if not client_provided and hasattr(wiki_client, 'close'):
            await wiki_client.close()


async def list_enemies(name: str, wiki_client: Optional[PRTSWikiClient] = None) -> str:
    """
    搜索相关敌人并返回敌人名称列表
    
    Args:
        name: 敌人名称关键词（支持模糊搜索）
        wiki_client: 可选的客户端实例，如果不提供会自动创建
    
    Returns:
        包含敌人列表的格式化字符串
    """
    if not name:
        return """# ❌ 敌人列表查询失败

## 🔍 查询状态
- **状态**: 查询参数为空
- **错误类型**: EMPTY_QUERY

## 🎯 建议操作
请提供敌人名称关键词进行搜索。

---
💡 **提示**: 例如搜索"源石虫"可以找到所有相关的源石虫类型敌人。
"""
    
    # 如果没有提供客户端，创建一个临时的
    client_provided = wiki_client is not None
    if not wiki_client:
        wiki_client = PRTSWikiClient()
    
    try:
        # 搜索相关敌人
        search_results = await wiki_client.search_pages(f"{name} 敌人")
        
        if not search_results:
            # 尝试直接搜索名称
            search_results = await wiki_client.search_pages(name)
        
        if not search_results:
            return f"""# ❌ 敌人列表查询失败

## 🔍 查询状态
- **状态**: 未找到相关敌人
- **查询关键词**: {name}
- **错误类型**: NO_ENEMIES_FOUND

## 📋 可能的原因
1. **关键词过于具体**: 试试更简短的关键词
2. **拼写错误**: 请检查敌人名称的拼写
3. **敌人不存在**: 该关键词可能不匹配任何敌人

## 🎯 建议操作
1. 使用更通用的关键词（如"虫"、"术师"、"士兵"等）
2. 查看 [PRTS.wiki 敌人一览](https://prts.wiki/w/敌人一览) 确认敌人名称

## 🔗 相关链接
- [PRTS.wiki 敌人一览](https://prts.wiki/w/敌人一览)
- [PRTS.wiki 首页]({BASE_URL})

---
💡 **提示**: 这是一个标准化的"未找到敌人"响应。
"""
        
        # 第一轮：基础过滤，收集候选页面
        candidates = []
        seen_names = set()
        
        for result in search_results:
            title = result['title']
            
            # 过滤掉子页面，但提取主页面名称
            if any(subpage in title for subpage in ['/spine', '/语音记录', '/敌人模型']):
                # 从子页面提取主页面名称
                main_name = title.split('/')[0]
                if main_name not in seen_names:
                    candidates.append(main_name)
                    seen_names.add(main_name)
            else:
                # 直接是主页面，过滤掉明显的干员页面
                if not any(prof in title for prof in ['（医疗）', '（术师）', '（狙击）', '（重装）', '（近卫）', '（先锋）', '（辅助）', '（特种）']):
                    if title not in seen_names:
                        candidates.append(title)
                        seen_names.add(title)
        
        # 第二轮：页面内容验证（限制验证数量以提高性能）
        print(f"🔍 找到 {len(candidates)} 个候选页面，正在验证...")
        enemy_names = []
        verified_count = 0
        max_verify = 15  # 最多验证15个页面，避免过多请求
        
        for title in candidates:
            if verified_count >= max_verify:
                # 如果验证数量达到上限，对于明显像敌人名称的直接通过
                if any(enemy_keyword in title for enemy_keyword in ['虫', '兵', '术师', '狗', '兽', '蛛', '守卫', '士兵']):
                    enemy_names.append(title)
                continue
                
            # 验证页面内容
            print(f"  验证: {title}")
            is_enemy = await wiki_client._verify_enemy_page(title)
            verified_count += 1
            
            if is_enemy:
                enemy_names.append(title)
                print(f"  ✅ 确认为敌人: {title}")
            else:
                print(f"  ❌ 非敌人页面: {title}")
        
        if not enemy_names:
            return f"""# ❌ 敌人列表查询失败

## 🔍 查询状态
- **状态**: 搜索结果无有效敌人页面
- **查询关键词**: {name}
- **搜索结果数**: {len(search_results)}
- **错误类型**: NO_VALID_ENEMIES

## 📋 搜索结果分析
找到了 {len(search_results)} 个结果，但都不是有效的敌人主页面。

## 🎯 建议操作
1. 尝试更精确的敌人名称
2. 查看 [PRTS.wiki 敌人一览](https://prts.wiki/w/敌人一览) 确认敌人名称

---
💡 **提示**: 可能搜索到的都是敌人的子页面，无法确定主页面名称。
"""
        
        # 格式化输出
        result = f"""# 🔍 敌人搜索结果

## 📊 查询信息
- **搜索关键词**: {name}
- **找到敌人数量**: {len(enemy_names)}
- **搜索结果总数**: {len(search_results)}

## 📋 敌人列表"""
        
        # 按字母/拼音排序（简单排序）
        enemy_names.sort()
        
        for i, enemy_name in enumerate(enemy_names, 1):
            result += f"\n{i:2d}. **{enemy_name}**"
        
        result += f"""

## 💡 使用说明
### 查询单个敌人详细信息：
可以使用以上任一敌人名称进行详细查询，例如：
```
敌人查询: {enemy_names[0] if enemy_names else "敌人名称"}
```

### 批量查询建议：
AI模型可以根据此列表，使用 `search_enemy()` 函数逐一查询每个敌人的详细信息。

## 🔗 相关链接
- [PRTS.wiki 敌人一览](https://prts.wiki/w/敌人一览)
- [PRTS.wiki 首页]({BASE_URL})

---
💡 **提示**: 这是敌人搜索列表，可用于进一步的详细查询。
"""
        
        return result
        
    except Exception as e:
        return f"""# ❌ 敌人列表查询错误

## 🔍 查询状态
- **状态**: 系统错误
- **查询关键词**: {name}
- **错误类型**: SYSTEM_ERROR
- **错误信息**: {str(e)}

## 🎯 建议操作
1. 重试查询
2. 检查网络连接
3. 联系管理员

---
💡 **提示**: 这是一个系统错误响应。
"""
    finally:
        # 如果是临时创建的客户端，确保清理资源
        if not client_provided and hasattr(wiki_client, 'close'):
            await wiki_client.close()


