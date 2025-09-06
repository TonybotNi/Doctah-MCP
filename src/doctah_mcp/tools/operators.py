#!/usr/bin/env python3
"""
干员查询功能模块
提供干员信息查询和列表搜索功能
"""

import asyncio
from typing import Optional
from ..client import PRTSWikiClient
from .utils import _create_operator_not_found_response, _extract_similar_operator_names, BASE_URL


async def search_operator(name: str, sections: Optional[str] = None, wiki_client: Optional[PRTSWikiClient] = None) -> str:
    """
    搜索明日方舟干员信息
    
    Args:
        name: 干员名称（支持中文、英文、代号）
        sections: 要查询的章节，用逗号分隔。如："天赋,技能"。不指定则返回所有内容
        wiki_client: 可选的客户端实例，如果不提供会自动创建
    """
    if not name:
        return _create_operator_not_found_response("空名称", ["请输入有效的干员名称"])
    
    # 如果没有提供客户端，创建一个临时的
    client_provided = wiki_client is not None
    if not wiki_client:
        wiki_client = PRTSWikiClient()
    
    try:
        # 解析章节参数
        target_sections = None
        if sections:
            target_sections = [s.strip() for s in sections.split(',') if s.strip()]
        
        # 策略1：直接尝试访问干员页面
        potential_titles = [
            name,  # 直接使用名称
            f"{name}（医疗）", f"{name}（术师）", f"{name}（狙击）", 
            f"{name}（重装）", f"{name}（近卫）", f"{name}（先锋）", 
            f"{name}（辅助）", f"{name}（特种）"
        ]
        
        # 尝试直接访问可能的页面
        operator_data = None
        for title in potential_titles:
            temp_data = await wiki_client.parse_operator_complete(title, target_sections)
            if temp_data and (temp_data.get('basic_info') or temp_data.get('sections') or temp_data.get('table_of_contents')):
                # 检查是否为敌人页面
                if temp_data.get('type') == 'enemy':
                    return f"""# ⚠️ 发现敌人页面

## 🔍 查询结果
- **查询名称**: {name}
- **找到页面**: {title}
- **页面类型**: 敌人页面

## 💡 建议
该查询结果指向敌人页面，而非干员页面。如果您要查询敌人信息，请使用敌人查询功能。

如果您确实要查询名为 "{name}" 的干员，可能是：
1. 干员不存在
2. 名称拼写有误
3. 需要完整的干员名称（如"阿米娅（医疗）"）

## 🔗 相关链接
- [PRTS.wiki 干员一览](https://prts.wiki/w/干员一览)
- [PRTS.wiki 敌人一览](https://prts.wiki/w/敌人一览)

---
💡 **提示**: 请使用专门的敌人查询功能来获取敌人信息。
"""
                
                # 找到有效的干员页面
                operator_data = temp_data
                break
        
        if not operator_data:
            # 策略2：使用搜索API
            search_results = await wiki_client.search_pages(f"{name} 干员")
            
            if not search_results:
                # 尝试直接搜索名称
                search_results = await wiki_client.search_pages(name)
            
            if not search_results:
                return _create_operator_not_found_response(name)
            
            # 找到最相关的干员主页面（排除密录、语音、模型等子页面）
            best_match = None
            potential_enemy_pages = []
            
            for result in search_results:
                title = result['title']
                
                # 检查是否是敌人的子页面（如 /spine）
                if '/spine' in title:
                    # 提取可能的敌人主页面名称
                    main_name = title.split('/')[0]
                    potential_enemy_pages.append(main_name)
                    continue
                
                # 优先选择不包含子页面路径的结果
                if not any(substr in title for substr in ['/干员密录', '/语音记录', '/干员模型', '/悖论模拟']):
                    # 进一步过滤，优先选择确实是干员页面的结果
                    if any(prof in title for prof in ['（医疗）', '（术师）', '（狙击）', '（重装）', '（近卫）', '（先锋）', '（辅助）', '（特种）']) or title == name:
                        best_match = result
                        break
            
            # 如果没找到干员页面，但找到了可能的敌人页面
            if not best_match and potential_enemy_pages:
                # 尝试访问敌人主页面
                for enemy_name in set(potential_enemy_pages):  # 去重
                    if enemy_name == name:  # 精确匹配查询名称
                        try:
                            enemy_data = await wiki_client.parse_enemy_complete(enemy_name, target_sections)
                            if enemy_data:
                                # 找到了敌人页面，返回敌人页面提示
                                return f"""# ⚠️ 发现敌人页面

## 🔍 查询结果
- **查询名称**: {name}
- **找到页面**: {enemy_name}
- **页面类型**: 敌人页面

## 💡 建议
该查询结果指向敌人页面，而非干员页面。如果您要查询敌人信息，请使用敌人查询功能。

如果您确实要查询名为 "{name}" 的干员，可能是：
1. 干员不存在
2. 名称拼写有误
3. 需要完整的干员名称（如"阿米娅（医疗）"）

## 🔗 相关链接
- [PRTS.wiki 干员一览](https://prts.wiki/w/干员一览)
- [PRTS.wiki 敌人一览](https://prts.wiki/w/敌人一览)

---
💡 **提示**: 请使用专门的敌人查询功能来获取敌人信息。
"""
                        except Exception:
                            continue  # 如果解析失败，继续尝试其他页面
            
            if not best_match:
                # 如果没找到标准格式，提取相似名称建议
                similar_names = _extract_similar_operator_names(search_results, name)
                if similar_names:
                    return _create_operator_not_found_response(name, similar_names)
                else:
                    # 作为最后手段，选择第一个结果
                    best_match = search_results[0]
            
            title = best_match['title']
            
            # 获取详细的干员信息
            operator_data = await wiki_client.parse_operator_complete(title, target_sections)
        
        if not operator_data:
            # 如果有标题说明找到了页面但无法解析内容
            if 'title' in locals():
                return _create_operator_not_found_response(name, [f"找到页面 '{title}' 但无法解析内容，可能是页面格式问题"])
            else:
                return _create_operator_not_found_response(name)
        
        # 格式化输出
        result = f"# {operator_data['name']}\n\n"
        
        # 如果指定了章节，只显示指定章节的内容
        if target_sections:
            # 章节过滤模式：只显示请求的章节
            pass  # 基本信息和目录不显示，直接跳到章节内容
        else:
            # 完整模式：显示所有信息
            # 基本信息
            if operator_data.get('basic_info'):
                result += "## 📋 基本信息\n"
                for key, value in operator_data['basic_info'].items():
                    result += f"- **{key}**: {value}\n"
                result += "\n"
            
            # 职业和稀有度
            if operator_data.get('profession') or operator_data.get('rarity'):
                result += "## 📊 基础数据\n"
                if operator_data.get('profession'):
                    result += f"- **职业**: {operator_data['profession']}\n"
                if operator_data.get('rarity'):
                    result += f"- **稀有度**: {operator_data['rarity']}\n"
                result += "\n"
            
            # 目录
            if operator_data.get('table_of_contents'):
                result += "## 📚 页面目录\n"
                skip_sections = {'注释与链接', '干员模型'}
                for toc_id, toc_info in operator_data['table_of_contents'].items():
                    # 跳过不需要的章节（使用更宽松的匹配）
                    if any(skip_section in toc_info['title'] for skip_section in skip_sections):
                        continue
                    indent = "  " * (toc_info['level'] - 1) if toc_info['level'] > 1 else ""
                    result += f"{indent}- {toc_info['title']}\n"
                result += "\n"
        
        # 各章节内容
        if operator_data.get('sections'):
            section_icons = {
                'characteristics': '⚡',
                'acquisition': '🎁',
                'attributes': '📊',
                'attack_range': '🎯',
                'talents': '🌟',
                'potential': '💎',
                'skills': '🎯',
                'base_skills': '🏢',
                'elite_materials': '⭐',
                'skill_materials': '📚',
                'modules': '🔧',
                'related_items': '🎒',
                'operator_record': '📜',
                'voice_records': '🎤',
                'operator_files': '📁',
                'paradox_simulation': '🎮',
                'operator_model': '🎨',
                'notes_and_links': '🔗'
            }
            
            for section_key, section_data in operator_data['sections'].items():
                icon = section_icons.get(section_key, '📋')
                title = section_data['title']
                content = section_data['content']
                
                if content:
                    result += f"## {icon} {title}\n"
                    result += f"{content}\n\n"
        
        # 页面链接
        result += f"---\n📍 **页面链接**: {operator_data['url']}\n"
        
        return result
        
    finally:
        # 如果是我们临时创建的客户端，需要关闭它
        if not client_provided:
            await wiki_client.close() 


async def list_operators(name: str, wiki_client: Optional[PRTSWikiClient] = None) -> str:
    """
    搜索相关干员并返回干员名称列表
    
    Args:
        name: 干员名称关键词（支持模糊搜索，如"阿米娅"、"医疗"、"罗德岛"等）
        wiki_client: 可选的客户端实例，如果不提供会自动创建
    
    Returns:
        包含干员列表的格式化字符串
    """
    if not name:
        return """# ❌ 干员列表查询失败

## 🔍 查询状态
- **状态**: 查询参数为空
- **错误类型**: EMPTY_QUERY

## 🎯 建议操作
请提供干员名称关键词进行搜索。

---
💡 **提示**: 例如搜索"阿米娅"可以找到所有阿米娅相关干员，搜索"医疗"可以找到医疗职业干员。
"""
    
    # 如果没有提供客户端，创建一个临时的
    client_provided = wiki_client is not None
    if not wiki_client:
        wiki_client = PRTSWikiClient()
    
    try:
        # 搜索相关干员
        search_results = await wiki_client.search_pages(f"{name} 干员")
        
        # 如果第一次搜索没有结果，或者搜索结果都是子页面，尝试直接搜索名称
        if not search_results:
            search_results = await wiki_client.search_pages(name)
        else:
            # 检查第一次搜索的结果是否都是子页面
            valid_results = []
            for result in search_results:
                title = result['title']
                if not any(subpage in title for subpage in ['/干员密录', '/语音记录', '/干员模型', '/悖论模拟', '/spine']):
                    valid_results.append(result)
            
            # 如果第一次搜索的结果都是子页面，进行第二次搜索并合并结果
            if not valid_results:
                additional_results = await wiki_client.search_pages(name)
                search_results.extend(additional_results)
        
        if not search_results:
            return f"""# ❌ 干员列表查询失败

## 🔍 查询状态
- **状态**: 未找到相关干员
- **查询关键词**: {name}
- **错误类型**: NO_OPERATORS_FOUND

## 📋 可能的原因
1. **关键词过于具体**: 试试更简短的关键词
2. **拼写错误**: 请检查干员名称的拼写
3. **干员不存在**: 该关键词可能不匹配任何干员

## 🎯 建议操作
1. 使用更通用的关键词（如"医疗"、"术师"、"阿米娅"等）
2. 查看 [PRTS.wiki 干员一览](https://prts.wiki/w/干员一览) 确认干员名称

## 🔗 相关链接
- [PRTS.wiki 干员一览](https://prts.wiki/w/干员一览)
- [PRTS.wiki 首页]({BASE_URL})

---
💡 **提示**: 这是一个标准化的"未找到干员"响应。
"""
        
        # 第一轮：基础过滤，收集候选页面
        candidates = []
        seen_names = set()
        
        for result in search_results:
            title = result['title']
            
            # 过滤掉明显的子页面和非干员页面
            if any(subpage in title for subpage in ['/干员密录', '/语音记录', '/干员模型', '/悖论模拟', '/spine']):
                continue
            
            # 过滤掉明显的敌人页面标识
            if any(enemy_indicator in title for enemy_indicator in ['级别0', '级别1', '级别2', '敌人模型']):
                continue
            
            # 过滤掉明显的道具、家具等
            if any(non_operator in title for non_operator in ['的信物', '的生日蛋糕', '家具', '道具', '材料', '芯片', '模组', 
                                                              '技能书', '经验', '龙门币', '合成玉', '源石', '赠礼', '装置',
                                                              '装备', '时装', '皮肤', '立绘', '头像', '名片', '徽章', '陈列',
                                                              '摆件', '柜', '架', '肯德基', '战利品', '古典', '陈旧']):
                continue
            
            # 过滤掉分类页面
            if any(non_operator in title for non_operator in ['分类:', '一览', '列表', '模板:', 'Category:', 'Template:']):
                continue
            
            # 收集所有可能的候选页面
            if title not in seen_names:
                # 有职业标识的优先级最高
                if any(prof in title for prof in ['（医疗）', '（术师）', '（狙击）', '（重装）', '（近卫）', '（先锋）', '（辅助）', '（特种）']):
                    candidates.insert(0, title)  # 插入到前面，优先验证
                    seen_names.add(title)
                # 特殊形态的干员（需要验证，因为魔王阿米娅实际是敌人）
                elif any(special in title for special in ['魔王', '(升变)', '（升变）']):
                    candidates.append(title)
                    seen_names.add(title)
                # 简短的页面名称
                elif (len(title) <= 8 and '/' not in title and '：' not in title and '的' not in title 
                      and not title.isdigit()):
                    if not any(non_operator in title.lower() for non_operator in ['list', 'category', '分类', '一览', '模板', 
                                                                                   '装备', '芯片', '展览', '仪', '信物']):
                        candidates.append(title)
                        seen_names.add(title)
        
        # 第二轮：页面内容验证（限制验证数量以提高性能）
        print(f"🔍 找到 {len(candidates)} 个候选页面，正在验证...")
        operator_names = []
        verified_count = 0
        max_verify = 15  # 最多验证15个页面，避免过多请求
        
        for title in candidates:
            if verified_count >= max_verify:
                # 如果验证数量达到上限，对于有职业标识的直接通过
                if any(prof in title for prof in ['（医疗）', '（术师）', '（狙击）', '（重装）', '（近卫）', '（先锋）', '（辅助）', '（特种）']):
                    operator_names.append(title)
                continue
                
            # 验证页面内容
            print(f"  验证: {title}")
            is_operator = await wiki_client._verify_operator_page(title)
            verified_count += 1
            
            if is_operator:
                operator_names.append(title)
                print(f"  ✅ 确认为干员: {title}")
            else:
                print(f"  ❌ 非干员页面: {title}")
        
        if not operator_names:
            return f"""# ❌ 干员列表查询失败

## 🔍 查询状态
- **状态**: 搜索结果无有效干员页面
- **查询关键词**: {name}
- **搜索结果数**: {len(search_results)}
- **错误类型**: NO_VALID_OPERATORS

## 📋 搜索结果分析
找到了 {len(search_results)} 个结果，但都不是有效的干员主页面。

## 🎯 建议操作
1. 尝试更精确的干员名称或职业名称
2. 查看 [PRTS.wiki 干员一览](https://prts.wiki/w/干员一览) 确认干员名称

---
💡 **提示**: 可能搜索到的都是干员的子页面或其他非干员页面。
"""
        
        # 格式化输出
        result = f"""# 🔍 干员搜索结果

## 📊 查询信息
- **搜索关键词**: {name}
- **找到干员数量**: {len(operator_names)}
- **搜索结果总数**: {len(search_results)}

## 📋 干员列表"""
        
        # 按字母/拼音排序（简单排序）
        operator_names.sort()
        
        for i, operator_name in enumerate(operator_names, 1):
            result += f"\n{i:2d}. **{operator_name}**"
        
        result += f"""

## 💡 使用说明
### 查询单个干员详细信息：
可以使用以上任一干员名称进行详细查询，例如：
```
干员查询: {operator_names[0] if operator_names else "干员名称"}
```

### 批量查询建议：
AI模型可以根据此列表，使用 `search_operator()` 函数逐一查询每个干员的详细信息。

## 🔗 相关链接
- [PRTS.wiki 干员一览](https://prts.wiki/w/干员一览)
- [PRTS.wiki 首页]({BASE_URL})

---
💡 **提示**: 这是干员搜索列表，可用于进一步的详细查询。
"""
        
        return result
        
    except Exception as e:
        return f"""# ❌ 干员列表查询错误

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


async def list_operators_advanced(
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
    wiki_client: Optional[PRTSWikiClient] = None,
) -> str:
    """
    按多维条件筛选干员并返回列表。

    所有字符串参数均为以逗号/顿号分隔的多值，例如：
    professions="医疗,术师"  rarities="6,5"  tags="治疗,群攻"。
    """
    # 预处理参数
    def parse_multi(value: Optional[str]) -> set[str]:
        if not value:
            return set()
        seps = [',', '，', '、', '|', ' ']
        temp = value
        for s in seps:
            temp = temp.replace(s, ',')
        items = [x.strip() for x in temp.split(',') if x.strip()]
        return set(items)

    def normalize_text(s: str) -> str:
        return s.replace('：', ':').replace('（', '(').replace('）', ')').strip()

    def normalize_rarity_set(values: set[str]) -> set[str]:
        mapped = set()
        for v in values:
            v = v.replace('★', '').replace('星', '').replace('稀有度', '').strip()
            for ch in ['一','二','三','四','五','六']:
                pass
            cn_map = {'一': '1', '二': '2', '三': '3', '四': '4', '五': '5', '六': '6'}
            if v in cn_map:
                v = cn_map[v]
            if v.isdigit():
                mapped.add(v)
        return mapped

    professions_set = parse_multi(professions)
    branches_set = parse_multi(branches)
    rarities_set = normalize_rarity_set(parse_multi(rarities))
    positions_set = parse_multi(positions)
    genders_set = parse_multi(genders)
    obtains_set = parse_multi(obtains)
    tags_set = parse_multi(tags)
    factions_set = parse_multi(factions)
    birthplaces_set = parse_multi(birthplaces)
    races_set = parse_multi(races)

    # 如果没有任何条件且没有关键词，则返回提示
    if not any([
        keyword, professions_set, branches_set, rarities_set, positions_set,
        genders_set, obtains_set, tags_set, factions_set, birthplaces_set, races_set
    ]):
        return (
            "# ❌ 干员多维筛选失败\n\n"
            "- **状态**: 缺少筛选条件\n"
            "- **错误类型**: EMPTY_FILTERS\n\n"
            "请至少提供一个条件，如 professions=医疗 或 tags=治疗。\n"
        )

    # 创建或复用客户端
    client_provided = wiki_client is not None
    if not wiki_client:
        wiki_client = PRTSWikiClient()

    try:
        # 1) 首选使用『干员一览』页面内置的数据（#filter-data）
        filter_data = await wiki_client.get_operator_filter_data()
        filtered: list[dict] = []

        def match_contains(value: str, need: set[str]) -> bool:
            if not need:
                return True
            if value is None:
                return False
            v = normalize_text(str(value))
            return any(n in v for n in need)

        def match_rarity(value: str) -> bool:
            if not rarities_set:
                return True
            v = (value or '').replace('★','').strip()
            return v in rarities_set

        for row in filter_data:
            name = row.get('zh') or row.get('name')
            if not name:
                continue
            if keyword and (keyword not in name):
                continue
            # 字段同义与标准化
            branch_val = row.get('branch') or row.get('subprofession') or ''
            gender_val = row.get('gender') or row.get('sex') or ''
            obtain_val = row.get('obtain') or row.get('obtain_method') or ''
            tags_val = row.get('tags') or row.get('tag') or ''
            faction_val = row.get('logo') or row.get('group') or row.get('nation') or ''
            rarity_raw = (row.get('rarity') or '').strip()
            rarity_star = ''
            if rarity_raw.isdigit():
                try:
                    rarity_star = str(int(rarity_raw) + 1)
                except Exception:
                    rarity_star = rarity_raw
            else:
                rarity_star = rarity_raw
            if not (match_contains(row.get('profession',''), professions_set) and
                    match_contains(branch_val, branches_set) and
                    ((not rarities_set) or rarity_star in rarities_set) and
                    match_contains(row.get('position',''), positions_set) and
                    match_contains(gender_val, genders_set) and
                    match_contains(obtain_val, obtains_set) and
                    match_contains(tags_val, tags_set) and
                    match_contains(faction_val, factions_set) and
                    match_contains(row.get('birth_place',''), birthplaces_set) and
                    match_contains(row.get('race',''), races_set)):
                continue
            filtered.append({
                'title': name,
                'profession': row.get('profession'),
                'branch': branch_val,
                'rarity': rarity_star,
                'position': row.get('position'),
                'gender': gender_val,
                'obtain': obtain_val,
                'tags': tags_val,
                'faction': faction_val,
                'birthplace': row.get('birth_place'),
                'race': row.get('race'),
                'url': row.get('url'),
            })

        # 2) 若 filter-data 不可用或结果为空，回退到逐页验证的旧策略
        candidates = [{'title': f.get('title')} for f in filtered] if filtered else []
        if not filtered:
            # 构造简单查询扩大覆盖
            search_terms = set([keyword] if keyword else [])
            for s in [professions_set, branches_set, tags_set, factions_set]:
                search_terms.update(s)
            if not search_terms:
                search_terms.add('干员')
            seen = set()
            for term in search_terms:
                for res in await wiki_client.search_pages(f"{term} 干员", limit=50):
                    t = res['title']
                    if any(x in t for x in ['/','：','列表','一览']):
                        continue
                    if t in seen:
                        continue
                    candidates.append({'title': t})
                    seen.add(t)

            # 验证候选并抽取字段
            semaphore = asyncio.Semaphore(8)
            async def verify(title: str):
                async with semaphore:
                    if not await wiki_client._verify_operator_page(title):
                        return None
                    data = await wiki_client.parse_operator_complete(title)
                    return data
            pages = await asyncio.gather(*(verify(c['title']) for c in candidates))
            for data in filter(None, pages):
                profession = data.get('profession','')
                rarity_text = data.get('rarity','')
                import re as _re
                m = _re.search(r'(\d+)', rarity_text or '')
                rarity_num = m.group(1) if m else ''
                basic = data.get('basic_info',{}) or {}
                row = {
                    'title': data.get('name'),
                    'profession': profession,
                    'branch': basic.get('分支',''),
                    'rarity': rarity_num or rarity_text,
                    'position': basic.get('位置',''),
                    'gender': basic.get('性别',''),
                    'obtain': basic.get('获得方式',''),
                    'tags': ' '.join([basic.get('标签',''), basic.get('词缀','')]).strip(),
                    'faction': basic.get('所属势力',''),
                    'birthplace': basic.get('出身地',''),
                    'race': basic.get('种族',''),
                    'url': data.get('url')
                }
                def ok():
                    return (
                        match_contains(row['profession'], professions_set) and
                        match_contains(row['branch'], branches_set) and
                        ((not rarities_set) or str(row['rarity']).replace('★','') in rarities_set) and
                        match_contains(row['position'], positions_set) and
                        match_contains(row['gender'], genders_set) and
                        match_contains(row['obtain'], obtains_set) and
                        match_contains(row['tags'], tags_set) and
                        match_contains(row['faction'], factions_set) and
                        match_contains(row['birthplace'], birthplaces_set) and
                        match_contains(row['race'], races_set)
                    )
                if ok():
                    filtered.append(row)
 
        if not filtered:
            conds = []
            if professions_set: conds.append(f"职业={','.join(professions_set)}")
            if branches_set: conds.append(f"分支={','.join(branches_set)}")
            if rarities_set: conds.append(f"稀有度={','.join(sorted(rarities_set))}")
            if positions_set: conds.append(f"位置={','.join(positions_set)}")
            if genders_set: conds.append(f"性别={','.join(genders_set)}")
            if obtains_set: conds.append(f"获得方式={','.join(obtains_set)}")
            if tags_set: conds.append(f"标签={','.join(tags_set)}")
            if factions_set: conds.append(f"势力={','.join(factions_set)}")
            if birthplaces_set: conds.append(f"出身地={','.join(birthplaces_set)}")
            if races_set: conds.append(f"种族={','.join(races_set)}")
            return (
                "# 🔍 干员多维筛选\n\n"
                f"- **匹配数量**: 0\n- **条件**: {'; '.join(conds) if conds else '无'}\n"
                "- 如需更精准结果，可减少条件或放宽关键词。\n"
            )

        # 排序：默认按稀有度降序，再按职业、名称
        def sort_key(item: dict):
            try:
                r = int(str(item.get('rarity') or 0).replace('★',''))
            except Exception:
                r = 0
            return (-r, item.get('profession', ''), item.get('title', ''))
        filtered.sort(key=sort_key)

        # 输出格式
        lines = [
            "# 🔎 干员多维筛选结果",
            "",
            "## 📊 统计",
            f"- **候选数据**: {len(filter_data) if 'filter_data' in locals() and filter_data else 0}",
            f"- **匹配干员**: {len(filtered)}",
        ]
        if keyword:
            lines.append(f"- **关键词**: {keyword}")

        lines.append("\n## 📋 干员列表")
        for idx, op in enumerate(filtered[:limit], 1):
            parts = [f"{idx:2d}. **{op['title']}**"]
            meta = []
            if op.get('rarity'): meta.append(f"{op['rarity']}★")
            if op.get('profession'): meta.append(op['profession'])
            if op.get('branch'): meta.append(op['branch'])
            if meta:
                parts.append(f"（{' / '.join(meta)}）")
            if op.get('tags'):
                parts.append(f" - {op['tags']}")
            if op.get('url'):
                parts.append(f"\n   链接: {op['url']}")
            lines.append(''.join(parts))

        lines.append("\n---\n数据来源: https://prts.wiki/w/干员一览")
        return "\n".join(lines)

    except Exception as e:
        return (
            "# ❌ 干员多维筛选错误\n\n"
            f"- **错误信息**: {str(e)}\n"
        )
    finally:
        if not client_provided:
            await wiki_client.close() 


 