# src/utils/vectorstore_setup.py
import os
import re
import requests
import streamlit as st
import openai  # Import the openai library to catch the specific error
from langchain_core.documents import Document
from langchain_openai import OpenAIEmbeddings
from langchain_chroma import Chroma

# --- Path Correction ---
_CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
_SRC_DIR = os.path.dirname(_CURRENT_DIR)
_PROJECT_ROOT = os.path.dirname(_SRC_DIR)
DB_DIR = os.path.join(_PROJECT_ROOT, "db")

class VectorStoreRetriever:
    """A retriever that encapsulates a Chroma vector store."""
    def __init__(self, vector_store: Chroma):
        self.vector_store = vector_store

    def query(self, query: str, k: int = 5) -> list[Document]:
        return self.vector_store.similarity_search(query, k=k)

@st.cache_resource
def setup_vector_store():
    """Sets up the Chroma vector store and handles potential API quota errors gracefully."""
    with st.spinner("Initializing policy document retriever..."):
        response = requests.get("https://storage.googleapis.com/benchmarks-artifacts/travel-db/swiss_faq.md")
        response.raise_for_status()
        faq_text = response.text
        docs_as_strings = re.split(r"(?=\n##)", faq_text)
        docs = [Document(page_content=txt) for txt in docs_as_strings]
    
    persist_directory = os.path.join(DB_DIR, "chroma_db_faq")
    
    try:
        # We always need an embedding function to query the DB, so we try to initialize it.
        embeddings = OpenAIEmbeddings(model="text-embedding-3-small")

        if os.path.exists(persist_directory):
            # Load existing store
            vector_store = Chroma(persist_directory=persist_directory, embedding_function=embeddings)
        else:
            # Create new store if it doesn't exist
            st.info("No existing vector store found. Creating a new one...")
            vector_store = Chroma.from_documents(
                documents=docs,
                embedding=embeddings,
                persist_directory=persist_directory,
            )
        return VectorStoreRetriever(vector_store)

    except openai.RateLimitError:
        # If we hit a rate limit error, it's a billing/quota issue.
        st.error(
            "OpenAI API Error: You have exceeded your current quota. "
            "Please check your OpenAI plan and billing details to continue using the policy lookup tool. "
            "The application cannot start without a valid API key.",
            icon="🚨"
        )
        # We can't proceed, so we stop the app gracefully.
        st.stop()
    except Exception as e:
        # Catch other potential errors during setup
        st.error(f"An unexpected error occurred during vector store setup: {e}", icon="🚨")
        st.stop()