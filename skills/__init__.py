"""
【文件意义】
工具注册中心 - 统一管理所有技能的加载和导出，是 Agent 与各个工具模块之间的桥梁。

在项目中的作用：
1. 集中导入所有本地技能工具（office_skill、customer_skill、mcp_weather_skill）
2. 集中导入所有企业级工具（task_management、email_handler、data_analyzer、schedule_manager、document_processor、logger）
3. 提供 load_all_tools() 异步函数：统一初始化所有工具，包括需要 retriever 的客户服务工具和需要 MCP 连接的天气工具
4. 将所有工具合并为一个列表返回，供 agent.py 直接传入 create_react_agent
5. 提供 close_mcp_client() 函数：优雅关闭 MCP 客户端连接，释放资源

设计意义：
- 新增工具只需在此文件 import 并加入列表，无需修改 agent.py，符合开闭原则
- 区分本地工具和远程 MCP 工具，远程工具需要异步初始化
"""
# skills/__init__.py
from .office_skill import tools as office_tools
from .customer_skill import create_customer_tools
from .mcp_weather_skill import get_weather_tools, close_mcp_client

# 企业级工具
from .task_management import tools as task_tools
from .email_handler import tools as email_tools
from .data_analyzer import tools as data_analyzer_tools
from .schedule_manager import tools as schedule_tools
from .document_processor import tools as document_tools
from .logger import tools as logger_tools


async def load_all_tools(retriever):
    """加载所有本地技能工具和 MCP 工具"""
    # 客户服务工具（需要 retriever）
    customer_tools = create_customer_tools(retriever)

    # 办公工具
    office = office_tools

    # 天气 MCP 工具
    weather_tools = await get_weather_tools()

    # 企业级工具
    enterprise_tools = (
        task_tools +
        email_tools +
        data_analyzer_tools +
        schedule_tools +
        document_tools +
        logger_tools
    )

    # 返回合并后的列表
    return customer_tools + office + weather_tools + enterprise_tools