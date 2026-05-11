import streamlit as st
import os
from rag_engine import load_and_index_docs, get_rag_chain
from dotenv import load_dotenv
from langchain_core.messages import AIMessage, HumanMessage
import random

# -----------------------
# Load environment variables
# -----------------------
load_dotenv()

# -----------------------
# Page Config
# -----------------------
st.set_page_config(page_title="ZHSF AGENT", page_icon="🤖")
st.title("🤖 FAQ Chatbot (English/Kiswahili)")

# -----------------------
# Check API Key
# -----------------------
if not os.getenv("OPENAI_API_KEY"):
    st.error("Please set your OPENAI_API_KEY in the .env file.")
    st.stop()

# -----------------------
# Sidebar for Admin/Indexing
# -----------------------
with st.sidebar:
    st.header("Admin Controls")
    if st.button("Re-index Documents"):
        with st.spinner("Indexing documents..."):
            result = load_and_index_docs("docs")
            st.success(result)
            st.cache_resource.clear()

# -----------------------
# Initialize chat session
# -----------------------
if "messages" not in st.session_state:
    welcome_messages = [
        "Karibu ZHSF! 👋 Kuwa na bima ya afya kunahakikisha matibabu bora wakati wowote unahitaji. Uliza swali lolote na nitakusaidia.",
        "Hello! 👋 Having health insurance ensures you get quality care when needed. Ask me anything!",
        "Karibu! 🌿 Health insurance protects you and your family from unexpected medical costs. Ask me anything!",
        "Hi there! 👋 Health insurance is important to stay safe from high medical bills. Ask a question!"
    ]
    st.session_state.messages = [
        {"role": "assistant", "content": random.choice(welcome_messages)}
    ]

# -----------------------
# Predefined Questions
# -----------------------
predefined_answers = {
    "who owns you": "ZHSF",
    "what is your name": "I am ZHSF CHAT Agent 🤖",
    "how are you": "I'm doing great! How can I help you today?",
    # Add more predefined Q&A here
}

def normalize_text(text):
    return text.strip().lower()

# -----------------------
# End-chat messages to encourage health insurance
# -----------------------
end_chat_messages = [
    "Asante kwa kuzungumza nami! 🌿 Bima ya afya inakulinda na familia yako dhidi ya gharama zisizotarajiwa.",
    "Kumbuka, kuwa na bima ya afya ni njia rahisi ya kupata matibabu bila wasiwasi.",
    "Bima ya afya inahakikisha unapata huduma bora wakati wowote unapoihitaji. 🏥",
    "Hakikisha amani ya akili yako leo, jiandikishe kwenye bima ya afya. ✅",
    "Bima ya afya inakusaidia kulipa gharama ghafi za matibabu bila mzigo mkubwa wa kifedha.",
    "Huwezi kujua kesho ni nini, lakini bima ya afya inakulinda leo. 🌟",
    "Fikiria familia yako, bima ya afya inahakikisha kila mmoja anapata matibabu bora.",
    "Kuwa na bima ya afya ni hatua ya busara kuelekea maisha yenye usalama na amani.",
    "Matibabu bora yanaweza kuwa ghali, lakini bima ya afya inakulinda. 💚",
    "Usisubiri ugonjwa ujafika; bima ya afya inakupa amani ya akili na usalama wa kifedha."
]

# -----------------------
# Display chat messages
# -----------------------
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# -----------------------
# Chat input handling
# -----------------------
if prompt := st.chat_input("Ask a question (Uliza swali):"):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # Normalize input for predefined matching
    normalized_prompt = normalize_text(prompt)

    # Check if the user asked a predefined question
    if normalized_prompt in predefined_answers:
        response_text = predefined_answers[normalized_prompt]
        with st.chat_message("assistant"):
            st.markdown(response_text)
        st.session_state.messages.append({"role": "assistant", "content": response_text})
    else:
        # Otherwise, use RAG engine
        chat_history = []
        for msg in st.session_state.messages[:-1]:
            if msg["role"] == "user":
                chat_history.append(HumanMessage(content=msg["content"]))
            elif msg["role"] == "assistant":
                chat_history.append(AIMessage(content=msg["content"]))

        with st.chat_message("assistant"):
            rag_chain = get_rag_chain()
            if rag_chain:
                with st.spinner("Thinking..."):
                    try:
                        response = rag_chain.invoke({
                            "input": prompt,
                            "chat_history": chat_history
                        })
                        # Handle dict or string
                        response_text = response.get("answer", str(response)) if isinstance(response, dict) else str(response)
                        st.markdown(response_text)
                        st.session_state.messages.append({"role": "assistant", "content": response_text})
                    except Exception as e:
                        st.error(f"Error: {e}")
            else:
                st.warning("No index found. Please index documents from the sidebar first.")

# -----------------------
# Optional: End-chat button
# -----------------------
if st.button("End Chat"):
    final_msg = random.choice(end_chat_messages)
    with st.chat_message("assistant"):
        st.markdown(final_msg)
    st.session_state.messages.append({"role": "assistant", "content": final_msg})
