import sys
from langchain_mcp_adapters.client import MultiServerMCPClient

mcp_client = None  # 全局引用，确保只初始化一次

async def get_weather_tools():
    global mcp_client
    if mcp_client is None:
        mcp_client = MultiServerMCPClient({
            "weather": {
                "command": sys.executable,
                "args": ["mcp_server.py"],
                "transport": "stdio",
            }
        })
    return await mcp_client.get_tools()

async def close_mcp_client():
    global mcp_client
    if mcp_client:
        await mcp_client.close()
        mcp_client = None