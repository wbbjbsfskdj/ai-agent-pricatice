"""企业级邮件处理工具 - 支持邮件草稿、模板、分类、摘要"""
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
