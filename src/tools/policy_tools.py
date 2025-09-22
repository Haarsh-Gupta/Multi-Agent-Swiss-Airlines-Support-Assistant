# src/tools/policy_tool.py
from langchain_core.tools import tool
from utils.vectorstore_setup import setup_vector_store

retriever = setup_vector_store()

@tool
def lookup_policy(query: str) -> str:
    """Consult the company policies to check whether certain options are permitted."""
    docs_result = retriever.query(query, k=2)
    return "\n\n".join([doc.page_content for doc in docs_result])