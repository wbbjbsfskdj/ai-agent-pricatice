"""
【文件意义】
企业级邮件处理工具 - 为 MCP Agent 提供邮件草稿、模板、分类、摘要能力。

在项目中的作用：
1. 使 Agent 能够协助用户撰写邮件，提供预定义模板（会议邀请、报告发送、跟进提醒等）
2. 支持邮件分类（general/urgent/meeting/report/follow_up），Agent 可自动识别邮件紧急程度
3. 支持生成邮件摘要，帮助快速浏览大量邮件
4. 提供邮件草稿管理，用户可保存、查询、发送草稿
5. 通过 @tool 装饰器注册为 LangChain 工具，Agent 在对话中可自动调用

使用场景示例：
- 用户说："帮我写一封会议邀请邮件，主题是项目评审，明天下午3点"
- Agent 会调用 create_email_draft 工具，使用 meeting_invite 模板生成邮件
"""
import json
import uuid
from datetime import datetime
from typing import Optional
from langchain_core.tools import tool

# 内存邮件存储
_email_store = {}

# 邮件模板库
_email_templates = {
    "meeting_invite": {
        "subject": "会议邀请：{topic}",
        "body": "您好，\n\n诚邀您参加以下会议：\n主题：{topic}\n时间：{time}\n地点：{location}\n\n请确认是否出席。\n\n此致\n{sender}"
    },
    "follow_up": {
        "subject": "跟进：{topic}",
        "body": "您好，\n\n关于{topic}，想跟进一下最新进展。\n如有任何问题，请随时联系。\n\n此致\n{sender}"
    },
    "report": {
        "subject": "报告：{topic}",
        "body": "各位好，\n\n以下是{topic}的报告：\n\n{content}\n\n如有问题请反馈。\n\n此致\n{sender}"
    }
}

"""
==================== Java 等价实现 ====================

import java.time.LocalDateTime;
import java.time.format.DateTimeFormatter;
import java.util.*;
import java.util.stream.Collectors;

// 邮件实体类（对应 Python 的 Email 类）
public class Email {
    private String id;
    private String subject;
    private String body;
    private List<String> to;
    private List<String> cc;
    private String category;      // general, urgent, meeting, report, follow_up
    private String priority;      // low, normal, high
    private String status;        // draft, sent, received
    private String createdAt;

    public Email(String subject, String body, List<String> to, List<String> cc,
                 String category, String priority) {
        this.id = UUID.randomUUID().toString().substring(0, 8);
        this.subject = subject;
        this.body = body;
        this.to = to != null ? to : new ArrayList<>();
        this.cc = cc != null ? cc : new ArrayList<>();
        this.category = category;
        this.priority = priority;
        this.status = "draft";
        this.createdAt = LocalDateTime.now().format(DateTimeFormatter.ISO_LOCAL_DATE_TIME);
    }

    // getter/setter 省略...

    public Map<String, Object> toDict() {
        Map<String, Object> map = new LinkedHashMap<>();
        map.put("id", id);
        map.put("subject", subject);
        map.put("body", body);
        map.put("to", to);
        map.put("cc", cc);
        map.put("category", category);
        map.put("priority", priority);
        map.put("status", status);
        map.put("created_at", createdAt);
        return map;
    }
}

// 邮件管理器（对应 Python 的全局 _email_store 和工具函数）
public class EmailHandler {
    private static final Map<String, Email> EMAIL_STORE = new HashMap<>();

    // 邮件模板库（对应 Python 的 _email_templates 字典）
    private static final Map<String, Map<String, String>> EMAIL_TEMPLATES = new HashMap<>();

    static {
        Map<String, String> meeting = new HashMap<>();
        meeting.put("subject", "会议邀请：{topic}");
        meeting.put("body", "您好，\n\n诚邀您参加以下会议：\n主题：{topic}\n时间：{time}\n地点：{location}\n\n请确认是否出席。\n\n此致\n{sender}");
        EMAIL_TEMPLATES.put("meeting_invite", meeting);

        Map<String, String> followUp = new HashMap<>();
        followUp.put("subject", "跟进：{topic}");
        followUp.put("body", "您好，\n\n关于{topic}，想跟进一下最新进展。\n如有任何问题，请随时联系。\n\n此致\n{sender}");
        EMAIL_TEMPLATES.put("follow_up", followUp);

        Map<String, String> report = new HashMap<>();
        report.put("subject", "报告：{topic}");
        report.put("body", "各位好，\n\n以下是{topic}的报告：\n\n{content}\n\n如有问题请反馈。\n\n此致\n{sender}");
        EMAIL_TEMPLATES.put("report", report);
    }

    // 对应 Python 的 create_email 函数
    public static String createEmail(String subject, String body, String to,
                                     String cc, String category, String priority) {
        List<String> toList = parseEmailList(to);
        List<String> ccList = cc != null && !cc.isEmpty() ? parseEmailList(cc) : new ArrayList<>();
        Email email = new Email(subject, body, toList, ccList, category, priority);
        EMAIL_STORE.put(email.getId(), email);
        return "邮件草稿创建成功！ID: " + email.getId() + "\n" + toJson(email.toDict());
    }

    // 对应 Python 的 use_email_template 函数
    public static String useEmailTemplate(String templateName, Map<String, String> variables) {
        Map<String, String> template = EMAIL_TEMPLATES.get(templateName);
        if (template == null) {
            return "未找到模板: " + templateName + "。可用模板: " + EMAIL_TEMPLATES.keySet();
        }

        String subject = formatTemplate(template.get("subject"), variables);
        String body = formatTemplate(template.get("body"), variables);
        return "主题：" + subject + "\n\n正文：\n" + body;
    }

    // 对应 Python 的 get_email 函数
    public static String getEmail(String emailId) {
        Email email = EMAIL_STORE.get(emailId);
        if (email == null) {
            return "未找到邮件: " + emailId;
        }
        return toJson(email.toDict());
    }

    // 对应 Python 的 list_emails 函数
    public static String listEmails(String category, String status, String priority) {
        List<Email> emails = new ArrayList<>(EMAIL_STORE.values());

        if (category != null && !category.isEmpty()) {
            emails = emails.stream().filter(e -> e.getCategory().equals(category)).collect(Collectors.toList());
        }
        if (status != null && !status.isEmpty()) {
            emails = emails.stream().filter(e -> e.getStatus().equals(status)).collect(Collectors.toList());
        }
        if (priority != null && !priority.isEmpty()) {
            emails = emails.stream().filter(e -> e.getPriority().equals(priority)).collect(Collectors.toList());
        }

        if (emails.isEmpty()) {
            return "未找到符合条件的邮件。";
        }

        StringBuilder result = new StringBuilder("共 " + emails.size() + " 封邮件:\n");
        for (Email e : emails) {
            result.append(String.format("[%s] [%s] %s (ID: %s) -> %s\n",
                    e.getPriority(), e.getStatus(), e.getSubject(),
                    e.getId(), String.join(", ", e.getTo())));
        }
        return result.toString();
    }

    // 对应 Python 的 summarize_email 函数
    public static String summarizeEmail(String emailId) {
        Email email = EMAIL_STORE.get(emailId);
        if (email == null) {
            return "未找到邮件: " + emailId;
        }

        String bodyPreview = email.getBody().length() > 200
                ? email.getBody().substring(0, 200) + "..."
                : email.getBody();

        Map<String, Object> summary = new LinkedHashMap<>();
        summary.put("subject", email.getSubject());
        summary.put("from_to", "-> " + String.join(", ", email.getTo()));
        summary.put("category", email.getCategory());
        summary.put("priority", email.getPriority());
        summary.put("preview", bodyPreview);
        summary.put("word_count", email.getBody().length());
        return toJson(summary);
    }

    // 对应 Python 的 classify_email_content 函数
    public static String classifyEmailContent(String content) {
        String contentLower = content.toLowerCase();

        // 关键词分类规则
        Map<String, List<String>> categories = new LinkedHashMap<>();
        categories.put("meeting", Arrays.asList("会议", "meeting", "invite", "邀请", "参加", "时间", "地点"));
        categories.put("urgent", Arrays.asList("紧急", "urgent", "asap", "立即", "尽快", "马上"));
        categories.put("report", Arrays.asList("报告", "report", "总结", "汇报", "数据"));
        categories.put("follow_up", Arrays.asList("跟进", "follow up", "进展", "更新", "进度"));

        Map<String, Integer> scores = new HashMap<>();
        for (Map.Entry<String, List<String>> entry : categories.entrySet()) {
            int score = 0;
            for (String kw : entry.getValue()) {
                if (contentLower.contains(kw)) {
                    score++;
                }
            }
            if (score > 0) {
                scores.put(entry.getKey(), score);
            }
        }

        if (scores.isEmpty()) {
            return "{\"category\": \"general\", \"confidence\": \"low\"}";
        }

        String bestCat = Collections.max(scores.entrySet(), Map.Entry.comparingByValue()).getKey();
        int bestScore = scores.get(bestCat);
        String confidence = bestScore >= 3 ? "high" : "medium";

        Map<String, Object> result = new LinkedHashMap<>();
        result.put("category", bestCat);
        result.put("confidence", confidence);
        result.put("scores", scores);
        return toJson(result);
    }

    // 辅助方法：解析邮箱列表
    private static List<String> parseEmailList(String input) {
        return Arrays.stream(input.split(","))
                .map(String::trim)
                .filter(e -> !e.isEmpty())
                .collect(Collectors.toList());
    }

    // 辅助方法：格式化模板（替换 {key} 为值）
    private static String formatTemplate(String template, Map<String, String> variables) {
        String result = template;
        for (Map.Entry<String, String> entry : variables.entrySet()) {
            result = result.replace("{" + entry.getKey() + "}", entry.getValue());
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


class Email:
    def __init__(self, subject: str, body: str, to: list, cc: list = None,
                 category: str = "general", priority: str = "normal"):
        self.id = str(uuid.uuid4())[:8]
        self.subject = subject
        self.body = body
        self.to = to
        self.cc = cc or []
        self.category = category  # general, urgent, meeting, report, follow_up
        self.priority = priority  # low, normal, high
        self.status = "draft"  # draft, sent, received
        self.created_at = datetime.now().isoformat()

    def to_dict(self):
        return {
            "id": self.id,
            "subject": self.subject,
            "body": self.body,
            "to": self.to,
            "cc": self.cc,
            "category": self.category,
            "priority": self.priority,
            "status": self.status,
            "created_at": self.created_at
        }


@tool
def create_email(subject: str, body: str, to: str, cc: str = "",
                 category: str = "general", priority: str = "normal") -> str:
    """创建邮件草稿。
    
    Args:
        subject: 邮件主题
        body: 邮件正文
        to: 收件人，逗号分隔
        cc: 抄送人，逗号分隔
        category: 分类 (general/urgent/meeting/report/follow_up)
        priority: 优先级 (low/normal/high)
    """
    to_list = [e.strip() for e in to.split(",") if e.strip()]
    cc_list = [e.strip() for e in cc.split(",") if cc.strip()] if cc else []
    email = Email(subject, body, to_list, cc_list, category, priority)
    _email[email.id] = email
    return f"邮件草稿创建成功！ID: {email.id}\n{json.dumps(email.to_dict(), ensure_ascii=False, indent=2)}"


@tool
def use_email_template(template_name: str, **kwargs) -> str:
    """使用预定义邮件模板生成邮件内容。
    
    可用模板：meeting_invite, follow_up, report
    
    Args:
        template_name: 模板名称
        kwargs: 模板变量，如 topic, time, location, sender, content 等
    """
    template = _email_templates.get(template_name)
    if not template:
        return f"未找到模板: {template_name}。可用模板: {', '.join(_email_templates.keys())}"
    
    subject = template["subject"].format(**kwargs)
    body = template["body"].format(**kwargs)
    return f"主题：{subject}\n\n正文：\n{body}"


@tool
def get_email(email_id: str) -> str:
    """获取邮件详情。"""
    email = _email_store.get(email_id)
    if not email:
        return f"未找到邮件: {email_id}"
    return json.dumps(email.to_dict(), ensure_ascii=False, indent=2)


@tool
def list_emails(category: str = "", status: str = "", priority: str = "") -> str:
    """列出邮件，支持筛选。
    
    Args:
        category: 分类筛选
        status: 状态筛选 (draft/sent/received)
        priority: 优先级筛选 (low/normal/high)
    """
    emails = list(_email_store.values())
    
    if category:
        emails = [e for e in emails if e.category == category]
    if status:
        emails = [e for e in emails if e.status == status]
    if priority:
        emails = [e for e in emails if e.priority == priority]
    
    if not emails:
        return "未找到符合条件的邮件。"
    
    result = []
    for e in emails:
        result.append(f"[{e.priority}] [{e.status}] {e.subject} (ID: {e.id}) -> {', '.join(e.to)}")
    return f"共 {len(emails)} 封邮件:\n" + "\n".join(result)


@tool
def summarize_email(email_id: str) -> str:
    """获取邮件摘要（提取主题、收件人、关键信息）。"""
    email = _email_store.get(email_id)
    if not email:
        return f"未找到邮件: {email_id}"
    
    # 简单摘要逻辑：提取前200字符
    body_preview = email.body[:200] + "..." if len(email.body) > 200 else email.body
    
    summary = {
        "subject": email.subject,
        "from_to": f"-> {', '.join(email.to)}",
        "category": email.category,
        "priority": email.priority,
        "preview": body_preview,
        "word_count": len(email.body)
    }
    return json.dumps(summary, ensure_ascii=False, indent=2)


@tool
def classify_email_content(content: str) -> str:
    """根据内容自动分类邮件（基于关键词规则）。"""
    content_lower = content.lower()
    
    categories = {
        "meeting": ["会议", "meeting", "invite", "邀请", "参加", "时间", "地点"],
        "urgent": ["紧急", "urgent", "asap", "立即", "尽快", "马上"],
        "report": ["报告", "report", "总结", "汇报", "数据"],
        "follow_up": ["跟进", "follow up", "进展", "更新", "进度"]
    }
    
    scores = {}
    for cat, keywords in categories.items():
        score = sum(1 for kw in keywords if kw in content_lower)
        if score > 0:
            scores[cat] = score
    
    if not scores:
        return json.dumps({"category": "general", "confidence": "low"})
    
    best_cat = max(scores, key=scores.get)
    confidence = "high" if scores[best_cat] >= 3 else "medium"
    return json.dumps({"category": best_cat, "confidence": confidence, "scores": scores})


tools = [create_email, use_email_template, get_email, list_emails, summarize_email, classify_email_content]
