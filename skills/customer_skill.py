"""
【文件意义】
客户服务技能 - 为 Agent 提供内部知识库检索能力，用于回答产品相关问题。

在项目中的作用：
1. 提供 knowledge_search 工具，接收用户查询文本，通过 RAG 检索器在知识库中搜索相关内容
2. 依赖外部传入的 retriever（由 agent.py 构建的 ChromaDB 检索器），通过工厂函数 create_customer_tools 注入
3. 将检索到的文档片段格式化后返回，供 LLM 基于检索结果生成回答
4. 这是 RAG（检索增强生成）的核心环节：用户提问 → 向量检索 → 返回相关文档 → LLM 生成回答

工作流程：
用户问"产品保修期多久？" → Agent 调用 knowledge_search → retriever 在向量库中检索 → 返回匹配文档 → LLM 基于文档回答
"""
from langchain_core.tools import tool

def create_customer_tools(retriever):
    @tool
    def knowledge_search(query: str) -> str:
        """在内部产品知识库中搜索相关信息，例如产品功能、保修政策等。"""
        docs = retriever.invoke(query)
        if not docs:
            return "未找到相关信息。"
        return "\n\n".join([f"【来源】\n{d.page_content}" for d in docs])

    return [knowledge_search]