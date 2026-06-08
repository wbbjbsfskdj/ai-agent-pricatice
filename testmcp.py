# server.py
from mcp.server.fastmcp import FastMCP

# 创建一个 MCP 服务器
mcp = FastMCP("Demo")


# 添加一个加法工具
@mcp.tool()
def add(a: int, b: int) -> int:
    """添加两个数字"""
    return a + b


# 添加一个动态问候资源
@mcp.resource("greeting://{name}")
def get_greeting(name: str) -> str:
    """获取个性化问候"""
    return f"Hello, {name}!"