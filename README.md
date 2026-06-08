# 企业级 MCP Agent 演示项目

基于 MCP (Model Context Protocol) 和 LangGraph 构建的企业级智能 Agent 系统。

## 功能模块

### 核心能力

| 模块 | 文件 | 功能描述 |
|------|------|----------|
| 📋 任务管理 | `skills/task_management.py` | 任务创建/查询/更新/删除、优先级管理、状态跟踪、统计分析 |
| 📧 邮件处理 | `skills/email_handler.py` | 邮件草稿、模板系统、自动分类、内容摘要 |
| 📊 数据分析 | `skills/data_analyzer.py` | 统计分析、异常检测(IQR/Z-Score)、趋势分析、数据对比 |
| 📅 日程管理 | `skills/schedule_manager.py` | 日程创建/查询、冲突检测、每日日程、提醒设置 |
| 📄 文档处理 | `skills/document_processor.py` | 信息提取(日期/邮箱/电话/URL/金额)、格式转换、报告模板 |
| 📝 日志记录 | `skills/logger.py` | 操作日志、多条件查询、统计分析、用户活动追踪 |

### 原有能力

| 模块 | 文件 | 功能描述 |
|------|------|----------|
| 🔍 知识检索 | `skills/customer_skill.py` | 基于 RAG 的内部知识库搜索 |
| 🌤️ 天气查询 | `skills/mcp_weather_skill.py` | 通过 MCP Server 查询天气 |
| 🧮 办公工具 | `skills/office_skill.py` | 计算器、字符串处理 |

## 快速开始

### 1. 安装依赖

```bash
uv sync
# 或
pip install -e .
```

### 2. 配置环境变量

在 `API.env` 中配置：

```
DASHSCOPE_API_KEY=your_api_key_here
```

### 3. 运行 Agent

```bash
python agent.py
```

## 使用示例

### 任务管理

```
用户：帮我创建一个高优先级任务，标题是"完成Q2报告"，负责人是张三，截止日期2026-06-30
用户：列出所有高优先级任务
用户：获取任务统计信息
```

### 邮件处理

```
用户：用会议邀请模板生成邮件，主题是产品评审，时间是明天下午3点，地点是会议室A
用户：帮我分类这段内容："紧急：请立即处理服务器故障问题"
```

### 数据分析

```
用户：分析这组数据的统计信息：10,20,30,40,50,100,25,35
用户：检测异常值：10,12,11,13,100,12,11
用户：分析趋势：100,120,115,130,145,140,160
```

### 日程管理

```
用户：创建日程，明天上午10点到11点开项目会议，地点会议室B
用户：检查明天下午2点到4点是否有日程冲突
用户：显示2026-06-09的完整日程
```

### 文档处理

```
用户：从这段文本提取邮箱和电话：联系张三zhangsan@example.com或13800138000
用户：生成周报模板
用户：统计这段文字的字数
```

### 日志记录

```
用户：记录一条info级别日志，模块是订单系统，操作是创建订单，用户是admin
用户：查询所有error级别的日志
用户：获取日志统计信息
```

## 项目结构

```
mcp-server-demo/
├── agent.py                    # 主 Agent 入口
├── mcp_server.py               # MCP 天气服务
├── main.py                     # 项目入口
├── pyproject.toml              # 项目配置
├── skills/
│   ├── __init__.py             # 工具加载器
│   ├── task_management.py      # 任务管理
│   ├── email_handler.py        # 邮件处理
│   ├── data_analyzer.py        # 数据分析
│   ├── schedule_manager.py     # 日程管理
│   ├── document_processor.py   # 文档处理
│   ├── logger.py               # 日志记录
│   ├── customer_skill.py       # 知识检索
│   ├── mcp_weather_skill.py    # MCP 天气
│   └── office_skill.py         # 办公工具
├── data/
│   └── knowledge.txt           # 知识库数据
└── chroma_db/                  # 向量数据库
```

## 技术栈

- **LangChain**: LLM 框架
- **LangGraph**: Agent 编排
- **MCP**: Model Context Protocol
- **ChromaDB**: 向量数据库
- **DashScope**: 阿里百炼大模型

## 扩展说明

### v0.2.0 新增企业级功能

1. **任务管理系统** - 完整的 CRUD 操作，支持优先级、状态、标签、负责人
2. **邮件处理系统** - 模板引擎、自动分类、内容摘要
3. **数据分析引擎** - 统计计算、异常检测、趋势分析
4. **日程管理系统** - 冲突检测、每日视图、提醒设置
5. **文档处理工具** - 信息提取、格式转换、模板生成
6. **日志记录系统** - 操作审计、多条件查询、统计分析

### 架构特点

- 所有工具基于 LangChain Tool 规范
- 支持 MCP 协议扩展
- 模块化设计，易于添加新技能
- 内存存储（生产环境可替换为数据库）
