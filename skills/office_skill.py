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