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