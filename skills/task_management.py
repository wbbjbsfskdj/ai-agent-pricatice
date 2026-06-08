"""
【文件意义】
企业级任务管理工具 - 为 MCP Agent 提供完整的任务管理能力。

在项目中的作用：
1. 作为 Agent 的核心工具之一，使 Agent 能够帮用户创建、查询、更新、删除任务
2. 支持任务优先级管理（low/medium/high/urgent），让 Agent 能协助用户进行任务优先级排序
3. 支持任务状态流转（pending → in_progress → completed → cancelled），模拟企业工作流
4. 支持任务标签和负责人分配，贴合企业团队协作场景
5. 通过 @tool 装饰器注册为 LangChain 工具，Agent 在对话中可自动调用这些函数

使用场景示例：
- 用户说："帮我创建一个明天截止的高优先级任务：完成季度报告"
- Agent 会调用 create_schedule 工具创建任务并返回结果
"""
import json
import uuid
from datetime import datetime
from typing import Optional
from langchain_core.tools import tool

# 内存任务存储（生产环境应使用数据库）
_task_store = {}

"""
==================== Java 等价实现 ====================

// 对应的 Java 类
import java.time.LocalDateTime;
import java.time.format.DateTimeFormatter;
import java.util.*;
import java.util.stream.Collectors;

public class Task {
    private String id;
    private String title;
    private String description;
    private String priority;      // low, medium, high, urgent
    private String status;        // pending, in_progress, completed, cancelled
    private String assignee;
    private String dueDate;       // YYYY-MM-DD
    private List<String> tags;
    private String createdAt;
    private String updatedAt;

    public Task(String title, String description, String priority,
                String assignee, String dueDate, List<String> tags) {
        this.id = UUID.randomUUID().toString().substring(0, 8);
        this.title = title;
        this.description = description;
        this.priority = priority;
        this.status = "pending";
        this.assignee = assignee;
        this.dueDate = dueDate;
        this.tags = tags != null ? tags : new ArrayList<>();
        this.createdAt = LocalDateTime.now().format(DateTimeFormatter.ISO_LOCAL_DATE_TIME);
        this.updatedAt = this.createdAt;
    }

    // getter/setter 省略...

    public Map<String, Object> toDict() {
        Map<String, Object> map = new LinkedHashMap<>();
        map.put("id", id);
        map.put("title", title);
        map.put("description", description);
        map.put("priority", priority);
        map.put("status", status);
        map.put("assignee", assignee);
        map.put("due_date", dueDate);
        map.put("tags", tags);
        map.put("created_at", createdAt);
        map.put("updated_at", updatedAt);
        return map;
    }
}

// 任务管理器（对应 Python 的全局 _task_store 和工具函数）
public class TaskManager {
    private static final Map<String, Task> TASK_STORE = new HashMap<>();

    // 对应 Python 的 create_task 函数
    public static String createTask(String title, String description, String priority,
                                    String assignee, String dueDate, String tags) {
        List<String> tagList = new ArrayList<>();
        if (tags != null && !tags.isEmpty()) {
            tagList = Arrays.stream(tags.split(","))
                    .map(String::trim)
                    .filter(t -> !t.isEmpty())
                    .collect(Collectors.toList());
        }
        Task task = new Task(title, description, priority, assignee, dueDate, tagList);
        TASK_STORE.put(task.getId(), task);
        return "任务创建成功！ID: " + task.getId() + "\n" + toJson(task.toDict());
    }

    // 对应 Python 的 get_task 函数
    public static String getTask(String taskId) {
        Task task = TASK_STORE.get(taskId);
        if (task == null) {
            return "未找到任务: " + taskId;
        }
        return toJson(task.toDict());
    }

    // 对应 Python 的 list_tasks 函数
    public static String listTasks(String status, String priority, String assignee, String tag) {
        List<Task> tasks = new ArrayList<>(TASK_STORE.values());

        if (status != null && !status.isEmpty()) {
            tasks = tasks.stream().filter(t -> t.getStatus().equals(status)).collect(Collectors.toList());
        }
        if (priority != null && !priority.isEmpty()) {
            tasks = tasks.stream().filter(t -> t.getPriority().equals(priority)).collect(Collectors.toList());
        }
        if (assignee != null && !assignee.isEmpty()) {
            tasks = tasks.stream().filter(t -> t.getAssignee().equals(assignee)).collect(Collectors.toList());
        }
        if (tag != null && !tag.isEmpty()) {
            tasks = tasks.stream().filter(t -> t.getTags().contains(tag)).collect(Collectors.toList());
        }

        if (tasks.isEmpty()) {
            return "未找到符合条件的任务。";
        }

        StringBuilder result = new StringBuilder("共 " + tasks.size() + " 个任务:\n");
        for (Task t : tasks) {
            result.append(String.format("[%s] [%s] %s (ID: %s) - 负责人: %s\n",
                    t.getPriority().toUpperCase(), t.getStatus(), t.getTitle(),
                    t.getId(), t.getAssignee().isEmpty() ? "未分配" : t.getAssignee()));
        }
        return result.toString();
    }

    // 对应 Python 的 update_task 函数
    public static String updateTask(String taskId, String title, String description,
                                    String priority, String status, String assignee,
                                    String dueDate, String tags) {
        Task task = TASK_STORE.get(taskId);
        if (task == null) {
            return "未找到任务: " + taskId;
        }
        if (title != null && !title.isEmpty()) task.setTitle(title);
        if (description != null && !description.isEmpty()) task.setDescription(description);
        if (priority != null && !priority.isEmpty()) task.setPriority(priority);
        if (status != null && !status.isEmpty()) task.setStatus(status);
        if (assignee != null && !assignee.isEmpty()) task.setAssignee(assignee);
        if (dueDate != null && !dueDate.isEmpty()) task.setDueDate(dueDate);
        if (tags != null && !tags.isEmpty()) {
            task.setTags(Arrays.stream(tags.split(","))
                    .map(String::trim)
                    .filter(t -> !t.isEmpty())
                    .collect(Collectors.toList()));
        }
        task.setUpdatedAt(LocalDateTime.now().format(DateTimeFormatter.ISO_LOCAL_DATE_TIME));
        return "任务更新成功！\n" + toJson(task.toDict());
    }

    // 对应 Python 的 delete_task 函数
    public static String deleteTask(String taskId) {
        if (!TASK_STORE.containsKey(taskId)) {
            return "未找到任务: " + taskId;
        }
        TASK_STORE.remove(taskId);
        return "任务 " + taskId + " 已删除。";
    }

    // 对应 Python 的 get_task_stats 函数
    public static String getTaskStats() {
        List<Task> tasks = new ArrayList<>(TASK_STORE.values());
        if (tasks.isEmpty()) {
            return "当前没有任务。";
        }

        Map<String, Object> stats = new LinkedHashMap<>();
        stats.put("total", tasks.size());
        Map<String, Integer> byStatus = new HashMap<>();
        Map<String, Integer> byPriority = new HashMap<>();
        int overdue = 0;
        String today = LocalDateTime.now().toLocalDate().toString();

        for (Task t : tasks) {
            byStatus.merge(t.getStatus(), 1, Integer::sum);
            byPriority.merge(t.getPriority(), 1, Integer::sum);
            if (t.getDueDate() != null && t.getDueDate().compareTo(today) < 0
                    && !t.getStatus().equals("completed") && !t.getStatus().equals("cancelled")) {
                overdue++;
            }
        }
        stats.put("by_status", byStatus);
        stats.put("by_priority", byPriority);
        stats.put("overdue", overdue);
        return toJson(stats);
    }

    private static String toJson(Map<?, ?> map) {
        // 实际项目中使用 Jackson/Gson 等 JSON 库
        return "";
    }
}

======================================================
"""

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
