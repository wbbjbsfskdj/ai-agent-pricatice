"""企业级日志记录工具 - 支持操作日志记录、查询、分析"""
import json
import uuid
from datetime import datetime
from typing import Optional
from langchain_core.tools import tool

# 内存日志存储
_log_store = []


class LogEntry:
    def __init__(self, level: str, module: str, action: str, user: str = "",
                 details: str = "", metadata: dict = None):
        self.id = str(uuid.uuid4())[:8]
        self.timestamp = datetime.now().isoformat()
        self.level = level  # info, warning, error, critical
        self.module = module
        self.action = action
        self.user = user
        self.details = details
        self.metadata = metadata or {}

    def to_dict(self):
        return {
            "id": self.id,
            "timestamp": self.timestamp,
            "level": self.level,
            "module": self.module,
            "action": self.action,
            "user": self.user,
            "details": self.details,
            "metadata": self.metadata
        }


@tool
def log_operation(level: str, module: str, action: str, user: str = "",
                  details: str = "", metadata: str = "") -> str:
    """记录操作日志。
    
    Args:
        level: 日志级别 (info/warning/error/critical)
        module: 模块名称
        action: 操作描述
        user: 操作用户
        details: 详细信息
        metadata: 元数据，JSON格式字符串
    """
    try:
        meta = json.loads(metadata) if metadata else {}
    except json.JSONDecodeError:
        meta = {"raw_metadata": metadata}
    
    entry = LogEntry(level, module, action, user, details, meta)
    _log_store.append(entry)
    
    return f"日志记录成功！ID: {entry.id}\n{json.dumps(entry.to_dict(), ensure_ascii=False, indent=2)}"


@tool
def query_logs(level: str = "", module: str = "", user: str = "",
               start_time: str = "", end_time: str = "", limit: int = 20) -> str:
    """查询日志，支持多条件筛选。
    
    Args:
        level: 日志级别筛选
        module: 模块筛选
        user: 用户筛选
        start_time: 开始时间 (YYYY-MM-DD)
        end_time: 结束时间 (YYYY-MM-DD)
        limit: 返回条数限制
    """
    logs = _log_store.copy()
    
    if level:
        logs = [l for l in logs if l.level == level]
    if module:
        logs = [l for l in logs if l.module == module]
    if user:
        logs = [l for l in logs if l.user == user]
    if start_time:
        logs = [l for l in logs if l.timestamp >= start_time]
    if end_time:
        logs = [l for l in logs if l.timestamp <= end_time]
    
    # 按时间倒序
    logs.sort(key=lambda l: l.timestamp, reverse=True)
    logs = logs[:limit]
    
    if not logs:
        return "未找到符合条件的日志。"
    
    result = []
    for l in logs:
        result.append(f"[{l.timestamp}] [{l.level.upper()}] [{l.module}] {l.action} (用户: {l.user or '系统'})")
    
    return f"共 {len(logs)} 条日志:\n" + "\n".join(result)


@tool
def get_log_stats(module: str = "") -> str:
    """获取日志统计信息。"""
    logs = _log_store
    if module:
        logs = [l for l in logs if l.module == module]
    
    if not logs:
        return "没有日志记录。"
    
    stats = {
        "total": len(logs),
        "by_level": {},
        "by_module": {},
        "by_user": {},
        "recent_errors": []
    }
    
    for l in logs:
        stats["by_level"][l.level] = stats["by_level"].get(l.level, 0) + 1
        stats["by_module"][l.module] = stats["by_module"].get(l.module, 0) + 1
        if l.user:
            stats["by_user"][l.user] = stats["by_user"].get(l.user, 0) + 1
        
        if l.level in ("error", "critical"):
            stats["recent_errors"].append({
                "timestamp": l.timestamp,
                "module": l.module,
                "action": l.action,
                "details": l.details
            })
    
    # 只保留最近5条错误
    stats["recent_errors"] = stats["recent_errors"][-5:]
    
    return json.dumps(stats, ensure_ascii=False, indent=2)


@tool
def get_user_activity(user: str) -> str:
    """获取指定用户的操作活动记录。"""
    user_logs = [l for l in _log_store if l.user == user]
    user_logs.sort(key=lambda l: l.timestamp, reverse=True)
    
    if not user_logs:
        return f"未找到用户 {user} 的活动记录。"
    
    activities = []
    for l in user_logs[:20]:
        activities.append({
            "time": l.timestamp,
            "module": l.module,
            "action": l.action,
            "level": l.level
        })
    
    return json.dumps({
        "user": user,
        "total_actions": len(user_logs),
        "recent_activities": activities
    }, ensure_ascii=False, indent=2)


@tool
def clear_logs(older_than: str = "") -> str:
    """清理日志。
    
    Args:
        older_than: 清理此时间之前的日志 (YYYY-MM-DD)
    """
    global _log_store
    
    if older_than:
        _log_store = [l for l in _log_store if l.timestamp >= older_than]
        return f"已清理 {older_than} 之前的日志，剩余 {len(_log_store)} 条。"
    else:
        count = len(_log_store)
        _log_store = []
        return f"已清理所有日志，共 {count} 条。"


tools = [log_operation, query_logs, get_log_stats, get_user_activity, clear_logs]
