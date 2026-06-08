"""
【文件意义】
企业级日程管理工具 - 为 MCP Agent 提供日程创建、查询、冲突检测能力。

在项目中的作用：
1. 使 Agent 能够帮用户创建和管理日程安排，支持标题、时间、地点、参与人等字段
2. 核心功能：日程冲突检测，检查指定时间段是否与已有日程重叠，避免时间冲突
3. 支持按日期和状态筛选日程，方便用户快速查找
4. 支持日程状态管理（confirmed/tentative/cancelled），模拟真实日程状态流转
5. 提供每日日程视图，Agent 可展示用户某天的完整日程安排
6. 通过 @tool 装饰器注册为 LangChain 工具，Agent 在对话中可自动调用

使用场景示例：
- 用户说："帮我查一下明天下午2点到4点有没有空"
- Agent 会调用 check_schedule_conflict 工具检查时间段是否可用
"""
import json
import uuid
from datetime import datetime, timedelta
from typing import Optional
from langchain_core.tools import tool

# 内存日程存储
_schedule_store = {}

"""
==================== Java 等价实现 ====================

import java.time.LocalDateTime;
import java.time.format.DateTimeFormatter;
import java.time.format.DateTimeParseException;
import java.util.*;
import java.util.stream.Collectors;

// 日程事件实体类（对应 Python 的 ScheduleEvent 类）
public class ScheduleEvent {
    private String id;
    private String title;
    private String startTime;     // YYYY-MM-DD HH:MM
    private String endTime;
    private String description;
    private String location;
    private List<String> attendees;
    private int reminderMinutes;
    private String status;        // confirmed, tentative, cancelled
    private String createdAt;

    public ScheduleEvent(String title, String startTime, String endTime,
                         String description, String location,
                         List<String> attendees, int reminderMinutes) {
        this.id = UUID.randomUUID().toString().substring(0, 8);
        this.title = title;
        this.startTime = startTime;
        this.endTime = endTime;
        this.description = description;
        this.location = location;
        this.attendees = attendees != null ? attendees : new ArrayList<>();
        this.reminderMinutes = reminderMinutes;
        this.status = "confirmed";
        this.createdAt = LocalDateTime.now().format(DateTimeFormatter.ISO_LOCAL_DATE_TIME);
    }

    // getter/setter 省略...

    public Map<String, Object> toDict() {
        Map<String, Object> map = new LinkedHashMap<>();
        map.put("id", id);
        map.put("title", title);
        map.put("start_time", startTime);
        map.put("end_time", endTime);
        map.put("description", description);
        map.put("location", location);
        map.put("attendees", attendees);
        map.put("reminder_minutes", reminderMinutes);
        map.put("status", status);
        map.put("created_at", createdAt);
        return map;
    }
}

// 日程管理器（对应 Python 的全局 _schedule_store 和工具函数）
public class ScheduleManager {
    private static final Map<String, ScheduleEvent> SCHEDULE_STORE = new HashMap<>();

    // 对应 Python 的 _parse_time 函数
    private static LocalDateTime parseTime(String timeStr) {
        try {
            return LocalDateTime.parse(timeStr, DateTimeFormatter.ofPattern("yyyy-MM-dd HH:mm"));
        } catch (DateTimeParseException e) {
            try {
                return LocalDateTime.parse(timeStr, DateTimeFormatter.ofPattern("yyyy-MM-dd"));
            } catch (DateTimeParseException e2) {
                throw new IllegalArgumentException("时间格式不正确: " + timeStr + "，请使用 YYYY-MM-DD HH:MM");
            }
        }
    }

    // 对应 Python 的 create_schedule 函数
    public static String createSchedule(String title, String startTime, String endTime,
                                        String description, String location,
                                        String attendees, int reminderMinutes) {
        try {
            LocalDateTime start = parseTime(startTime);
            LocalDateTime end = parseTime(endTime);

            if (!end.isAfter(start)) {
                return "结束时间必须晚于开始时间。";
            }

            List<String> attendeeList = new ArrayList<>();
            if (attendees != null && !attendees.isEmpty()) {
                attendeeList = Arrays.stream(attendees.split(","))
                        .map(String::trim)
                        .filter(a -> !a.isEmpty())
                        .collect(Collectors.toList());
            }

            ScheduleEvent event = new ScheduleEvent(title, startTime, endTime,
                    description, location, attendeeList, reminderMinutes);
            SCHEDULE_STORE.put(event.getId(), event);

            return "日程创建成功！ID: " + event.getId() + "\n" + toJson(event.toDict());
        } catch (IllegalArgumentException e) {
            return e.getMessage();
        }
    }

    // 对应 Python 的 get_schedule 函数
    public static String getSchedule(String eventId) {
        ScheduleEvent event = SCHEDULE_STORE.get(eventId);
        if (event == null) {
            return "未找到日程: " + eventId;
        }
        return toJson(event.toDict());
    }

    // 对应 Python 的 list_schedules 函数
    public static String listSchedules(String date, String status) {
        List<ScheduleEvent> events = new ArrayList<>(SCHEDULE_STORE.values());

        if (date != null && !date.isEmpty()) {
            events = events.stream()
                    .filter(e -> e.getStartTime().startsWith(date))
                    .collect(Collectors.toList());
        }
        if (status != null && !status.isEmpty()) {
            events = events.stream()
                    .filter(e -> e.getStatus().equals(status))
                    .collect(Collectors.toList());
        }

        if (events.isEmpty()) {
            return "未找到符合条件的日程。";
        }

        // 按时间排序
        events.sort(Comparator.comparing(ScheduleEvent::getStartTime));

        StringBuilder result = new StringBuilder("共 " + events.size() + " 个日程:\n");
        for (ScheduleEvent e : events) {
            result.append(String.format("[%s - %s] %s (ID: %s) | 地点: %s\n",
                    e.getStartTime(), e.getEndTime(), e.getTitle(),
                    e.getId(), e.getLocation().isEmpty() ? "未指定" : e.getLocation()));
        }
        return result.toString();
    }

    // 对应 Python 的 check_schedule_conflict 函数
    public static String checkScheduleConflict(String startTime, String endTime, String excludeId) {
        try {
            LocalDateTime newStart = parseTime(startTime);
            LocalDateTime newEnd = parseTime(endTime);

            List<Map<String, Object>> conflicts = new ArrayList<>();
            for (ScheduleEvent event : SCHEDULE_STORE.values()) {
                if (event.getId().equals(excludeId) || event.getStatus().equals("cancelled")) {
                    continue;
                }

                LocalDateTime eventStart = parseTime(event.getStartTime());
                LocalDateTime eventEnd = parseTime(event.getEndTime());

                // 检查时间重叠：新开始 < 已有结束 且 新结束 > 已有开始
                if (newStart.isBefore(eventEnd) && newEnd.isAfter(eventStart)) {
                    conflicts.add(event.toDict());
                }
            }

            if (!conflicts.isEmpty()) {
                Map<String, Object> result = new LinkedHashMap<>();
                result.put("has_conflict", true);
                result.put("conflicts", conflicts);
                return toJson(result);
            } else {
                Map<String, Object> result = new LinkedHashMap<>();
                result.put("has_conflict", false);
                result.put("message", "时间段可用，无冲突");
                return toJson(result);
            }
        } catch (IllegalArgumentException e) {
            return e.getMessage();
        }
    }

    // 对应 Python 的 update_schedule 函数
    public static String updateSchedule(String eventId, String title, String startTime,
                                        String endTime, String description, String location,
                                        String attendees, String status) {
        ScheduleEvent event = SCHEDULE_STORE.get(eventId);
        if (event == null) {
            return "未找到日程: " + eventId;
        }

        try {
            if (title != null && !title.isEmpty()) event.setTitle(title);
            if (startTime != null && !startTime.isEmpty()) event.setStartTime(startTime);
            if (endTime != null && !endTime.isEmpty()) event.setEndTime(endTime);
            if (description != null && !description.isEmpty()) event.setDescription(description);
            if (location != null && !location.isEmpty()) event.setLocation(location);
            if (attendees != null && !attendees.isEmpty()) {
                event.setAttendees(Arrays.stream(attendees.split(","))
                        .map(String::trim)
                        .filter(a -> !a.isEmpty())
                        .collect(Collectors.toList()));
            }
            if (status != null && !status.isEmpty()) event.setStatus(status);

            return "日程更新成功！\n" + toJson(event.toDict());
        } catch (IllegalArgumentException e) {
            return e.getMessage();
        }
    }

    // 对应 Python 的 delete_schedule 函数
    public static String deleteSchedule(String eventId) {
        if (!SCHEDULE_STORE.containsKey(eventId)) {
            return "未找到日程: " + eventId;
        }
        SCHEDULE_STORE.remove(eventId);
        return "日程 " + eventId + " 已删除。";
    }

    // 对应 Python 的 get_daily_schedule 函数
    public static String getDailySchedule(String date) {
        List<ScheduleEvent> events = SCHEDULE_STORE.values().stream()
                .filter(e -> e.getStartTime().startsWith(date) && !e.getStatus().equals("cancelled"))
                .sorted(Comparator.comparing(ScheduleEvent::getStartTime))
                .collect(Collectors.toList());

        if (events.isEmpty()) {
            return date + " 没有日程安排。";
        }

        StringBuilder result = new StringBuilder("📅 " + date + " 日程安排：\n");
        for (ScheduleEvent e : events) {
            String startHour = e.getStartTime().contains(" ")
                    ? e.getStartTime().split(" ")[1] : "全天";
            String endHour = e.getEndTime().contains(" ")
                    ? e.getEndTime().split(" ")[1] : "";
            result.append(String.format("⏰ %s - %s\n", startHour, endHour));
            result.append(String.format("   %s\n", e.getTitle()));
            if (!e.getLocation().isEmpty()) {
                result.append(String.format("   📍 %s\n", e.getLocation()));
            }
            if (!e.getAttendees().isEmpty()) {
                result.append(String.format("   👥 %s\n", String.join(", ", e.getAttendees())));
            }
            result.append("\n");
        }
        return result.toString();
    }

    private static String toJson(Map<?, ?> map) {
        // 实际项目中使用 Jackson/Gson
        return "";
    }
}

======================================================
"""


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
