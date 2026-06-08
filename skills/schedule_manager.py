"""企业级日程管理工具 - 支持日程创建、查询、冲突检测、提醒"""
import json
import uuid
from datetime import datetime, timedelta
from typing import Optional
from langchain_core.tools import tool

# 内存日程存储
_schedule_store = {}


class ScheduleEvent:
    def __init__(self, title: str, start_time: str, end_time: str,
                 description: str = "", location: str = "", attendees: list = None,
                 reminder_minutes: int = 15):
        self.id = str(uuid.uuid4())[:8]
        self.title = title
        self.start_time = start_time  # YYYY-MM-DD HH:MM
        self.end_time = end_time
        self.description = description
        self.location = location
        self.attendees = attendees or []
        self.reminder_minutes = reminder_minutes
        self.status = "confirmed"  # confirmed, tentative, cancelled
        self.created_at = datetime.now().isoformat()

    def to_dict(self):
        return {
            "id": self.id,
            "title": self.title,
            "start_time": self.start_time,
            "end_time": self.end_time,
            "description": self.description,
            "location": self.location,
            "attendees": self.attendees,
            "reminder_minutes": self.reminder_minutes,
            "status": self.status,
            "created_at": self.created_at
        }


def _parse_time(time_str: str) -> datetime:
    """解析时间字符串"""
    formats = ["%Y-%m-%d %H:%M", "%Y-%m-%d"]
    for fmt in formats:
        try:
            return datetime.strptime(time_str, fmt)
        except ValueError:
            continue
    raise ValueError(f"时间格式不正确: {time_str}，请使用 YYYY-MM-DD HH:MM")


@tool
def create_schedule(title: str, start_time: str, end_time: str,
                    description: str = "", location: str = "",
                    attendees: str = "", reminder_minutes: int = 15) -> str:
    """创建日程安排。
    
    Args:
        title: 日程标题
        start_time: 开始时间 (YYYY-MM-DD HH:MM)
        end_time: 结束时间 (YYYY-MM-DD HH:MM)
        description: 描述
        location: 地点
        attendees: 参与人，逗号分隔
        reminder_minutes: 提前提醒分钟数
    """
    try:
        start = _parse_time(start_time)
        end = _parse_time(end_time)
        
        if end <= start:
            return "结束时间必须晚于开始时间。"
        
        attendee_list = [a.strip() for a in attendees.split(",") if a.strip()] if attendees else []
        event = ScheduleEvent(title, start_time, end_time, description, location, attendee_list, reminder_minutes)
        _schedule_store[event.id] = event
        
        return f"日程创建成功！ID: {event.id}\n{json.dumps(event.to_dict(), ensure_ascii=False, indent=2)}"
    except ValueError as e:
        return str(e)


@tool
def get_schedule(event_id: str) -> str:
    """获取日程详情。"""
    event = _schedule_store.get(event_id)
    if not event:
        return f"未找到日程: {event_id}"
    return json.dumps(event.to_dict(), ensure_ascii=False, indent=2)


@tool
def list_schedules(date: str = "", status: str = "") -> str:
    """列出日程，支持按日期和状态筛选。
    
    Args:
        date: 日期筛选 (YYYY-MM-DD)，显示该日所有日程
        status: 状态筛选 (confirmed/tentative/cancelled)
    """
    events = list(_schedule_store.values())
    
    if date:
        events = [e for e in events if e.start_time.startswith(date)]
    if status:
        events = [e for e in events if e.status == status]
    
    if not events:
        return "未找到符合条件的日程。"
    
    # 按时间排序
    events.sort(key=lambda e: e.start_time)
    
    result = []
    for e in events:
        result.append(f"[{e.start_time} - {e.end_time}] {e.title} (ID: {e.id}) | 地点: {e.location or '未指定'}")
    return f"共 {len(events)} 个日程:\n" + "\n".join(result)


@tool
def check_schedule_conflict(start_time: str, end_time: str, exclude_id: str = "") -> str:
    """检查指定时间段是否有日程冲突。
    
    Args:
        start_time: 开始时间 (YYYY-MM-DD HH:MM)
        end_time: 结束时间 (YYYY-MM-DD HH:MM)
        exclude_id: 排除的日程ID（用于更新时检查）
    """
    try:
        new_start = _parse_time(start_time)
        new_end = _parse_time(end_time)
        
        conflicts = []
        for event in _schedule_store.values():
            if event.id == exclude_id or event.status == "cancelled":
                continue
            
            event_start = _parse_time(event.start_time)
            event_end = _parse_time(event.end_time)
            
            # 检查时间重叠
            if new_start < event_end and new_end > event_start:
                conflicts.append(event.to_dict())
        
        if conflicts:
            return json.dumps({
                "has_conflict": True,
                "conflicts": conflicts
            }, ensure_ascii=False, indent=2)
        else:
            return json.dumps({"has_conflict": False, "message": "时间段可用，无冲突"}, ensure_ascii=False, indent=2)
    except ValueError as e:
        return str(e)


@tool
def update_schedule(event_id: str, title: str = "", start_time: str = "",
                    end_time: str = "", description: str = "", location: str = "",
                    attendees: str = "", status: str = "") -> str:
    """更新日程信息。"""
    event = _schedule_store.get(event_id)
    if not event:
        return f"未找到日程: {event_id}"
    
    try:
        if title:
            event.title = title
        if start_time:
            event.start_time = start_time
        if end_time:
            event.end_time = end_time
        if description:
            event.description = description
        if location:
            event.location = location
        if attendees:
            event.attendees = [a.strip() for a in attendees.split(",") if a.strip()]
        if status:
            event.status = status
        
        return f"日程更新成功！\n{json.dumps(event.to_dict(), ensure_ascii=False, indent=2)}"
    except ValueError as e:
        return str(e)


@tool
def delete_schedule(event_id: str) -> str:
    """删除日程。"""
    if event_id not in _schedule_store:
        return f"未找到日程: {event_id}"
    del _schedule_store[event_id]
    return f"日程 {event_id} 已删除。"


@tool
def get_daily_schedule(date: str) -> str:
    """获取某日的完整日程安排。"""
    events = [e for e in _schedule_store.values() if e.start_time.startswith(date) and e.status != "cancelled"]
    events.sort(key=lambda e: e.start_time)
    
    if not events:
        return f"{date} 没有日程安排。"
    
    result = [f"📅 {date} 日程安排：\n"]
    for e in events:
        result.append(f"⏰ {e.start_time.split(' ')[1] if ' ' in e.start_time else '全天'} - {e.end_time.split(' ')[1] if ' ' in e.end_time else ''}")
        result.append(f"   {e.title}")
        if e.location:
            result.append(f"   📍 {e.location}")
        if e.attendees:
            result.append(f"   👥 {', '.join(e.attendees)}")
        result.append("")
    
    return "\n".join(result)


tools = [create_schedule, get_schedule, list_schedules, check_schedule_conflict, update_schedule, delete_schedule, get_daily_schedule]
