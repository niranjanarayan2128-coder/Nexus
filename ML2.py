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
llm = ChatGroq(model="openai/gpt-oss-20b", groq_api_key=groq_api_key, temperature=0.7)
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
    # 1. Save and show user message
    st.session_state.messages.append({"role": "user", "content": typed_text})
    with st.chat_message("user", avatar="👤"):
        st.markdown(typed_text)

    # 2. Build the history payload for the AI brain
    # We load the system prompt first, then append all previous messages
    chat_history = [
        {"role": "system", "content": "You are an AI assistant named Project Nexus. Assist users with anything. For news/weather/facts, start with 'SEARCH: '. Otherwise, be like a human assistant but dont be brief but dont be a chatter box"}
    ]
    
    for msg in st.session_state.messages:
        chat_history.append({"role": msg["role"], "content": msg["content"]})

    # 3. Assistant response block
    with st.chat_message("assistant", avatar="🌐"):
        with st.spinner("Thinking..."):
            # We send the WHOLE chat_history array now instead of just a text string
            response = llm.invoke(chat_history)
            content = response.content

            # Handle web search triggers
            if "SEARCH:" in content:
                topic = content.split("SEARCH:")[1].strip()
                st.write(f"*(Searching for {topic}...)*")
                web_info = quick_search(topic)
                
                # Append the search result to context and re-invoke
                chat_history.append({"role": "system", "content": f"Search results for context: {web_info}"})
                content = llm.invoke(chat_history).content

            st.markdown(content)
            st.session_state.messages.append({"role": "assistant", "content": content})
