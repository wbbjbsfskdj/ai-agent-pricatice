import os
import sys
import asyncio
import logging
from dotenv import load_dotenv

load_dotenv()
logging.getLogger("mcp").setLevel(logging.WARNING)

# 1. 初始化阿里百炼聊天模型
from langchain_openai import ChatOpenAI

llm = ChatOpenAI(
    model="qwen-plus",
    openai_api_key=os.getenv("DASHSCOPE_API_KEY"),
    openai_api_base="https://dashscope.aliyuncs.com/compatible-mode/v1",
    temperature=0.2,
)

# 2. 构建 RAG 向量库和检索器
from langchain_community.document_loaders import TextLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.embeddings import DashScopeEmbeddings
from langchain_community.vectorstores import Chroma

loader = TextLoader("./data/knowledge.txt", encoding="utf-8")
documents = loader.load()
text_splitter = RecursiveCharacterTextSplitter(chunk_size=200, chunk_overlap=20)
docs = text_splitter.split_documents(documents)

embeddings = DashScopeEmbeddings(
    model="text-embedding-v2",
    dashscope_api_key=os.getenv("DASHSCOPE_API_KEY"),
)
vectorstore = Chroma.from_documents(docs, embeddings, persist_directory="./chroma_db")
retriever = vectorstore.as_retriever(search_kwargs={"k": 2})

# 3. 加载所有技能工具
from skills import load_all_tools, close_mcp_client

# 4. 企业级系统提示词
SYSTEM_PROMPT = """你是一个企业级智能助手，具备以下能力：

📋 **任务管理**：创建、查询、更新、删除任务，支持优先级和状态管理
📧 **邮件处理**：创建邮件、使用模板、分类、摘要
📊 **数据分析**：统计分析、异常检测、趋势分析、数据对比
📅 **日程管理**：创建日程、冲突检测、日程查询
📄 **文档处理**：信息提取、格式转换、报告模板生成
📝 **日志记录**：操作日志记录、查询、统计分析
🔍 **知识检索**：基于 RAG 的内部知识库搜索
🌤️ **天气查询**：实时天气查询
🧮 **办公工具**：计算器、字符串处理

请根据用户需求智能选择合适的工具，并提供专业、准确的回复。"""


async def main():
    all_tools = await load_all_tools(retriever)

    # 5. 创建增强版 ReAct Agent
    from langgraph.prebuilt import create_react_agent
    agent_executor = create_react_agent(
        llm,
        all_tools,
        prompt=SYSTEM_PROMPT
    )

    print("=" * 50)
    print("🏢 企业级智能 Agent 已启动！")
    print("=" * 50)
    print("\n可用功能：")
    print("  📋 任务管理  📧 邮件处理  📊 数据分析")
    print("  📅 日程管理  📄 文档处理  📝 日志记录")
    print("  🔍 知识检索  🌤️ 天气查询  🧮 办公工具")
    print("\n输入问题开始对话，输入 'exit' 退出。")
    
    # 对话历史（简单记忆）
    conversation_history = []
    
    try:
        while True:
            user_input = input("\n👤 你：").strip()
            if not user_input:
                continue
            if user_input.lower() == "exit":
                break

            # 构建消息（包含历史上下文）
            messages = [("system", SYSTEM_PROMPT)]
            messages.extend(conversation_history[-6:])  # 保留最近3轮对话
            messages.append(("user", user_input))

            response = await agent_executor.ainvoke({"messages": messages})
            response_messages = response.get("messages", [])
            
            # 提取 AI 回复
            answer = None
            for msg in reversed(response_messages):
                if hasattr(msg, "type") and msg.type == "ai" and hasattr(msg, "content"):
                    content = msg.content
                    if content and isinstance(content, str) and content.strip():
                        answer = content
                        break
            
            if answer:
                print(f"\n🤖 Agent：{answer}")
                # 更新对话历史
                conversation_history.append(("user", user_input))
                conversation_history.append(("assistant", answer))
            else:
                print("🤖 Agent 未生成有效回复。")
                
    finally:
        await close_mcp_client()  # 释放 MCP 资源


if __name__ == "__main__":
    asyncio.run(main())
