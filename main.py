import streamlit as st
import os
from rag_engine import load_and_index_docs, get_rag_chain
from dotenv import load_dotenv
from langchain_core.messages import AIMessage, HumanMessage

# Load environment variables
load_dotenv()

st.set_page_config(page_title="FAQ Chatbot", page_icon="🤖")

st.title("🤖 FAQ Chatbot (English/Kiswahili)")

# Check API Key
if not os.getenv("OPENAI_API_KEY"):
    st.error("Please set your OPENAI_API_KEY in the .env file.")
    st.stop()

# Sidebar for Admin/Indexing
with st.sidebar:
    st.header("Admin Controls")
    if st.button("Re-index Documents"):
        with st.spinner("Indexing documents..."):
            result = load_and_index_docs("docs")
            st.success(result)
            st.cache_resource.clear()

if "messages" not in st.session_state:
    welcome_msg = "Karibu!" # TODO: needs to change
    st.session_state.messages = [
        {"role": "assistant", "content": welcome_msg}
    ]

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

if prompt := st.chat_input("Ask a question (Uliza swali):"):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)


    chat_history = []
    for msg in st.session_state.messages[:-1]: 
        if msg["role"] == "user":
            chat_history.append(HumanMessage(content=msg["content"]))
        elif msg["role"] == "assistant":
            chat_history.append(AIMessage(content=msg["content"]))

    # Generate Answer
    with st.chat_message("assistant"):
        rag_chain = get_rag_chain()
        if rag_chain:
            with st.spinner("Thinking..."):
                try:
                    response_text = rag_chain.invoke({
                        "input": prompt,
                        "chat_history": chat_history
                    })
                    st.markdown(response_text)
                    st.session_state.messages.append({"role": "assistant", "content": response_text})
                except Exception as e:
                    st.error(f"Error: {e}")
        else:
            st.warning("No index found. Please index documents from the sidebar first.")
