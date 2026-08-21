import streamlit as st
import os
from langchain_groq import ChatGroq
from duckduckgo_search import DDGS

# --- 1. PAGE SETUP ---
st.set_page_config(page_title="Project Nexus", page_icon="🌐")
st.title("Project Nexus")
st.markdown("How can I help you?")

# --- 2. INITIALIZE BRAIN (Groq Cloud API) ---
# It reads your secret API key safely from Streamlit's settings
groq_api_key = st.secrets["GROQ_API_KEY"]
llm = ChatGroq(model="llama-3.1-8b-instant", groq_api_key=groq_api_key, temperature=0.7)
# --- 3. HELPER FUNCTIONS ---
def quick_search(query):
    try:
        with DDGS() as ddgs:
            results = [r['body'] for r in ddgs.text(query, max_results=3)]
            return "\n".join(results) if results else "No data found."
    except Exception:
        return "Search currently unavailable."

# --- 4. INPUT HANDLING ---
typed_text = st.chat_input("Type your message here...")

# --- 5. CHAT SYSTEM ---
if "messages" not in st.session_state:
    st.session_state.messages = []

# Display previous messages with custom avatars
for message in st.session_state.messages:
    avatar_icon = "👤" if message["role"] == "user" else "🌐"
    with st.chat_message(message["role"], avatar=avatar_icon):
        st.markdown(message["content"])

if typed_text:
    # User message
    st.session_state.messages.append({"role": "user", "content": typed_text})
    with st.chat_message("user", avatar="👤"):
        st.markdown(typed_text)

    # Assistant message
    with st.chat_message("assistant", avatar="🌐"):
        with st.spinner("Thinking..."):
            sys_msg = "You are an AI assistant named Project Nexus. Assist users with anything. For news/weather/facts, start with 'SEARCH: '. Otherwise, be like a human assistant—polite but not too polite."
            response = llm.invoke(f"{sys_msg}\n\nUser: {typed_text}")
            content = response.content

            if "SEARCH:" in content:
                topic = content.split("SEARCH:")[1].strip()
                st.write(f"*(Searching for {topic}...)*")
                web_info = quick_search(topic)
                content = llm.invoke(f"User asked: {typed_text}. Search info: {web_info}. Answer modestly.").content

            st.markdown(content)
            st.session_state.messages.append({"role": "assistant", "content": content})
