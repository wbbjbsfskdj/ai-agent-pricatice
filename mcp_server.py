"""
【文件意义】
MCP 天气服务器 - 一个独立的 MCP Server，提供天气查询服务。

在项目中的作用：
1. 使用 FastMCP 框架创建一个独立的 MCP 服务器，提供 get_weather 工具
2. 返回模拟天气数据（城市、温度、天气状况、湿度），用于演示 MCP 协议的工作方式
3. 通过 stdio 传输（transport="stdio"）与客户端通信，是 MCP 最简单的通信模式
4. 被 mcp_weather_skill.py 作为子进程启动，展示 MCP 客户端-服务器架构

MCP 架构说明：
- mcp_server.py 是服务端：定义工具并等待客户端连接
- mcp_weather_skill.py 是客户端：启动子进程连接服务端，获取工具列表
- 两者通过 stdio 传输 JSON-RPC 消息，实现进程间通信
"""
import json
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("weather-server")

@mcp.tool()
def get_weather(city: str = "北京") -> str:
    """查询指定城市的实时天气（模拟数据）"""
    weather_data = {
        "city": city,
        "temperature": "25°C",
        "condition": "晴天",
        "humidity": "45%"
    }
    return json.dumps(weather_data, ensure_ascii=False)

if __name__ == "__main__":
    mcp.run(transport="stdio")