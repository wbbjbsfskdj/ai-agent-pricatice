"""
【文件意义】
MCP 天气技能 - 演示如何通过 MCP 协议连接远程服务获取天气数据。

在项目中的作用：
1. 作为 MCP（Model Context Protocol）客户端示例，展示如何连接外部 MCP 服务器
2. 使用 MultiServerMCPClient 启动 mcp_server.py 子进程，通过 stdio 通信
3. 将远程 MCP 服务暴露的工具转换为 LangChain 工具格式，供 Agent 统一调用
4. 提供全局单例管理，避免重复初始化 MCP 客户端
5. 提供 close_mcp_client() 方法，确保程序退出时清理子进程资源

MCP 协议说明：
- MCP 是 Anthropic 提出的模型上下文协议，允许 LLM 通过统一接口调用外部服务
- 本项目中天气服务是一个独立的 MCP Server（mcp_server.py），通过 stdio 传输 JSON-RPC 消息
"""
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