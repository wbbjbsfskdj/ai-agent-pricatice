"""
【文件意义】
企业级日志记录工具 - 为 MCP Agent 提供操作日志记录、查询、分析能力。

在项目中的作用：
1. 操作审计：记录用户的所有操作行为，包括操作人、模块、动作、时间等，满足企业合规要求
2. 多条件查询：支持按日志级别、模块、用户、时间范围筛选日志，方便问题排查
3. 统计分析：自动统计各模块、各用户的操作频次，汇总错误日志，帮助发现系统热点和问题
4. 用户活动追踪：查看指定用户的完整操作历史，适用于权限审计和行为分析
5. 日志清理：支持按时间清理过期日志，控制存储成本
6. 通过 @tool 装饰器注册为 LangChain 工具，Agent 在对话中可自动调用

使用场景示例：
- 用户说："帮我查一下最近有哪些错误日志"
- Agent 会调用 get_log_stats 工具，返回错误日志统计和详情
"""
import json
import uuid
from datetime import datetime
from typing import Optional
from langchain_core.tools import tool

# 内存日志存储
_log_store = []

"""
==================== Java 等价实现 ====================

import java.time.LocalDateTime;
import java.time.format.DateTimeFormatter;
import java.util.*;
import java.util.stream.Collectors;

// 日志条目实体类（对应 Python 的 LogEntry 类）
public class LogEntry {
    private String id;
    private String timestamp;
    private String level;       // info, warning, error, critical
    private String module;
    private String action;
    private String user;
    private String details;
    private Map<String, Object> metadata;

    public LogEntry(String level, String module, String action, String user,
                    String details, Map<String, Object> metadata) {
        this.id = UUID.randomUUID().toString().substring(0, 8);
        this.timestamp = LocalDateTime.now().format(DateTimeFormatter.ISO_LOCAL_DATE_TIME);
        this.level = level;
        this.module = module;
        this.action = action;
        this.user = user;
        this.details = details;
        this.metadata = metadata != null ? metadata : new HashMap<>();
    }

    // getter/setter 省略...

    public Map<String, Object> toDict() {
        Map<String, Object> map = new LinkedHashMap<>();
        map.put("id", id);
        map.put("timestamp", timestamp);
        map.put("level", level);
        map.put("module", module);
        map.put("action", action);
        map.put("user", user);
        map.put("details", details);
        map.put("metadata", metadata);
        return map;
    }
}

// 日志管理器（对应 Python 的全局 _log_store 和工具函数）
public class Logger {
    private static final List<LogEntry> LOG_STORE = new ArrayList<>();

    // 对应 Python 的 log_operation 函数
    public static String logOperation(String level, String module, String action,
                                      String user, String details, String metadata) {
        Map<String, Object> meta = new HashMap<>();
        if (metadata != null && !metadata.isEmpty()) {
            try {
                // 实际项目中使用 Jackson/Gson 解析 JSON
                meta = parseJson(metadata);
            } catch (Exception e) {
                meta.put("raw_metadata", metadata);
            }
        }

        LogEntry entry = new LogEntry(level, module, action, user, details, meta);
        LOG_STORE.add(entry);

        return "日志记录成功！ID: " + entry.getId() + "\n" + toJson(entry.toDict());
    }

    // 对应 Python 的 query_logs 函数
    public static String queryLogs(String level, String module, String user,
                                   String startTime, String endTime, int limit) {
        List<LogEntry> logs = new ArrayList<>(LOG_STORE);

        if (level != null && !level.isEmpty()) {
            logs = logs.stream()
                    .filter(l -> l.getLevel().equals(level))
                    .collect(Collectors.toList());
        }
        if (module != null && !module.isEmpty()) {
            logs = logs.stream()
                    .filter(l -> l.getModule().equals(module))
                    .collect(Collectors.toList());
        }
        if (user != null && !user.isEmpty()) {
            logs = logs.stream()
                    .filter(l -> l.getUser().equals(user))
                    .collect(Collectors.toList());
        }
        if (startTime != null && !startTime.isEmpty()) {
            logs = logs.stream()
                    .filter(l -> l.getTimestamp().compareTo(startTime) >= 0)
                    .collect(Collectors.toList());
        }
        if (endTime != null && !endTime.isEmpty()) {
            logs = logs.stream()
                    .filter(l -> l.getTimestamp().compareTo(endTime) <= 0)
                    .collect(Collectors.toList());
        }

        // 按时间倒序
        logs.sort(Comparator.comparing(LogEntry::getTimestamp).reversed());
        logs = logs.subList(0, Math.min(limit, logs.size()));

        if (logs.isEmpty()) {
            return "未找到符合条件的日志。";
        }

        StringBuilder result = new StringBuilder("共 " + logs.size() + " 条日志:\n");
        for (LogEntry l : logs) {
            result.append(String.format("[%s] [%s] [%s] %s (用户: %s)\n",
                    l.getTimestamp(),
                    l.getLevel().toUpperCase(),
                    l.getModule(),
                    l.getAction(),
                    l.getUser().isEmpty() ? "系统" : l.getUser()));
        }
        return result.toString();
    }

    // 对应 Python 的 get_log_stats 函数
    public static String getLogStats(String module) {
        List<LogEntry> logs = LOG_STORE;
        if (module != null && !module.isEmpty()) {
            logs = logs.stream()
                    .filter(l -> l.getModule().equals(module))
                    .collect(Collectors.toList());
        }

        if (logs.isEmpty()) {
            return "没有日志记录。";
        }

        Map<String, Object> stats = new LinkedHashMap<>();
        stats.put("total", logs.size());

        Map<String, Integer> byLevel = new HashMap<>();
        Map<String, Integer> byModule = new HashMap<>();
        Map<String, Integer> byUser = new HashMap<>();
        List<Map<String, Object>> recentErrors = new ArrayList<>();

        for (LogEntry l : logs) {
            byLevel.merge(l.getLevel(), 1, Integer::sum);
            byModule.merge(l.getModule(), 1, Integer::sum);
            if (!l.getUser().isEmpty()) {
                byUser.merge(l.getUser(), 1, Integer::sum);
            }

            if ("error".equals(l.getLevel()) || "critical".equals(l.getLevel())) {
                Map<String, Object> error = new LinkedHashMap<>();
                error.put("timestamp", l.getTimestamp());
                error.put("module", l.getModule());
                error.put("action", l.getAction());
                error.put("details", l.getDetails());
                recentErrors.add(error);
            }
        }

        stats.put("by_level", byLevel);
        stats.put("by_module", byModule);
        stats.put("by_user", byUser);
        // 只保留最近5条错误
        stats.put("recent_errors", recentErrors.subList(
                Math.max(0, recentErrors.size() - 5), recentErrors.size()));

        return toJson(stats);
    }

    // 对应 Python 的 get_user_activity 函数
    public static String getUserActivity(String user) {
        List<LogEntry> userLogs = LOG_STORE.stream()
                .filter(l -> l.getUser().equals(user))
                .sorted(Comparator.comparing(LogEntry::getTimestamp).reversed())
                .collect(Collectors.toList());

        if (userLogs.isEmpty()) {
            return "未找到用户 " + user + " 的活动记录。";
        }

        List<Map<String, Object>> activities = new ArrayList<>();
        for (LogEntry l : userLogs.subList(0, Math.min(20, userLogs.size()))) {
            Map<String, Object> activity = new LinkedHashMap<>();
            activity.put("time", l.getTimestamp());
            activity.put("module", l.getModule());
            activity.put("action", l.getAction());
            activity.put("level", l.getLevel());
            activities.add(activity);
        }

        Map<String, Object> result = new LinkedHashMap<>();
        result.put("user", user);
        result.put("total_actions", userLogs.size());
        result.put("recent_activities", activities);
        return toJson(result);
    }

    // 对应 Python 的 clear_logs 函数
    public static String clearLogs(String olderThan) {
        if (olderThan != null && !olderThan.isEmpty()) {
            int beforeSize = LOG_STORE.size();
            List<LogEntry> filtered = LOG_STORE.stream()
                    .filter(l -> l.getTimestamp().compareTo(olderThan) >= 0)
                    .collect(Collectors.toList());
            LOG_STORE.clear();
            LOG_STORE.addAll(filtered);
            return "已清理 " + olderThan + " 之前的日志，剩余 " + LOG_STORE.size() + " 条。";
        } else {
            int count = LOG_STORE.size();
            LOG_STORE.clear();
            return "已清理所有日志，共 " + count + " 条。";
        }
    }

    private static Map<String, Object> parseJson(String json) {
        // 实际项目中使用 Jackson/Gson
        return new HashMap<>();
    }

    private static String toJson(Map<?, ?> map) {
        // 实际项目中使用 Jackson/Gson
        return "";
    }
}

======================================================
"""


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
