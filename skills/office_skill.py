"""
【文件意义】
办公基础技能 - 提供字符串处理和简单计算等基础工具，作为 Agent 的基础能力补充。

在项目中的作用：
1. 提供 string_length 工具：计算输入文本的字符长度，适用于文本长度校验场景
2. 提供 calculator 工具：执行四则运算（加减乘除），Agent 可直接调用进行数学计算
3. 作为项目中最简单的技能示例，帮助理解 LangChain @tool 装饰器的基本用法
4. 这些基础工具虽然简单，但在实际对话中经常用到（如"这个标题太长了帮我看看多少字"）

注意：calculator 使用 eval() 仅用于学习演示，生产环境应使用安全的数学表达式解析器。
"""
from langchain_core.tools import tool

@tool
def string_length(text: str) -> int:
    """返回输入字符串的长度"""
    return len(text)

@tool
def calculator(expression: str) -> str:
    """执行简单的四则运算，表达式如 '2+3*4'，返回计算结果"""
    try:
        # 安全评估数学表达式（仅限数字和运算符）
        # 注意：生产环境需谨慎，这里仅用于学习
        result = eval(expression)
        return f"计算结果：{result}"
    except Exception as e:
        return f"计算出错：{str(e)}"

# 该技能提供的所有工具列表
tools = [string_length, calculator]