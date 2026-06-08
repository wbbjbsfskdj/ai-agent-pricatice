# skills/__init__.py
from .office_skill import tools as office_tools
from .customer_skill import create_customer_tools
from .mcp_weather_skill import get_weather_tools, close_mcp_client


async def load_all_tools(retriever):
    """加载所有本地技能工具和 MCP 工具"""
    # 客户服务工具（需要 retriever）
    customer_tools = create_customer_tools(retriever)

    # 办公工具
    office = office_tools

    # 天气 MCP 工具
    weather_tools = await get_weather_tools()

    # 返回合并后的列表
    return customer_tools + office + weather_tools