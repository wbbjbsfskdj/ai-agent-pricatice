"""
【文件意义】
项目入口文件 - Python 包的标准入口，目前仅包含基础打印语句。

在项目中的作用：
1. 作为 Python 包的标准入口点（pyproject.toml 中配置的 entry point）
2. 当前仅打印欢迎信息，实际项目启动应运行 agent.py
3. 保留此文件是为了符合 Python 包规范，便于将来打包发布
"""
def main():
    print("Hello from mcp-server-demo!")


if __name__ == "__main__":
    main()
