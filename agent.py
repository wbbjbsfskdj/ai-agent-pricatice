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

async def main():
    all_tools = await load_all_tools(retriever)

    # 4. 创建 ReAct Agent
    from langgraph.prebuilt import create_react_agent
    agent_executor = create_react_agent(llm, all_tools)

    print("✅ 你的智能 Agent 已启动！输入问题开始对话，输入 'exit' 退出。")
    try:
        while True:
            user_input = input("\n👤 你：")
            if user_input.lower() == "exit":
                break

            response = await agent_executor.ainvoke({"messages": [("user", user_input)]})
            messages = response.get("messages", [])
            answer = None
            for msg in reversed(messages):
                if hasattr(msg, "type") and msg.type == "ai" and hasattr(msg, "content"):
                    content = msg.content
                    if content and isinstance(content, str) and content.strip():
                        answer = content
                        break
            if answer:
                print(f"🤖 Agent：{answer}")
            else:
                print("🤖 Agent 未生成有效回复，调试信息：")
                for i, msg in enumerate(messages):
                    print(f"  [{i}] {msg.type}: {getattr(msg, 'content', '')}")
    finally:
        await close_mcp_client()  # 释放 MCP 资源

if __name__ == "__main__":
    asyncio.run(main())