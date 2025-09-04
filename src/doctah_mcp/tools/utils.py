#!/usr/bin/env python3
"""
PRTS.wiki 工具函数模块
提供通用的辅助函数
"""

from typing import Dict, List, Optional

# PRTS.wiki 基础配置
BASE_URL = "https://prts.wiki"

def _create_operator_not_found_response(name: str, similar_names: List[str] = None) -> str:
    """创建标准化的"干员不存在"响应"""
    response = f"""# ❌ 干员查询失败

## 🔍 查询状态
- **状态**: 干员不存在
- **查询名称**: {name}
- **错误类型**: OPERATOR_NOT_FOUND

## 📋 可能的原因
1. **拼写错误**: 请检查干员名称的拼写
2. **名称不完整**: 一些干员需要完整名称（如"阿米娅（医疗）"）
3. **干员不存在**: 该名称可能不是有效的明日方舟干员

## 🎯 建议操作"""
    
    if similar_names:
        response += f"""
### 相似干员名称建议：
"""
        for i, similar_name in enumerate(similar_names, 1):
            response += f"{i}. {similar_name}\n"
    else:
        response += """
1. 检查干员名称拼写
2. 尝试使用完整干员名称
3. 查看 PRTS.wiki 确认干员是否存在
"""
    
    response += f"""
## 🔗 相关链接
- [PRTS.wiki 干员列表](https://prts.wiki/w/干员一览)
- [PRTS.wiki 首页]({BASE_URL})

---
💡 **提示**: 这是一个标准化的"干员不存在"响应，AI助手可以据此判断查询失败的原因。
"""
    
    return response


def _extract_similar_operator_names(search_results: List[Dict[str, str]], target_name: str) -> List[str]:
    """从搜索结果中提取相似的干员名称"""
    similar_names = []
    target_lower = target_name.lower()
    
    for result in search_results:
        title = result['title']
        # 过滤掉非干员页面
        if any(exclude in title for exclude in ['/干员密录', '/语音记录', '/干员模型', '/悖论模拟', '/', '：']):
            continue
        
        # 查找包含职业标识的干员名称
        if any(prof in title for prof in ['（医疗）', '（术师）', '（狙击）', '（重装）', '（近卫）', '（先锋）', '（辅助）', '（特种）']):
            similar_names.append(title)
        # 或者是与目标名称相似的干员
        elif title.lower() != target_lower and len(title) <= 10:  # 避免太长的标题
            similar_names.append(title)
        
        # 最多返回5个建议
        if len(similar_names) >= 5:
            break
    
    return similar_names

