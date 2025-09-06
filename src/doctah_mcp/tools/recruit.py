#!/usr/bin/env python3
"""
公招计算（公开招募标签匹配）

参考 PRTS『公招计算』页面的数据来源，通过 cargoquery 拉取可公招干员与其标签，
根据给定的筛选词条（资历/职业/位置/词缀）返回可能出现的干员列表。

数据来源示例（与前端一致）：
- /api.php?action=cargoquery&format=json&tables=chara,char_obtain&limit=5000
  &fields=chara.profession,chara.position,chara.rarity,chara.tag,chara.cn,char_obtain.obtainMethod
  &where=char_obtain.obtainMethod like "%公开 招募%" AND chara.charIndex>0
  &join_on=chara._pageName=char_obtain._pageName
"""

import asyncio
from typing import Dict, List, Optional
from urllib.parse import quote

from ..client import PRTSWikiClient
from .utils import BASE_URL

# 常量（与页面一致）
PROFESSIONS = ["近卫", "狙击", "重装", "医疗", "辅助", "术师", "特种", "先锋"]
POSITIONS = ["近战位", "远程位"]
RARITY_TAGS = ["高级资深干员", "资深干员", "新手"]  # 注意："新手"在 chara.tag 字段中出现
TAG_WORDS = [
    "支援机械", "控场", "爆发", "治疗", "支援", "费用回复", "输出", "生存",
    "群攻", "防护", "减速", "削弱", "快速复活", "位移", "召唤", "元素",
]

# 别名归一
PROF_ALIASES = {
    "近卫干员": "近卫", "狙击干员": "狙击", "重装干员": "重装", "医疗干员": "医疗",
    "辅助干员": "辅助", "术师干员": "术师", "特种干员": "特种", "先锋干员": "先锋",
}
POS_ALIASES = {"近战": "近战位", "远程": "远程位", "近战位": "近战位", "远程位": "远程位"}
RARITY_ALIASES = {"高资": "高级资深干员", "高资深": "高级资深干员", "资深": "资深干员", "资深干员": "资深干员", "新手干员": "新手"}
TAG_ALIASES = {"费用回收": "费用回复"}


def _split_terms(terms: Optional[str]) -> List[str]:
    if not terms:
        return []
    text = terms
    for sep in [",", "，", "、", "|", " "]:
        text = text.replace(sep, ",")
    tokens = [t.strip() for t in text.split(",") if t.strip()]
    # 归一映射
    normed = []
    for t in tokens:
        t2 = RARITY_ALIASES.get(t, PROF_ALIASES.get(t, POS_ALIASES.get(t, TAG_ALIASES.get(t, t))))
        # 去掉“干员”后缀（兜底）
        if t2.endswith("干员"):
            t2 = t2[:-2]
        normed.append(t2)
    return normed


def _classify_terms(terms: List[str]):
    """将词条按类别拆分：职业/位置/资历tag/词缀。"""
    pros, poss, rars, tags = set(), set(), set(), []
    for t in terms:
        if t in PROFESSIONS:
            pros.add(t)
        elif t in POSITIONS or t in POS_ALIASES.values():
            poss.add(POS_ALIASES.get(t, t))
        elif t in RARITY_TAGS or t in RARITY_ALIASES.values():
            rars.add(RARITY_ALIASES.get(t, t))
        elif t in TAG_WORDS or t in TAG_ALIASES.values():
            tags.append(TAG_ALIASES.get(t, t))
        else:
            # 未识别词条尝试去掉“干员”后缀再匹配
            if t.endswith("干员") and t[:-2] in PROFESSIONS:
                pros.add(t[:-2])
            else:
                tags.append(t)  # 当作普通词缀尝试
    return pros, poss, rars, tags


async def recruit_by_tags(terms: str, wiki_client: Optional[PRTSWikiClient] = None) -> str:
    """
    给定词条（以逗号/顿号/空格/竖线分隔），返回可能出现的公招干员。
    支持维度：资历(高级资深干员/资深干员/新手)、职业、位置、词缀（如 输出/治疗/费用回复 等）。
    同一类别内为“或”匹配（职业/位置/资历），词缀为“且”匹配。
    """
    selected = _split_terms(terms)
    if not selected:
        return (
            "# ❌ 公招计算失败\n\n"
            "- **状态**: 缺少筛选词条\n"
            "- **示例**: 资深干员, 术师, 群攻 或 先锋 费用回复\n"
        )

    pros, poss, rars, tag_need = _classify_terms(selected)

    client_provided = wiki_client is not None
    if not wiki_client:
        wiki_client = PRTSWikiClient()

    try:
        # 拉取可公开招募的干员数据
        params = {
            "action": "cargoquery",
            "format": "json",
            "tables": "chara,char_obtain",
            "limit": "5000",
            "fields": "chara.profession,chara.position,chara.rarity,chara.tag,chara.cn,char_obtain.obtainMethod",
            "where": 'char_obtain.obtainMethod like "%公开%招募%" AND chara.charIndex>0',
            "join_on": "chara._pageName=char_obtain._pageName",
        }
        resp = await wiki_client.session.get(f"{BASE_URL}/api.php", params=params)
        resp.raise_for_status()
        data = resp.json().get("cargoquery", [])

        candidates: List[Dict] = []
        for item in data:
            title = item.get("title", {})
            name = title.get("cn")
            if not name:
                continue
            rarity_num = int(title.get("rarity", "0") or 0)  # 0..5
            tags = (title.get("tag") or "").split(" ") if title.get("tag") else []
            obtain = (title.get("obtainMethod") or "").split(" ") if title.get("obtainMethod") else []
            # 资历标签
            rarity_tag = "高级资深干员" if rarity_num == 5 else ("资深干员" if rarity_num == 4 else None)

            # OR 匹配：职业/位置/资历
            if pros and (title.get("profession") not in pros):
                continue
            if poss and (title.get("position") not in poss):
                continue
            if rars and (rarity_tag not in rars):
                continue
            # AND 匹配：词缀
            if tag_need and not set(tag_need).issubset(set(tags)):
                continue

            candidates.append({
                "name": name,
                "rarity": rarity_num + 1,
                "profession": title.get("profession", ""),
                "position": title.get("position", ""),
                "tags": tags,
                "obtain": obtain,
                "rarity_tag": rarity_tag or "",
                "hit_tags": [t for t in tag_need if t in tags],
                "url": f"{BASE_URL}/w/{quote(name)}",
            })

        if not candidates:
            # 返回诊断信息
            diag = []
            if pros: diag.append(f"职业∈{','.join(pros)}")
            if poss: diag.append(f"位置∈{','.join(poss)}")
            if rars: diag.append(f"资历∈{','.join(rars)}")
            if tag_need: diag.append(f"词缀⊇{','.join(tag_need)}")
            return (
                "# 🔍 公招计算\n\n"
                f"- **匹配数量**: 0\n- **词条**: {', '.join(selected)}\n"
                f"- **筛选条件**: {'；'.join(diag) if diag else '无'}\n"
                "- 可能原因：\n  1) 选择了互斥职业；2) 词缀组合过于苛刻（如“元素”当前公开招募中基本不存在）；3) 词条拼写或别名不一致。\n"
            )

        candidates.sort(key=lambda x: (-x["rarity"], x["profession"], x["name"]))
        groups: Dict[int, List[Dict]] = {}
        for c in candidates:
            groups.setdefault(c["rarity"], []).append(c)

        lines = [
            "# 🎯 公招计算结果",
            "",
            f"- **词条**: {', '.join(selected)}",
            f"- **匹配干员**: {len(candidates)}",
            "",
        ]
        for rarity in sorted(groups.keys(), reverse=True):
            lines.append(f"## {rarity}★")
            for op in groups[rarity]:
                meta = [op["profession"], op["position"], " ".join(op["tags"])[:60]]
                meta = [m for m in meta if m]
                lines.append(f"- **{op['name']}**（{' / '.join(meta)}）")
                # 匹配依据
                reason = []
                if op.get("profession"): reason.append(f"职业={op['profession']}")
                if op.get("position"): reason.append(f"位置={op['position']}")
                if op.get("rarity_tag"): reason.append(f"资历={op['rarity_tag']}")
                if op.get("hit_tags"): reason.append(f"词缀命中={','.join(op['hit_tags'])}")
                if reason:
                    lines.append(f"  匹配依据: {'；'.join(reason)}")
                lines.append(f"  链接: {op['url']}")
            lines.append("")

        lines.append("---")
        lines.append("数据来源: 公招计算 / cargoquery")
        return "\n".join(lines)

    except Exception as e:
        return f"# ❌ 公招计算错误\n\n- **错误信息**: {e}"
    finally:
        if not client_provided:
            await wiki_client.close()


def _build_universe():
    """返回与前端一致的并集顺序与索引映射。"""
    R = PROFESSIONS + POSITIONS + RARITY_TAGS + TAG_WORDS
    idx = {name: i for i, name in enumerate(R)}
    return R, idx


def _bits_set(indices: List[int]) -> int:
    v = 0
    for i in indices:
        v |= (1 << i)
    return v


def _subset_bitsets(bitmask: int) -> List[int]:
    """返回 bitmask 的所有非空子集位图。"""
    bits = []
    i = 0
    while (1 << i) <= bitmask:
        if bitmask & (1 << i):
            bits.append(i)
        i += 1
    res = []
    total = 1 << len(bits)
    for s in range(1, total):
        v = 0
        for j, bi in enumerate(bits):
            if s & (1 << j):
                v |= (1 << bi)
        res.append(v)
    return res


async def recruit_by_tags_all(terms: str, wiki_client: Optional[PRTSWikiClient] = None) -> str:
    """
    严格使用所有词条（AND）：只有当干员具备“所有给定词条”时才会命中。
    词条统一使用职业/位置/资历/词缀全集，无“或”逻辑。
    """
    selected = _split_terms(terms)
    if not selected:
        return "# ❌ 公招计算（严格）\n\n- **状态**: 缺少词条"
    R, IDX = _build_universe()
    need_bits = 0
    for t in selected:
        if t in IDX:
            need_bits |= (1 << IDX[t])
    client_provided = wiki_client is not None
    if not wiki_client:
        wiki_client = PRTSWikiClient()
    try:
        params = {
            "action": "cargoquery",
            "format": "json",
            "tables": "chara,char_obtain",
            "limit": "5000",
            "fields": "chara.profession,chara.position,chara.rarity,chara.tag,chara.cn,char_obtain.obtainMethod",
            "where": 'char_obtain.obtainMethod like "%公开%招募%" AND chara.charIndex>0',
            "join_on": "chara._pageName=char_obtain._pageName",
        }
        resp = await wiki_client.session.get(f"{BASE_URL}/api.php", params=params)
        resp.raise_for_status()
        data = resp.json().get("cargoquery", [])

        hits = []
        for item in data:
            t = item.get("title", {})
            name = t.get("cn")
            if not name:
                continue
            star = int(t.get("rarity", 0)) + 1
            profession = t.get("profession", "")
            position = t.get("position", "")
            tags = (t.get("tag") or "").split(" ") if t.get("tag") else []
            rarity_tag = "高级资深干员" if star == 6 else ("资深干员" if star == 5 else None)
            op_bits = 0
            if profession in IDX: op_bits |= (1 << IDX[profession])
            if position in IDX: op_bits |= (1 << IDX[position])
            if rarity_tag and rarity_tag in IDX: op_bits |= (1 << IDX[rarity_tag])
            for tg in tags:
                if tg in IDX: op_bits |= (1 << IDX[tg])
            if (op_bits & need_bits) == need_bits:
                hits.append({
                    "name": name,
                    "star": star,
                    "profession": profession,
                    "position": position,
                    "tags": tags,
                    "url": f"{BASE_URL}/w/{quote(name)}",
                })

        if not hits:
            return (
                "# 🔍 公招计算（严格）\n\n"
                f"- **词条**: {', '.join(selected)}\n- **匹配数量**: 0\n"
                "- 提示：若包含互斥职业/位置，将导致必然为空。\n"
            )

        hits.sort(key=lambda x: (-x["star"], x["profession"], x["name"]))
        lines = ["# 🎯 公招计算结果（严格使用全部词条）", "", f"- **词条**: {', '.join(selected)}", f"- **匹配干员**: {len(hits)}", ""]
        for h in hits:
            meta = [f"{h['star']}★", h['profession'], h['position']]
            lines.append(f"- **{h['name']}**（{' / '.join([m for m in meta if m])}）")
            lines.append(f"  链接: {h['url']}")
        return "\n".join(lines)
    except Exception as e:
        return f"# ❌ 公招计算（严格）错误\n\n- **错误信息**: {e}"
    finally:
        if not client_provided:
            await wiki_client.close()


async def recruit_by_tags_suggest(terms: str, top_k: int = 10, wiki_client: Optional[PRTSWikiClient] = None) -> str:
    """
    自动寻找“能出结果”的最佳子集组合（不要求用完所有词条）。
    - 评分：先按平均星级，再按命中数量排序，取前 top_k 个组合。
    - 6★ 组合仅在包含“高级资深干员”时显示。
    """
    selected = _split_terms(terms)
    if not selected:
        return "# ❌ 公招计算（建议组合）\n\n- **状态**: 缺少词条"
    R, IDX = _build_universe()
    sel_bits = 0
    for t in selected:
        if t in IDX:
            sel_bits |= (1 << IDX[t])
    client_provided = wiki_client is not None
    if not wiki_client:
        wiki_client = PRTSWikiClient()
    try:
        params = {
            "action": "cargoquery",
            "format": "json",
            "tables": "chara,char_obtain",
            "limit": "5000",
            "fields": "chara.profession,chara.position,chara.rarity,chara.tag,chara.cn,char_obtain.obtainMethod",
            "where": 'char_obtain.obtainMethod like "%公开%招募%" AND chara.charIndex>0',
            "join_on": "chara._pageName=char_obtain._pageName",
        }
        resp = await wiki_client.session.get(f"{BASE_URL}/api.php", params=params)
        resp.raise_for_status()
        data = resp.json().get("cargoquery", [])

        groups: Dict[int, Dict] = {}
        HIGH = IDX.get("高级资深干员", -1)
        for item in data:
            t = item.get("title", {})
            name = t.get("cn")
            if not name:
                continue
            star = int(t.get("rarity", 0)) + 1
            profession = t.get("profession", "")
            position = t.get("position", "")
            tags = (t.get("tag") or "").split(" ") if t.get("tag") else []
            rarity_tag = "高级资深干员" if star == 6 else ("资深干员" if star == 5 else None)
            op_bits = 0
            if profession in IDX: op_bits |= (1 << IDX[profession])
            if position in IDX: op_bits |= (1 << IDX[position])
            if rarity_tag and rarity_tag in IDX: op_bits |= (1 << IDX[rarity_tag])
            for tg in tags:
                if tg in IDX: op_bits |= (1 << IDX[tg])
            for subset in _subset_bitsets(op_bits):
                if (sel_bits | subset) != sel_bits:
                    continue
                if star == 6 and HIGH >= 0 and not (subset & (1 << HIGH)):
                    continue
                g = groups.setdefault(subset, {"ops": [], "stars": []})
                g["ops"].append({"name": name, "star": star, "profession": profession, "position": position, "url": f"{BASE_URL}/w/{quote(name)}"})
                g["stars"].append(star)

        if not groups:
            return (
                "# 🔍 公招计算（建议组合）\n\n"
                f"- **词条**: {', '.join(selected)}\n- 没有能产生结果的组合\n"
            )

        def score(item):
            subset, g = item
            avg = sum(g["stars"]) / max(1, len(g["stars"]))
            return (avg, len(g["ops"]))
        ordered = sorted(groups.items(), key=score, reverse=True)[:top_k]

        def names(subset: int) -> List[str]:
            out = []
            i = 0
            while (1 << i) <= subset:
                if subset & (1 << i):
                    out.append(R[i])
                i += 1
            return out

        lines = ["# 🎯 公招计算建议组合", "", f"- **词条**: {', '.join(selected)}", f"- **组合数**: {len(ordered)}", ""]
        for subset, g in ordered:
            title = "+".join(names(subset))
            avg = sum(g["stars"]) / max(1, len(g["stars"]))
            lines.append(f"## {title}  — 平均星级≈{avg:.2f}，人数={len(g['ops'])}")
            for op in sorted(g["ops"], key=lambda x: (-x["star"], x["profession"], x["name"])):
                lines.append(f"- **{op['name']}**（{op['star']}★ / {op['profession']} / {op['position']}）")
                lines.append(f"  链接: {op['url']}")
            lines.append("")
        lines.append("---")
        lines.append("数据来源: 公招计算 / cargoquery（建议组合）")
        return "\n".join(lines)
    except Exception as e:
        return f"# ❌ 公招计算（建议组合）错误\n\n- **错误信息**: {e}"
    finally:
        if not client_provided:
            await wiki_client.close()


async def recruit_by_tags_grouped(terms: str, wiki_client: Optional[PRTSWikiClient] = None) -> str:
    """
    按网页逻辑将结果按“所选词条的子集组合”进行分组展示。

    - 输入：同 recruit_by_tags 的 terms
    - 分组：将每位干员的(职业/位置/资历/词缀)形成位图，枚举其所有非空子集；
      若该子集完全包含在“所选词条位图”内，则将该干员计入该子集的分组。
      对于 6★ 干员，仅当子集包含“高级资深干员”时才计入（与前端一致）。
    - 排序：按各组平均星级由高到低，再按组内人数由多到少。
    """
    selected = _split_terms(terms)
    pros, poss, rars, tag_need = _classify_terms(selected)
    R, IDX = _build_universe()

    # 所选词条位图
    selected_bits = 0
    for t in selected:
        if t in IDX:
            selected_bits |= (1 << IDX[t])

    client_provided = wiki_client is not None
    if not wiki_client:
        wiki_client = PRTSWikiClient()

    try:
        params = {
            "action": "cargoquery",
            "format": "json",
            "tables": "chara,char_obtain",
            "limit": "5000",
            "fields": "chara.profession,chara.position,chara.rarity,chara.tag,chara.cn,char_obtain.obtainMethod",
            "where": 'char_obtain.obtainMethod like "%公开%招募%" AND chara.charIndex>0',
            "join_on": "chara._pageName=char_obtain._pageName",
        }
        resp = await wiki_client.session.get(f"{BASE_URL}/api.php", params=params)
        resp.raise_for_status()
        data = resp.json().get("cargoquery", [])

        groups: Dict[int, Dict] = {}
        def star_from_rarity(rn: int) -> int:
            return int(rn) + 1

        HIGH_TAG_BIT = IDX.get("高级资深干员", -1)

        for item in data:
            t = item.get("title", {})
            name = t.get("cn")
            if not name:
                continue
            rarity_num = int(t.get("rarity", "0") or 0)
            star = star_from_rarity(rarity_num)
            profession = t.get("profession", "")
            position = t.get("position", "")
            tags = (t.get("tag") or "").split(" ") if t.get("tag") else []
            rarity_tag = "高级资深干员" if star == 6 else ("资深干员" if star == 5 else None)

            # 构建干员位图
            op_bits = 0
            if profession in IDX: op_bits |= (1 << IDX[profession])
            if position in IDX: op_bits |= (1 << IDX[position])
            if rarity_tag and rarity_tag in IDX: op_bits |= (1 << IDX[rarity_tag])
            for tg in tags:
                if tg in IDX:
                    op_bits |= (1 << IDX[tg])

            # 生成所有非空子集
            for subset in _subset_bitsets(op_bits):
                # 子集需完全包含在所选词条中
                if (selected_bits | subset) != selected_bits:
                    continue
                # 6★ 仅当子集包含 高级资深干员
                if star == 6 and HIGH_TAG_BIT is not None and HIGH_TAG_BIT >= 0:
                    if not (subset & (1 << HIGH_TAG_BIT)):
                        continue
                # 记录
                g = groups.setdefault(subset, {"ops": [], "stars": []})
                g["ops"].append({
                    "name": name,
                    "star": star,
                    "profession": profession,
                    "position": position,
                    "tags": tags,
                    "url": f"{BASE_URL}/w/{quote(name)}",
                })
                g["stars"].append(star)

        if not groups:
            return (
                "# 🔍 公招计算（分组）\n\n"
                f"- **词条**: {', '.join(selected) if selected else '无'}\n"
                "- 暂无可匹配分组（可能是词缀过于苛刻或未选择任何可分组的词条）。\n"
            )

        # 排序分组
        def group_score(item):
            subset, g = item
            avg = sum(g["stars"]) / max(1, len(g["stars"]))
            return (avg, len(g["ops"]))

        ordered = sorted(groups.items(), key=group_score, reverse=True)

        # 渲染
        def subset_to_names(subset: int) -> List[str]:
            names = []
            i = 0
            while (1 << i) <= subset:
                if subset & (1 << i):
                    names.append(R[i])
                i += 1
            return names

        lines = ["# 🎯 公招计算结果（分组）", "", f"- **词条**: {', '.join(selected)}", ""]
        for subset, g in ordered:
            title = "+".join(subset_to_names(subset)) or "(未命名子集)"
            lines.append(f"## {title}")
            # 列表：按星级降序
            ops_sorted = sorted(g["ops"], key=lambda x: (-x["star"], x["profession"], x["name"]))
            for op in ops_sorted:
                meta = [f"{op['star']}★", op["profession"], op["position"]]
                lines.append(f"- **{op['name']}**（{' / '.join([m for m in meta if m])}）")
                lines.append(f"  链接: {op['url']}")
            lines.append("")

        lines.append("---")
        lines.append("数据来源: 公招计算 / cargoquery（分组逻辑与前端一致）")
        return "\n".join(lines)

    except Exception as e:
        return f"# ❌ 公招计算（分组）错误\n\n- **错误信息**: {e}"
    finally:
        if not client_provided:
            await wiki_client.close() 