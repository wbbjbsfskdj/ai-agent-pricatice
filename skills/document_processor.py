"""
【文件意义】
企业级文档处理工具 - 为 MCP Agent 提供文档格式转换、信息提取、模板生成能力。

在项目中的作用：
1. 关键信息提取：从文本中自动提取日期、邮箱、电话、URL、金额等结构化信息
2. 文档格式转换：支持将文本转换为 Markdown 或 HTML 格式，方便展示和分享
3. 报告模板生成：内置周报、月报、项目报告、会议纪要四种常用模板，Agent 可直接生成
4. 文本统计：统计字数、段落数、行数、词频等，帮助了解文档特征
5. 文本对比：比较两段文本的差异，计算相似度，适用于版本对比场景
6. 通过 @tool 装饰器注册为 LangChain 工具，Agent 在对话中可自动调用

使用场景示例：
- 用户说："帮我生成一份周报模板"
- Agent 会调用 generate_report_template 工具，返回周报 Markdown 模板
"""
import json
import re
from datetime import datetime
from typing import Optional
from langchain_core.tools import tool

"""
==================== Java 等价实现 ====================

import java.util.*;
import java.util.regex.Matcher;
import java.util.regex.Pattern;
import java.util.stream.Collectors;

public class DocumentProcessor {

    // 正则表达式模式（对应 Python 的 patterns 字典）
    private static final Map<String, String> PATTERNS = new LinkedHashMap<>();
    static {
        PATTERNS.put("date", "\\d{4}[-/]\\d{1,2}[-/]\\d{1,2}");
        PATTERNS.put("email", "[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\\.[a-zA-Z]{2,}");
        PATTERNS.put("phone", "1[3-9]\\d{9}|(\\d{3,4}-?\\d{7,8})");
        PATTERNS.put("url", "https?://[^\\s]+");
        PATTERNS.put("money", "¥?\\d+\\.?\\d*[万元亿]?");
    }

    // 对应 Python 的 extract_key_info 函数
    public static String extractKeyInfo(String text, String infoType) {
        Map<String, List<String>> results = new LinkedHashMap<>();
        List<String> targetTypes = !"all".equals(infoType)
                ? Collections.singletonList(infoType)
                : new ArrayList<>(PATTERNS.keySet());

        for (String type : targetTypes) {
            String regex = PATTERNS.get(type);
            if (regex != null) {
                Pattern pattern = Pattern.compile(regex);
                Matcher matcher = pattern.matcher(text);
                Set<String> matches = new LinkedHashSet<>();
                while (matcher.find()) {
                    matches.add(matcher.group());
                }
                results.put(type, new ArrayList<>(matches));
            }
        }
        return toJson(results);
    }

    // 对应 Python 的 format_document 函数
    public static String formatDocument(String content, String formatType) {
        if ("markdown".equals(formatType)) {
            String[] lines = content.split("\n");
            List<String> formatted = new ArrayList<>();
            for (String line : lines) {
                line = line.trim();
                if (line.isEmpty()) {
                    formatted.add("");
                    continue;
                }
                // 检测可能的标题：短且不以句号结尾
                if (line.length() < 50 && !line.endsWith(".") && !line.endsWith("。")
                        && !line.endsWith("!") && !line.endsWith("！")) {
                    formatted.add("## " + line);
                } else {
                    formatted.add(line);
                }
            }
            return String.join("\n", formatted);

        } else if ("html".equals(formatType)) {
            String[] lines = content.split("\n");
            List<String> html = new ArrayList<>();
            html.add("<div>");
            for (String line : lines) {
                line = line.trim();
                if (!line.isEmpty()) {
                    html.add("<p>" + line + "</p>");
                }
            }
            html.add("</div>");
            return String.join("\n", html);
        }

        return content;
    }

    // 对应 Python 的 generate_report_template 函数
    public static String generateReportTemplate(String reportType, Map<String, String> variables) {
        Map<String, Map<String, Object>> templates = new LinkedHashMap<>();

        // 周报模板
        Map<String, Object> weekly = new LinkedHashMap<>();
        weekly.put("title", "周报 - {week}");
        weekly.put("sections", Arrays.asList(
                "## 本周完成", "- 任务1：", "- 任务2：", "",
                "## 进行中", "- 任务3：进度 XX%", "",
                "## 下周计划", "- 计划1：", "- 计划2：", "",
                "## 风险与问题", "- 无"
        ));
        templates.put("weekly", weekly);

        // 月报模板
        Map<String, Object> monthly = new LinkedHashMap<>();
        monthly.put("title", "月报 - {month}");
        monthly.put("sections", Arrays.asList(
                "## 月度目标完成情况", "- 目标1：完成率 XX%", "- 目标2：完成率 XX%", "",
                "## 关键成果", "1. 成果1", "2. 成果2", "",
                "## 数据分析", "- 指标1：数值", "- 指标2：数值", "",
                "## 下月规划", "- 规划1：", "- 规划2："
        ));
        templates.put("monthly", monthly);

        // 项目报告模板
        Map<String, Object> project = new LinkedHashMap<>();
        project.put("title", "项目报告 - {project_name}");
        project.put("sections", Arrays.asList(
                "## 项目概述", "- 项目名称：", "- 负责人：", "- 当前阶段：", "",
                "## 进度更新", "- 已完成里程碑：", "- 当前进度：XX%", "",
                "## 风险与问题", "| 风险 | 影响 | 应对措施 |", "|------|------|----------|", "|      |      |          |", "",
                "## 资源需求", "- 人力：", "- 预算："
        ));
        templates.put("project", project);

        // 会议纪要模板
        Map<String, Object> meeting = new LinkedHashMap<>();
        meeting.put("title", "会议纪要 - {meeting_name}");
        meeting.put("sections", Arrays.asList(
                "## 基本信息", "- 时间：", "- 地点：", "- 参会人：", "",
                "## 会议议题", "1. 议题1", "2. 议题2", "",
                "## 讨论内容", "### 议题1", "- 讨论要点：", "- 结论：", "",
                "## 行动项", "| 任务 | 负责人 | 截止日期 |", "|------|--------|----------|", "|      |        |          |"
        ));
        templates.put("meeting", meeting);

        Map<String, Object> template = templates.get(reportType);
        if (template == null) {
            return "未找到模板: " + reportType + "。可用模板: " + templates.keySet();
        }

        String title = formatTemplate((String) template.get("title"), variables);
        @SuppressWarnings("unchecked")
        List<String> sections = (List<String>) template.get("sections");
        String content = String.join("\n", sections);

        return "# " + title + "\n\n" + content;
    }

    // 对应 Python 的 count_words 函数
    public static String countWords(String text, boolean detail) {
        Map<String, Object> result = new LinkedHashMap<>();
        result.put("total_chars", text.length());
        result.put("chars_without_spaces", text.replaceAll("[ \\n\t]", "").length());
        result.put("words", text.split("\\s+").length);
        result.put("lines", text.split("\n", -1).length);
        result.put("paragraphs", Arrays.stream(text.split("\n\n"))
                .filter(p -> !p.trim().isEmpty()).count());

        if (detail) {
            // 统计词频
            Map<String, Integer> wordFreq = new HashMap<>();
            for (String word : text.split("\\s+")) {
                word = word.replaceAll("[.,!?;:，。！？；：]", "");
                if (!word.isEmpty()) {
                    wordFreq.merge(word, 1, Integer::sum);
                }
            }
            // 取前10个高频词
            List<Map.Entry<String, Integer>> topWords = wordFreq.entrySet().stream()
                    .sorted(Map.Entry.<String, Integer>comparingByValue().reversed())
                    .limit(10)
                    .collect(Collectors.toList());
            Map<String, Integer> top10 = new LinkedHashMap<>();
            for (Map.Entry<String, Integer> entry : topWords) {
                top10.put(entry.getKey(), entry.getValue());
            }
            result.put("top_10_words", top10);
        }

        return toJson(result);
    }

    // 对应 Python 的 compare_texts 函数
    public static String compareTexts(String text1, String text2) {
        Set<String> lines1 = new HashSet<>(Arrays.asList(text1.split("\n")));
        Set<String> lines2 = new HashSet<>(Arrays.asList(text2.split("\n")));

        Set<String> onlyIn1 = new HashSet<>(lines1);
        onlyIn1.removeAll(lines2);

        Set<String> onlyIn2 = new HashSet<>(lines2);
        onlyIn2.removeAll(lines1);

        Set<String> common = new HashSet<>(lines1);
        common.retainAll(lines2);

        Set<String> union = new HashSet<>(lines1);
        union.addAll(lines2);
        double similarity = union.isEmpty() ? 0 : (double) common.size() / union.size() * 100;

        Map<String, Object> result = new LinkedHashMap<>();
        result.put("similarity_percent", Math.round(similarity * 100.0) / 100.0);
        result.put("lines_only_in_text1", onlyIn1.size());
        result.put("lines_only_in_text2", onlyIn2.size());
        result.put("common_lines", common.size());
        result.put("unique_to_text1", onlyIn1.stream().limit(5).collect(Collectors.toList()));
        result.put("unique_to_text2", onlyIn2.stream().limit(5).collect(Collectors.toList()));
        return toJson(result);
    }

    // 辅助方法：格式化模板
    private static String formatTemplate(String template, Map<String, String> variables) {
        String result = template;
        if (variables != null) {
            for (Map.Entry<String, String> entry : variables.entrySet()) {
                result = result.replace("{" + entry.getKey() + "}", entry.getValue());
            }
        }
        return result;
    }

    private static String toJson(Map<?, ?> map) {
        // 实际项目中使用 Jackson/Gson
        return "";
    }
}

======================================================
"""


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
