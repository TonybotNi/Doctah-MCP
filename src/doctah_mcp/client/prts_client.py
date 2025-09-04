#!/usr/bin/env python3
"""
PRTS.wiki 查询功能模块
提供明日方舟 PRTS.wiki 网站的数据查询和解析功能
"""

import asyncio
import logging
from typing import Dict, List, Any, Optional
from urllib.parse import quote, unquote
import httpx
from bs4 import BeautifulSoup, Comment
import re

# 配置日志
logger = logging.getLogger(__name__)

# PRTS.wiki 基础配置
BASE_URL = "https://prts.wiki"
SEARCH_API = f"{BASE_URL}/api.php"



class PRTSWikiClient:
    """PRTS.wiki 客户端"""
    
    def __init__(self):
        self.session = httpx.AsyncClient(
            timeout=httpx.Timeout(30.0),
            headers={
                "User-Agent": "PRTS-MCP-Server/1.0 (https://github.com/example/prts-mcp)"
            }
        )
    
    async def close(self):
        """关闭HTTP会话"""
        await self.session.aclose()
    
    async def search_pages(self, query: str, limit: int = 10) -> List[Dict[str, str]]:
        """搜索页面"""
        try:
            params = {
                "action": "query",
                "format": "json",
                "list": "search",
                "srsearch": query,
                "srlimit": limit,
                "srprop": "title|snippet"
            }
            
            response = await self.session.get(SEARCH_API, params=params)
            response.raise_for_status()
            data = response.json()
            
            results = []
            if "query" in data and "search" in data["query"]:
                for item in data["query"]["search"]:
                    results.append({
                        "title": item["title"],
                        "snippet": item.get("snippet", ""),
                        "url": f"{BASE_URL}/w/{quote(item['title'])}"
                    })
            
            return results
            
        except Exception as e:
            logger.error(f"搜索页面失败: {e}")
            return []
    
    async def get_page_html(self, title: str) -> str:
        """获取页面HTML内容"""
        try:
            url = f"{BASE_URL}/w/{quote(title)}"
            response = await self.session.get(url)
            response.raise_for_status()
            return response.text
        except Exception as e:
            logger.error(f"获取页面HTML失败: {e}")
            return ""
    
    async def get_page_content(self, title: str) -> str:
        """获取页面纯文本内容"""
        try:
            params = {
                "action": "query",
                "format": "json",
                "titles": title,
                "prop": "extracts",
                "exintro": False,
                "explaintext": True,
                "exsectionformat": "plain"
            }
            
            response = await self.session.get(SEARCH_API, params=params)
            response.raise_for_status()
            data = response.json()
            
            pages = data.get("query", {}).get("pages", {})
            for page_id, page_data in pages.items():
                if "extract" in page_data:
                    return page_data["extract"]
            
            return ""
            
        except Exception as e:
            logger.error(f"获取页面内容失败: {e}")
            return ""

    def extract_text_from_cell(self, cell) -> str:
        """从表格单元格中提取纯文本，清理HTML标签和特殊标记"""
        if not cell:
            return ""
        
        # 移除注释
        for comment in cell.find_all(string=lambda text: isinstance(text, Comment)):
            comment.extract()
        
        # 移除script和style标签
        for tag in cell.find_all(['script', 'style']):
            tag.decompose()
        
        # 移除特定的span标签（算法标记等）
        try:
            for span in cell.find_all('span'):
                if span and hasattr(span, 'get') and span.get('style'):
                    style = span.get('style', '')
                    if style and 'display:none' in style:
                        span.decompose()
        except Exception:
            pass  # 忽略处理span标签时的错误
        
        # 获取文本
        text = cell.get_text(separator=' ', strip=True)
        
        # 清理特殊标记
        text = re.sub(r'显示算法.*?(?=\s|$)', '', text)
        text = re.sub(r'直接乘算.*?(?=\s|$)', '', text)
        text = re.sub(r'里属于叠加.*?(?=\s|$)', '', text)
        text = re.sub(r'为.*?乘算', '', text)
        text = re.sub(r'\[\s*注\s*\d+\s*\]', '', text)  # 移除注释标记
        text = re.sub(r'\s+', ' ', text)  # 合并多个空格
        text = re.sub(r'^\s*：\s*', '', text)  # 移除开头的冒号
        
        return text.strip()

    def extract_table_of_contents(self, soup: BeautifulSoup) -> Dict[str, Dict]:
        """提取页面目录结构"""
        toc = {}
        
        # 查找目录容器
        toc_div = soup.find('div', {'id': 'toc'}) or soup.find('div', class_='toc')
        
        if toc_div:
            # 从目录中提取
            for link in toc_div.find_all('a'):
                href = link.get('href', '')
                if href.startswith('#'):
                    section_id = href[1:]
                    section_title = link.get_text(strip=True)
                    toc[section_id] = {
                        'title': section_title,
                        'level': len(link.find_parents('li', recursive=False)),
                        'anchor': section_id
                    }
        else:
            # 从标题中提取目录
            for heading in soup.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'h6']):
                if heading.get('id'):
                    section_id = heading.get('id')
                    section_title = heading.get_text(strip=True)
                    level = int(heading.name[1])  # h1->1, h2->2, etc.
                    toc[section_id] = {
                        'title': section_title,
                        'level': level,
                        'anchor': section_id
                    }
        
        return toc

    def extract_section_content(self, soup: BeautifulSoup, section_id: str, next_section_id: str = None) -> str:
        """提取指定章节的内容"""
        content = []
        
        # 找到章节标题
        section_heading = soup.find(id=section_id)
        if not section_heading:
            return ""
        
        # 如果不是标题标签，查找其父级标题
        if section_heading.name not in ['h1', 'h2', 'h3', 'h4', 'h5', 'h6']:
            section_heading = section_heading.find_parent(['h1', 'h2', 'h3', 'h4', 'h5', 'h6'])
        
        if not section_heading:
            return ""
        
        # 获取下一个同级或更高级的标题作为边界
        current_level = int(section_heading.name[1])
        next_element = section_heading.next_sibling
        
        while next_element:
            if hasattr(next_element, 'name'):
                if next_element.name in ['h1', 'h2', 'h3', 'h4', 'h5', 'h6']:
                    next_level = int(next_element.name[1])
                    if next_level <= current_level:
                        break
                
                # 提取表格内容
                if next_element.name == 'table':
                    table_content = self.extract_table_content(next_element)
                    if table_content:
                        content.append(table_content)
                
                # 提取其他内容
                elif next_element.name in ['p', 'div', 'ul', 'ol', 'dl']:
                    text = self.extract_text_from_cell(next_element)
                    if text:
                        content.append(text)
            
            next_element = next_element.next_sibling
        
        return '\n\n'.join(content) if content else ""

    def extract_table_content(self, table) -> str:
        """提取表格内容为markdown格式"""
        if not table:
            return ""
        
        content = []
        rows = table.find_all('tr')
        
        for row in rows:
            cells = row.find_all(['th', 'td'])
            if cells:
                row_data = []
                for cell in cells:
                    cell_text = self.extract_text_from_cell(cell)
                    row_data.append(cell_text)
                
                if any(row_data):  # 只有当行中有内容时才添加
                    content.append(' | '.join(row_data))
        
        return '\n'.join(content) if content else ""

    async def parse_operator_complete(self, title: str, sections: Optional[List[str]] = None) -> Dict[str, Any]:
        """完整解析干员信息，支持章节过滤"""
        html = await self.get_page_html(title)
        if not html:
            return {}
        
        soup = BeautifulSoup(html, 'html.parser')
        
        # 检查是否为敌人页面
        if self._is_enemy_page(soup, title):
            return {
                'type': 'enemy',
                'name': title,
                'url': f"{BASE_URL}/w/{quote(title)}",
                'message': '该页面为敌人页面，请使用敌人查询功能'
            }
        
        # 提取目录结构
        toc = self.extract_table_of_contents(soup)
        
        # 基础数据结构
        operator_data = {
            'type': 'operator',
            'name': title,
            'url': f"{BASE_URL}/w/{quote(title)}",
            'table_of_contents': toc,
            'sections': {}
        }
        
        # 定义章节映射
        section_mapping = {
            '干员信息': 'operator_info',
            '特性': 'characteristics', 
            '获得方式': 'acquisition',
            '属性': 'attributes',
            '攻击范围': 'attack_range',
            '天赋': 'talents',
            '潜能提升': 'potential',
            '技能': 'skills',
            '后勤技能': 'base_skills',
            '精英化材料': 'elite_materials',
            '技能升级材料': 'skill_materials',
            '模组': 'modules',
            '相关道具': 'related_items',
            '干员档案': 'operator_record',
            '语音记录': 'voice_records',
            '干员密录': 'operator_files',
            '悖论模拟': 'paradox_simulation',
            '干员模型': 'operator_model',
            '注释与链接': 'notes_and_links'
        }
        
        try:
            # 如果指定了章节，只解析指定章节
            if sections:
                target_sections = sections
            else:
                # 解析所有可识别的章节，跳过不需要的章节
                skip_sections = {'注释与链接', '干员模型'}
                target_sections = [s for s in section_mapping.keys() 
                                 if not any(skip_section in s for skip_section in skip_sections)]
            
            for section_title in target_sections:
                if section_title in section_mapping:
                    section_key = section_mapping[section_title]
                    
                    # 查找对应的章节ID
                    section_id = None
                    for toc_id, toc_info in toc.items():
                        # 更精确的匹配逻辑
                        if (section_title == toc_id or 
                            section_title in toc_info['title'] or 
                            toc_info['title'].endswith(section_title) or
                            toc_id == section_title):
                            section_id = toc_id
                            break
                    
                    if section_id:
                        content = self.extract_section_content(soup, section_id)
                        if content:
                            operator_data['sections'][section_key] = {
                                'title': section_title,
                                'content': content
                            }
                    
                    # 使用原有的专门解析方法作为备选
                    if section_key not in operator_data['sections']:
                        if section_title == '属性':
                            attr_data = {}
                            self._extract_attributes(soup, attr_data)
                            if attr_data.get('attributes'):
                                operator_data['sections'][section_key] = {
                                    'title': section_title,
                                    'content': self._format_attributes(attr_data['attributes'])
                                }
                        elif section_title == '天赋':
                            talent_data = {'talents': []}
                            self._extract_talents(soup, talent_data)
                            if talent_data['talents']:
                                operator_data['sections'][section_key] = {
                                    'title': section_title,
                                    'content': self._format_talents(talent_data['talents'])
                                }
                        elif section_title == '技能':
                            skill_data = {'skills': []}
                            self._extract_skills(soup, skill_data)
                            if skill_data['skills']:
                                operator_data['sections'][section_key] = {
                                    'title': section_title,
                                    'content': self._format_skills(skill_data['skills'])
                                }
                        elif section_title == '特性':
                            char_data = {}
                            self._extract_characteristics(soup, char_data)
                            if char_data.get('characteristics'):
                                operator_data['sections'][section_key] = {
                                    'title': section_title,
                                    'content': char_data['characteristics']
                                }
            
            # 提取基本信息（总是包含）
            basic_info = {}
            self._extract_basic_info(soup, basic_info)
            if basic_info.get('basic_info'):
                operator_data['basic_info'] = basic_info['basic_info']
                
            # 提取职业和稀有度（总是包含）  
            self._extract_profession_rarity(soup, operator_data)
                
        except Exception as e:
            logger.error(f"解析干员完整信息失败: {e}")
        
        return operator_data

    def _format_attributes(self, attributes: Dict) -> str:
        """格式化属性数据"""
        content = []
        for attr_name, attr_data in attributes.items():
            content.append(f"### {attr_name}")
            for key, value in attr_data.items():
                content.append(f"- **{key}**: {value}")
            content.append("")
        return '\n'.join(content)

    def _format_talents(self, talents: List) -> str:
        """格式化天赋数据"""
        content = []
        for i, talent in enumerate(talents, 1):
            content.append(f"### 天赋 {i}: {talent.get('name', '未知')}")
            if talent.get('condition'):
                content.append(f"**解锁条件**: {talent['condition']}")
            if talent.get('description'):
                content.append(f"**效果**: {talent['description']}")
            content.append("")
        return '\n'.join(content)

    def _format_skills(self, skills: List) -> str:
        """格式化技能数据"""
        content = []
        for i, skill in enumerate(skills, 1):
            content.append(f"### 技能 {i}: {skill.get('name', '未知')}")
            if skill.get('type'):
                content.append(f"**类型**: {skill['type']}")
            if skill.get('description'):
                content.append(f"**效果**: {skill['description']}")
            if skill.get('levels'):
                content.append("**等级数据**:")
                for level, level_data in skill['levels'].items():
                    content.append(f"- {level}: {level_data}")
            content.append("")
        return '\n'.join(content)

    async def parse_operator_detailed(self, title: str) -> Dict[str, Any]:
        """详细解析干员信息（保持向后兼容）"""
        return await self.parse_operator_complete(title)

    def _extract_basic_info(self, soup: BeautifulSoup, operator_data: Dict):
        """提取基本信息"""
        basic_info = {}
        
        # 查找属性表格
        for table in soup.find_all('table'):
            rows = table.find_all('tr')
            for row in rows:
                cells = row.find_all(['th', 'td'])
                if len(cells) >= 2:
                    key = self.extract_text_from_cell(cells[0])
                    value = self.extract_text_from_cell(cells[1])
                    
                    if key and value:
                        # 标准化字段名
                        if '再部署' in key or '部署时间' in key:
                            basic_info['再部署时间'] = value
                        elif '阻挡' in key:
                            basic_info['阻挡数'] = value
                        elif '所属势力' in key and '隐藏' not in key:
                            basic_info['所属势力'] = value
                        elif '隐藏势力' in key:
                            basic_info['隐藏势力仅在战斗中所使用的数据'] = value
                        elif '攻击间隔' in key:
                            basic_info['攻击间隔'] = value
                        elif '部署费用' in key:
                            basic_info['部署费用'] = value
        
        operator_data['basic_info'] = basic_info

    def _extract_attributes(self, soup: BeautifulSoup, operator_data: Dict):
        """提取属性数据"""
        attributes = {}
        
        # 查找属性表格
        for table in soup.find_all('table'):
            rows = table.find_all('tr')
            if not rows:
                continue
                
            # 检查是否是属性表格
            header_row = rows[0]
            header_cells = header_row.find_all(['th', 'td'])
            header_text = ' '.join([self.extract_text_from_cell(cell) for cell in header_cells])
            
            if '精英' in header_text and ('生命' in header_text or '攻击' in header_text):
                # 这是一个属性表格
                for row in rows[1:]:  # 跳过表头
                    cells = row.find_all(['th', 'td'])
                    if len(cells) >= 2:
                        attr_name = self.extract_text_from_cell(cells[0])
                        
                        if attr_name and any(keyword in attr_name for keyword in ['生命', '攻击', '防御', '法术抗性']):
                            attr_data = {}
                            for i, cell in enumerate(cells[1:], 1):
                                value = self.extract_text_from_cell(cell)
                                if value and value != '-':
                                    if i == 1:
                                        attr_data['精英0 1级不包括信赖及潜能加成'] = value
                                    elif i == 2:
                                        attr_data['精英0 满级不包括信赖及潜能加成'] = value
                                    elif i == 3:
                                        attr_data['精英1 满级不包括信赖及潜能加成'] = value
                                    elif i == 4:
                                        attr_data['精英2 满级不包括信赖及潜能加成'] = value
                                    elif i == 5 and '信赖' not in value:
                                        attr_data['信赖加成上限'] = value
                            
                            if attr_data:
                                attributes[attr_name] = attr_data
        
        operator_data['attributes'] = attributes

    def _extract_characteristics(self, soup: BeautifulSoup, operator_data: Dict):
        """提取特性信息"""
        characteristics = ""
        
        # 查找特性表格
        for table in soup.find_all('table'):
            rows = table.find_all('tr')
            for row in rows:
                cells = row.find_all(['th', 'td'])
                if len(cells) >= 2:
                    header = self.extract_text_from_cell(cells[0])
                    if '分支' in header or '特性' in header:
                        for cell in cells[1:]:
                            text = self.extract_text_from_cell(cell)
                            if text and '优先攻击' in text:
                                characteristics = text
                                break
                        if characteristics:
                            break
        
        operator_data['characteristics'] = characteristics

    def _extract_talents(self, soup: BeautifulSoup, operator_data: Dict):
        """提取天赋信息"""
        talents = []
        seen_talents = set()
        
        # 查找天赋表格
        for table in soup.find_all('table'):
            rows = table.find_all('tr')
            if not rows:
                continue
            
            # 检查是否是天赋表格
            for row in rows:
                cells = row.find_all(['th', 'td'])
                if len(cells) >= 3:
                    first_cell = self.extract_text_from_cell(cells[0])
                    if '天赋' in first_cell and ('第' in first_cell or '1' in first_cell or '2' in first_cell):
                        self._parse_talent_table(table, operator_data)
                        break
        
        # 从处理后的数据中去重
        if 'talents' in operator_data:
            for talent in operator_data['talents']:
                talent_key = f"{talent.get('name', '')}-{talent.get('condition', '')}"
                if talent_key not in seen_talents:
                    seen_talents.add(talent_key)
                    talents.append(talent)
        
        operator_data['talents'] = talents

    def _parse_talent_table(self, table, operator_data: Dict):
        """解析天赋表格"""
        if 'talents' not in operator_data:
            operator_data['talents'] = []
        
        rows = table.find_all('tr')
        for row in rows:
            cells = row.find_all(['th', 'td'])
            if len(cells) >= 3:
                first_cell = self.extract_text_from_cell(cells[0])
                
                if '天赋' in first_cell:
                    # 提取天赋名称
                    name_text = self.extract_text_from_cell(cells[1])
                    condition_text = self.extract_text_from_cell(cells[2])
                    
                    # 查找描述 - 可能在第4列或后续行
                    description = ""
                    if len(cells) > 3:
                        description = self.extract_text_from_cell(cells[3])
                    
                    if name_text and condition_text:
                        talent = {
                            'name': name_text,
                            'condition': condition_text,
                            'description': description
                        }
                        operator_data['talents'].append(talent)

    def _extract_skills(self, soup: BeautifulSoup, operator_data: Dict):
        """提取技能信息"""
        skills = []
        seen_skills = set()
        
        # 查找技能表格
        for table in soup.find_all('table'):
            rows = table.find_all('tr')
            if not rows:
                continue
            
            # 检查是否是技能表格
            header_text = ""
            for row in rows[:2]:  # 检查前两行
                cells = row.find_all(['th', 'td'])
                for cell in cells:
                    cell_text = self.extract_text_from_cell(cell)
                    if '技能' in cell_text and ('名称' in cell_text or '等级' in cell_text or '描述' in cell_text):
                        header_text += cell_text + " "
            
            if '技能' in header_text:
                self._parse_skill_table(table, operator_data)
        
        # 从处理后的数据中去重
        if 'skills' in operator_data:
            for skill in operator_data['skills']:
                skill_key = f"{skill.get('name', '')}-{skill.get('type', '')}"
                if skill_key not in seen_skills:
                    seen_skills.add(skill_key)
                    skills.append(skill)
        
        operator_data['skills'] = skills

    def _parse_skill_table(self, table, operator_data: Dict):
        """解析技能表格"""
        if 'skills' not in operator_data:
            operator_data['skills'] = []
        
        rows = table.find_all('tr')
        current_skill = None
        
        for row in rows:
            cells = row.find_all(['th', 'td'])
            if not cells:
                continue
            
            # 尝试识别技能行
            first_cell = self.extract_text_from_cell(cells[0])
            
            # 检查是否是新技能的开始
            if '技能' in first_cell and ('名称' in first_cell or len(cells) >= 3):
                if len(cells) >= 2:
                    skill_name = self.extract_text_from_cell(cells[1])
                    if skill_name and skill_name not in ['名称', '技能名称']:
                        current_skill = {
                            'name': skill_name,
                            'type': '',
                            'description': '',
                            'levels': {}
                        }
                        
                        # 查找技能类型和描述
                        if len(cells) >= 3:
                            type_or_desc = self.extract_text_from_cell(cells[2])
                            if '自动回复' in type_or_desc or '手动触发' in type_or_desc or '被动' in type_or_desc:
                                current_skill['type'] = type_or_desc
                            else:
                                current_skill['description'] = type_or_desc
                        
                        if len(cells) >= 4:
                            current_skill['description'] = self.extract_text_from_cell(cells[3])
                        
                        operator_data['skills'].append(current_skill)
            
            # 检查是否是技能等级数据
            elif current_skill and first_cell and ('等级' in first_cell or first_cell.isdigit()):
                level_name = first_cell
                level_data = []
                
                for cell in cells[1:]:
                    value = self.extract_text_from_cell(cell)
                    if value:
                        level_data.append(value)
                
                if level_data:
                    current_skill['levels'][level_name] = ' | '.join(level_data)

    def _extract_profession_rarity(self, soup: BeautifulSoup, operator_data: Dict):
        """提取职业和稀有度信息"""
        # 从页面标题和图标中提取
        title_text = soup.find('h1', {'id': 'firstHeading'})
        if title_text:
            title = title_text.get_text(strip=True)
            
            # 提取稀有度（从星星图标）
            star_imgs = soup.find_all('img', alt=re.compile(r'稀有度'))
            if star_imgs:
                for img in star_imgs:
                    alt_text = img.get('alt', '')
                    if '星' in alt_text:
                        operator_data['rarity'] = alt_text
                        break
            
            # 提取职业（从职业图标或文本）
            profession_imgs = soup.find_all('img', alt=re.compile(r'(医疗|术师|狙击|重装|近卫|先锋|辅助|特种)'))
            if profession_imgs:
                for img in profession_imgs:
                    alt_text = img.get('alt', '')
                    for prof in ['医疗', '术师', '狙击', '重装', '近卫', '先锋', '辅助', '特种']:
                        if prof in alt_text:
                            operator_data['profession'] = prof
                            break

    async def parse_enemy_complete(self, title: str, target_sections: Optional[List[str]] = None) -> Optional[Dict]:
        """解析敌人页面的完整信息"""
        try:
            html = await self.get_page_html(title)
            if not html:
                return None
            
            soup = BeautifulSoup(html, 'lxml')
            
            # 检查是否为敌人页面
            if not self._is_enemy_page(soup, title):
                return None
            
            enemy_data = {
                'title': title,
                'type': 'enemy',
                'basic_info': {},
                'levels': {},
                'table_of_contents': {},
                'sections': {}
            }
            
            # 提取目录
            toc = self.extract_table_of_contents(soup)
            enemy_data['table_of_contents'] = toc
            
            # 提取基本信息
            self._extract_enemy_basic_info(soup, enemy_data)
            
            # 提取敌人等级信息
            self._extract_enemy_levels(soup, enemy_data)
            
            # 根据章节需求过滤内容
            if target_sections:
                filtered_sections = {}
                for section_id, section_info in toc.items():
                    section_title = section_info['title']
                    if any(target in section_title for target in target_sections):
                        content = self.extract_section_content(soup, section_id)
                        if content:
                            filtered_sections[section_id] = {
                                'title': section_title,
                                'content': content
                            }
                enemy_data['sections'] = filtered_sections
            else:
                # 提取所有章节内容
                all_sections = {}
                skip_sections = {'敌人模型', '导航菜单'}  # 跳过不需要的章节
                
                for section_id, section_info in toc.items():
                    section_title = section_info['title']
                    if not any(skip_section in section_title for skip_section in skip_sections):
                        content = self.extract_section_content(soup, section_id)
                        if content:
                            all_sections[section_id] = {
                                'title': section_title,
                                'content': content
                            }
                enemy_data['sections'] = all_sections
            
            return enemy_data
            
        except Exception as e:
            print(f"解析敌人页面失败: {e}")
            return None

    def _is_enemy_page(self, soup: BeautifulSoup, title: str) -> bool:
        """判断是否为敌人页面"""
        # 检查页面标题和内容特征
        
        # 1. 检查是否有"敌人一览"链接
        enemy_overview_link = soup.find('a', href='/w/敌人一览')
        if enemy_overview_link:
            return True
        
        # 2. 检查是否有敌人特有的章节
        enemy_sections = ['级别0', '级别1', '级别2', '敌人模型']
        for heading in soup.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'h6']):
            heading_text = heading.get_text(strip=True)
            if any(section in heading_text for section in enemy_sections):
                return True
        
        # 3. 检查目录中是否有敌人特有内容
        toc_div = soup.find('div', {'id': 'toc'}) or soup.find('div', class_='toc')
        if toc_div:
            toc_text = toc_div.get_text()
            if any(section in toc_text for section in enemy_sections):
                return True
        
        # 4. 检查是否有敌人数据表格
        for table in soup.find_all('table'):
            table_text = table.get_text()
            if '生命值' in table_text and '攻击力' in table_text and '防御力' in table_text:
                # 进一步检查是否有敌人特有的属性
                if any(attr in table_text for attr in ['移动速度', '攻击间隔', '重量', '阻挡数']):
                    return True
        
        return False

    def _extract_enemy_basic_info(self, soup: BeautifulSoup, enemy_data: Dict):
        """提取敌人基本信息"""
        basic_info = {}
        
        # 从页面中提取敌人的基本属性
        for table in soup.find_all('table'):
            rows = table.find_all('tr')
            for row in rows:
                cells = row.find_all(['th', 'td'])
                if len(cells) >= 2:
                    header = self.extract_text_from_cell(cells[0])
                    value = self.extract_text_from_cell(cells[1])
                    
                    # 识别常见的敌人属性
                    if any(keyword in header for keyword in ['分类', '种族', '重量', '阻挡数']):
                        basic_info[header] = value
        
        enemy_data['basic_info'] = basic_info

    def _extract_enemy_levels(self, soup: BeautifulSoup, enemy_data: Dict):
        """提取敌人等级信息"""
        levels = {}
        
        # 查找级别章节
        for heading in soup.find_all(['h2', 'h3']):
            heading_text = heading.get_text(strip=True)
            if '级别' in heading_text:
                level_id = heading.get('id', heading_text)
                
                # 查找该级别下的数据表格
                level_data = self._extract_enemy_level_data(heading)
                if level_data:
                    levels[level_id] = {
                        'title': heading_text,
                        'data': level_data
                    }
        
        enemy_data['levels'] = levels

    def _extract_enemy_level_data(self, level_heading) -> List[Dict]:
        """提取指定级别的敌人数据"""
        level_data = []
        
        # 从级别标题开始，查找下一个表格
        current_element = level_heading.next_sibling
        while current_element:
            if hasattr(current_element, 'name'):
                if current_element.name == 'table':
                    # 解析敌人数据表格
                    table_data = self._parse_enemy_table(current_element)
                    if table_data:
                        level_data.extend(table_data)
                    break
                elif current_element.name in ['h1', 'h2', 'h3', 'h4', 'h5', 'h6']:
                    # 遇到新的标题，停止搜索
                    break
            
            current_element = current_element.next_sibling
        
        return level_data

    def _parse_enemy_table(self, table) -> List[Dict]:
        """解析敌人数据表格"""
        enemies = []
        rows = table.find_all('tr')
        
        if not rows:
            return enemies
        
        # 获取表头
        header_row = rows[0]
        headers = [self.extract_text_from_cell(cell) for cell in header_row.find_all(['th', 'td'])]
        
        # 解析数据行
        for row in rows[1:]:
            cells = row.find_all(['td', 'th'])
            if len(cells) >= len(headers):
                enemy_data = {}
                for i, cell in enumerate(cells[:len(headers)]):
                    if i < len(headers):
                        header = headers[i]
                        value = self.extract_text_from_cell(cell)
                        if header and value:
                            enemy_data[header] = value
                
                if enemy_data:
                    enemies.append(enemy_data)
        
        return enemies

    def _format_enemy_info(self, enemy_data: Dict, target_sections: Optional[List[str]] = None) -> str:
        """格式化敌人信息输出"""
        if not enemy_data:
            return "敌人信息解析失败"
        
        result = [f"# {enemy_data.get('title', '未知敌人')}"]
        
        # 基本信息
        if enemy_data.get('basic_info'):
            result.append("\n## 📋 基本信息")
            for key, value in enemy_data['basic_info'].items():
                result.append(f"- **{key}**: {value}")
        
        # 等级信息
        if enemy_data.get('levels'):
            result.append("\n## 📊 等级数据")
            for level_id, level_info in enemy_data['levels'].items():
                result.append(f"\n### {level_info['title']}")
                if level_info.get('data'):
                    for enemy in level_info['data']:
                        result.append(f"\n**{enemy.get('名称', '未知敌人')}**:")
                        for attr, value in enemy.items():
                            if attr != '名称':
                                result.append(f"- {attr}: {value}")
        
        # 页面目录（仅在完整模式下显示）
        if not target_sections and enemy_data.get('table_of_contents'):
            result.append("\n## 📚 页面目录")
            for section_id, toc_info in enemy_data['table_of_contents'].items():
                indent = "  " * (toc_info.get('level', 1) - 1)
                result.append(f"{indent}- {toc_info['title']}")
        
        # 章节内容
        if enemy_data.get('sections'):
            for section_id, section_info in enemy_data['sections'].items():
                result.append(f"\n## {section_info['title']}")
                result.append(section_info['content'])
        
        return '\n'.join(result)

    async def _verify_operator_page(self, title: str) -> bool:
        """验证页面是否真的是干员页面（通过检查是否有"干员信息"栏目）"""
        try:
            html = await self.get_page_html(title)
            if not html:
                return False
            
            soup = BeautifulSoup(html, 'lxml')
            
            # 检查是否有"干员信息"相关的标题或内容
            for heading in soup.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'h6']):
                heading_text = heading.get_text(strip=True)
                if '干员信息' in heading_text:
                    return True
            
            # 检查是否有职业、稀有度等干员特有信息
            page_text = soup.get_text()
            if any(indicator in page_text for indicator in ['★★★★★★', '★★★★★', '★★★★', '★★★', '精英化', '潜能提升']):
                return True
            
            # 检查是否有职业标识
            if any(prof in page_text for prof in ['医疗干员', '术师干员', '狙击干员', '重装干员', '近卫干员', '先锋干员', '辅助干员', '特种干员']):
                return True
                
            return False
            
        except Exception as e:
            print(f"验证干员页面失败 {title}: {e}")
            return False
    
    async def _verify_enemy_page(self, title: str) -> bool:
        """验证页面是否真的是敌人页面（通过检查是否有"敌人模型"或级别信息）"""
        try:
            html = await self.get_page_html(title)
            if not html:
                return False
            
            soup = BeautifulSoup(html, 'lxml')
            
            # 检查是否有"敌人模型"栏目
            for heading in soup.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'h6']):
                heading_text = heading.get_text(strip=True)
                if '敌人模型' in heading_text:
                    return True
            
            # 检查是否有级别信息
            for heading in soup.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'h6']):
                heading_text = heading.get_text(strip=True)
                if any(level in heading_text for level in ['级别0', '级别1', '级别2']):
                    return True
            
            # 检查是否有敌人特有的属性表格
            page_text = soup.get_text()
            if '移动速度' in page_text and '攻击间隔' in page_text and '重量' in page_text:
                return True
                
            return False
            
        except Exception as e:
            print(f"验证敌人页面失败 {title}: {e}")
            return False


