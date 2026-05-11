import os
import ssl
from dotenv import load_dotenv

from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain_community.vectorstores import FAISS
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough, RunnableBranch

load_dotenv()

# ── FIX: stable FAISS path ─────────────────────
FAISS_INDEX_PATH = os.path.join(os.path.dirname(__file__), "faiss_index")


# ⚠️ NOTE: removed unsafe SSL bypass (it causes OpenAI crashes)


def load_and_index_docs(docs_folder):
    documents = []

    if not os.path.exists(docs_folder):
        return "Docs folder not found."

    files = [f for f in os.listdir(docs_folder) if f.endswith(".pdf")]
    if not files:
        return "No PDF files found."

    for file in files:
        file_path = os.path.join(docs_folder, file)
        loader = PyPDFLoader(file_path)
        documents.extend(loader.load())

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=200
    )

    splits = splitter.split_documents(documents)

    if not splits:
        return "No text extracted."

    embeddings = OpenAIEmbeddings()

    vectorstore = FAISS.from_documents(splits, embeddings)
    vectorstore.save_local(FAISS_INDEX_PATH)

    return f"Indexed {len(documents)} docs into {len(splits)} chunks."


def format_docs(docs):
    return "\n\n".join(d.page_content for d in docs)


def get_rag_chain():
    try:
        print("📦 Loading FAISS from:", FAISS_INDEX_PATH)

        if not os.path.exists(FAISS_INDEX_PATH):
            print("❌ FAISS folder not found")
            return None

        embeddings = OpenAIEmbeddings()

        vectorstore = FAISS.load_local(
            FAISS_INDEX_PATH,
            embeddings,
            allow_dangerous_deserialization=True
        )

        retriever = vectorstore.as_retriever(search_kwargs={"k": 5})

        llm = ChatOpenAI(model="gpt-4o", temperature=0)

        # ── Question reformulation ─────────────
        contextualize_q_prompt = ChatPromptTemplate.from_messages([
            ("system",
             "Rewrite the question into standalone form using chat history. "
             "Do NOT answer it."),
            MessagesPlaceholder("chat_history"),
            ("human", "{input}")
        ])

        contextualize_chain = contextualize_q_prompt | llm | StrOutputParser()

        # ── QA prompt ──────────────────────────
        qa_prompt = ChatPromptTemplate.from_messages([
            ("system",
             "You are a helpful assistant. Use context to answer concisely (max 3 sentences). "
             "If unknown, say you don't know.\n\nContext:\n{context}"),
            MessagesPlaceholder("chat_history"),
            ("human", "{input}")
        ])

        # ── SAFE PIPELINE ──────────────────────
        chain = (
            RunnablePassthrough.assign(
                standalone_question=RunnableBranch(
                    (
                        lambda x: x.get("chat_history"),
                        contextualize_chain
                    ),
                    lambda x: x["input"]
                )
            )
            | RunnablePassthrough.assign(
                context=lambda x: format_docs(
                    retriever.invoke(x["standalone_question"])
                )
            )
            | qa_prompt
            | llm
            | StrOutputParser()
        )

        print("✅ RAG chain ready")
        return chain

    except Exception as e:
        print("❌ RAG INIT ERROR:", repr(e))
        return None