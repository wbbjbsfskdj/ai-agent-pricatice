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