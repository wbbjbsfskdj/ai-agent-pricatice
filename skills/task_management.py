"""企业级任务管理工具 - 支持任务创建、查询、更新、删除、优先级管理"""
import json
import uuid
from datetime import datetime
from typing import Optional
from langchain_core.tools import tool

# 内存任务存储（生产环境应使用数据库）
_task_store = {}

class Task:
    def __init__(self, title: str, description: str = "", priority: str = "medium",
                 assignee: str = "", due_date: str = "", tags: list = None):
        self.id = str(uuid.uuid4())[:8]
        self.title = title
        self.description = description
        self.priority = priority  # low, medium, high, urgent
        self.status = "pending"  # pending, in_progress, completed, cancelled
        self.assignee = assignee
        self.due_date = due_date
        self.tags = tags or []
        self.created_at = datetime.now().isoformat()
        self.updated_at = self.created_at

    def to_dict(self):
        return {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "priority": self.priority,
            "status": self.status,
            "assignee": self.assignee,
            "due_date": self.due_date,
            "tags": self.tags,
            "created_at": self.created_at,
            "updated_at": self.updated_at
        }


@tool
def create_task(title: str, description: str = "", priority: str = "medium",
                assignee: str = "", due_date: str = "", tags: str = "") -> str:
    """创建新任务。
    
    Args:
        title: 任务标题（必填）
        description: 任务描述
        priority: 优先级 (low/medium/high/urgent)
        assignee: 负责人
        due_date: 截止日期 (YYYY-MM-DD)
        tags: 标签，逗号分隔
    """
    tag_list = [t.strip() for t in tags.split(",") if t.strip()] if tags else []
    task = Task(title, description, priority, assignee, due_date, tag_list)
    _task_store[task.id] = task
    return f"任务创建成功！ID: {task.id}\n{json.dumps(task.to_dict(), ensure_ascii=False, indent=2)}"


@tool
def get_task(task_id: str) -> str:
    """根据任务ID获取任务详情。"""
    task = _task_store.get(task_id)
    if not task:
        return f"未找到任务: {task_id}"
    return json.dumps(task.to_dict(), ensure_ascii=False, indent=2)


@tool
def list_tasks(status: str = "", priority: str = "", assignee: str = "", tag: str = "") -> str:
    """列出任务，支持按状态、优先级、负责人、标签筛选。
    
    Args:
        status: 状态筛选 (pending/in_progress/completed/cancelled)
        priority: 优先级筛选 (low/medium/high/urgent)
        assignee: 负责人筛选
        tag: 标签筛选
    """
    tasks = list(_task_store.values())
    
    if status:
        tasks = [t for t in tasks if t.status == status]
    if priority:
        tasks = [t for t in tasks if t.priority == priority]
    if assignee:
        tasks = [t for t in tasks if t.assignee == assignee]
    if tag:
        tasks = [t for t in tasks if tag in t.tags]
    
    if not tasks:
        return "未找到符合条件的任务。"
    
    result = []
    for t in tasks:
        result.append(f"[{t.priority.upper()}] [{t.status}] {t.title} (ID: {t.id}) - 负责人: {t.assignee or '未分配'}")
    return f"共 {len(tasks)} 个任务:\n" + "\n".join(result)


@tool
def update_task(task_id: str, title: str = "", description: str = "",
                priority: str = "", status: str = "", assignee: str = "",
                due_date: str = "", tags: str = "") -> str:
    """更新任务信息。只需提供要更新的字段。"""
    task = _task_store.get(task_id)
    if not task:
        return f"未找到任务: {task_id}"
    
    if title:
        task.title = title
    if description:
        task.description = description
    if priority:
        task.priority = priority
    if status:
        task.status = status
    if assignee:
        task.assignee = assignee
    if due_date:
        task.due_date = due_date
    if tags:
        task.tags = [t.strip() for t in tags.split(",") if t.strip()]
    
    task.updated_at = datetime.now().isoformat()
    return f"任务更新成功！\n{json.dumps(task.to_dict(), ensure_ascii=False, indent=2)}"


@tool
def delete_task(task_id: str) -> str:
    """删除指定任务。"""
    if task_id not in _task_store:
        return f"未找到任务: {task_id}"
    del _task_store[task_id]
    return f"任务 {task_id} 已删除。"


@tool
def get_task_stats() -> str:
    """获取任务统计信息，包括总数、各状态数量、各优先级数量。"""
    tasks = list(_task_store.values())
    if not tasks:
        return "当前没有任务。"
    
    stats = {
        "total": len(tasks),
        "by_status": {},
        "by_priority": {},
        "overdue": 0
    }
    
    today = datetime.now().date().isoformat()
    for t in tasks:
        stats["by_status"][t.status] = stats["by_status"].get(t.status, 0) + 1
        stats["by_priority"][t.priority] = stats["by_priority"].get(t.priority, 0) + 1
        if t.due_date and t.due_date < today and t.status not in ("completed", "cancelled"):
            stats["overdue"] += 1
    
    return json.dumps(stats, ensure_ascii=False, indent=2)


tools = [create_task, get_task, list_tasks, update_task, delete_task, get_task_stats]
