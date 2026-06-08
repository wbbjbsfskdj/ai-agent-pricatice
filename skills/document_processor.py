"""企业级文档处理工具 - 支持文档格式转换、内容提取、模板生成"""
import json
import re
from datetime import datetime
from typing import Optional
from langchain_core.tools import tool


@tool
def extract_key_info(text: str, info_type: str = "all") -> str:
    """从文本中提取关键信息（日期、邮箱、电话、URL、金额等）。
    
    Args:
        text: 要分析的文本
        info_type: 提取类型 (date/email/phone/url/money/all)
    """
    patterns = {
        "date": r'\d{4}[-/]\d{1,2}[-/]\d{1,2}',
        "email": r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}',
        "phone": r'1[3-9]\d{9}|(\d{3,4}-?\d{7,8})',
        "url": r'https?://[^\s]+',
        "money": r'¥?\d+\.?\d*[万元亿]?'
    }
    
    results = {}
    target_types = [info_type] if info_type != "all" else patterns.keys()
    
    for t in target_types:
        if t in patterns:
            matches = re.findall(patterns[t], text)
            results[t] = list(set(matches))
    
    return json.dumps(results, ensure_ascii=False, indent=2)


@tool
def format_document(content: str, format_type: str = "markdown") -> str:
    """将文本转换为指定格式。
    
    Args:
        content: 原始内容
        format_type: 目标格式 (markdown/html/plain)
    """
    if format_type == "markdown":
        # 简单格式化：标题、列表等
        lines = content.split("\n")
        formatted = []
        for line in lines:
            line = line.strip()
            if not line:
                formatted.append("")
                continue
            # 检测可能的标题
            if len(line) < 50 and not line.endswith((".", "！", "!", "。")):
                formatted.append(f"## {line}")
            elif line.startswith(("-", "*")):
                formatted.append(line)
            else:
                formatted.append(line)
        return "\n".join(formatted)
    
    elif format_type == "html":
        lines = content.split("\n")
        html = ["<div>"]
        for line in lines:
            line = line.strip()
            if not line:
                continue
            html.append(f"<p>{line}</p>")
        html.append("</div>")
        return "\n".join(html)
    
    else:
        return content


@tool
def generate_report_template(report_type: str = "weekly", **kwargs) -> str:
    """生成报告模板。
    
    Args:
        report_type: 报告类型 (weekly/monthly/project/meeting)
        kwargs: 自定义变量
    """
    templates = {
        "weekly": {
            "title": "周报 - {week}",
            "sections": [
                "## 本周完成",
                "- 任务1：",
                "- 任务2：",
                "",
                "## 进行中",
                "- 任务3：进度 XX%",
                "",
                "## 下周计划",
                "- 计划1：",
                "- 计划2：",
                "",
                "## 风险与问题",
                "- 无"
            ]
        },
        "monthly": {
            "title": "月报 - {month}",
            "sections": [
                "## 月度目标完成情况",
                "- 目标1：完成率 XX%",
                "- 目标2：完成率 XX%",
                "",
                "## 关键成果",
                "1. 成果1",
                "2. 成果2",
                "",
                "## 数据分析",
                "- 指标1：数值",
                "- 指标2：数值",
                "",
                "## 下月规划",
                "- 规划1：",
                "- 规划2："
            ]
        },
        "project": {
            "title": "项目报告 - {project_name}",
            "sections": [
                "## 项目概述",
                "- 项目名称：",
                "- 负责人：",
                "- 当前阶段：",
                "",
                "## 进度更新",
                "- 已完成里程碑：",
                "- 当前进度：XX%",
                "",
                "## 风险与问题",
                "| 风险 | 影响 | 应对措施 |",
                "|------|------|----------|",
                "|      |      |          |",
                "",
                "## 资源需求",
                "- 人力：",
                "- 预算："
            ]
        },
        "meeting": {
            "title": "会议纪要 - {meeting_name}",
            "sections": [
                "## 基本信息",
                "- 时间：",
                "- 地点：",
                "- 参会人：",
                "",
                "## 会议议题",
                "1. 议题1",
                "2. 议题2",
                "",
                "## 讨论内容",
                "### 议题1",
                "- 讨论要点：",
                "- 结论：",
                "",
                "## 行动项",
                "| 任务 | 负责人 | 截止日期 |",
                "|------|--------|----------|",
                "|      |        |          |"
            ]
        }
    }
    
    template = templates.get(report_type)
    if not template:
        return f"未找到模板: {report_type}。可用模板: {', '.join(templates.keys())}"
    
    title = template["title"].format(**kwargs) if kwargs else template["title"]
    content = "\n".join(template["sections"])
    
    return f"# {title}\n\n{content}"


@tool
def count_words(text: str, detail: bool = False) -> str:
    """统计文本字数、段落数、行数等信息。"""
    chars = len(text)
    chars_no_space = len(text.replace(" ", "").replace("\n", "").replace("\t", ""))
    words = len(text.split())
    lines = len(text.split("\n"))
    paragraphs = len([p for p in text.split("\n\n") if p.strip()])
    
    result = {
        "total_chars": chars,
        "chars_without_spaces": chars_no_space,
        "words": words,
        "lines": lines,
        "paragraphs": paragraphs
    }
    
    if detail:
        # 统计词频
        word_freq = {}
        for word in text.split():
            word = word.strip(".,!?;:，。！？；：")
            if word:
                word_freq[word] = word_freq.get(word, 0) + 1
        top_words = sorted(word_freq.items(), key=lambda x: x[1], reverse=True)[:10]
        result["top_10_words"] = dict(top_words)
    
    return json.dumps(result, ensure_ascii=False, indent=2)


@tool
def compare_texts(text1: str, text2: str) -> str:
    """比较两段文本的差异（简单版本）。"""
    lines1 = set(text1.split("\n"))
    lines2 = set(text2.split("\n"))
    
    only_in_1 = lines1 - lines2
    only_in_2 = lines2 - lines1
    common = lines1 & lines2
    
    similarity = len(common) / max(len(lines1 | lines2), 1) * 100
    
    return json.dumps({
        "similarity_percent": round(similarity, 2),
        "lines_only_in_text1": len(only_in_1),
        "lines_only_in_text2": len(only_in_2),
        "common_lines": len(common),
        "unique_to_text1": list(only_in_1)[:5],
        "unique_to_text2": list(only_in_2)[:5]
    }, ensure_ascii=False, indent=2)


tools = [extract_key_info, format_document, generate_report_template, count_words, compare_texts]
