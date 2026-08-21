import streamlit as st
import os
from langchain_groq import ChatGroq
from duckduckgo_search import DDGS

# --- 1. PAGE SETUP ---
st.set_page_config(page_title="Project Nexus", page_icon="🌐")
st.title("Project Nexus")
st.markdown("How can I help you?")

# --- 2. INITIALIZE BRAIN ---
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

# --- 5. INITIALIZE MEMORY VAULTS ---
if "messages" not in st.session_state:
    st.session_state.messages = []
if "summary" not in st.session_state:
    st.session_state.summary = ""

# Display previous messages with custom avatars
for message in st.session_state.messages:
    avatar_icon = "👤" if message["role"] == "user" else "🌐"
    with st.chat_message(message["role"], avatar=avatar_icon):
        st.markdown(message["content"])

# --- 6. CHAT & SUMMARIZATION LOGIC ---
if typed_text:
    # 1. Save and show user message
    st.session_state.messages.append({"role": "user", "content": typed_text})
    with st.chat_message("user", avatar="👤"):
        st.markdown(typed_text)

    # 2. Trigger Auto-Summarization if chat history gets too long
    # This keeps your token count lightweight to prevent Error 429!
    if len(st.session_state.messages) > 4:
        with st.spinner("Compressing memory to save tokens..."):
            # Turn current messages + existing summary into a new summary string
            history_text = "\n".join([f"{m['role']}: {m['content']}" for m in st.session_state.messages])
            summary_prompt = (
                f"Progressively summarize the conversation so far. "
                f"Current summary: {st.session_state.summary}\n\n"
                f"New conversation data to add:\n{history_text}\n\n"
                f"Write a concise paragraph capturing essential facts."
            )
            st.session_state.summary = llm.invoke(summary_prompt).content
            
            # Wipe out old messages from memory so they stop costing tokens
            st.session_state.messages = st.session_state.messages[-2:]

    # 3. Build the payload for the AI brain with your exact system prompt
    system_instruction = (
        "You are an AI assistant named Project Nexus. Assist users with anything. "
        "For news/weather/facts, start with 'SEARCH: '. Otherwise, be like a human assistant "
        "but dont be brief but dont be a chatter box."
    )
    
    # Insert the compressed background history summary directly into the system brain
    if st.session_state.summary:
        system_instruction += f" Background history context of this chat: {st.session_state.summary}"

    chat_history = [{"role": "system", "content": system_instruction}]
    
    # Append the remaining active messages
    for msg in st.session_state.messages:
        chat_history.append({"role": msg["role"], "content": msg["content"]})

    # 4. Generate response
    with st.chat_message("assistant", avatar="🌐"):
        with st.spinner("Thinking..."):
            response = llm.invoke(chat_history)
            content = response.content

            # Handle web search triggers
            if "SEARCH:" in content:
                topic = content.split("SEARCH:")[1].strip()
                st.write(f"*(Searching for {topic}...)*")
                web_info = quick_search(topic)
                
                chat_history.append({"role": "system", "content": f"Search results for context: {web_info}"})
                content = llm.invoke(chat_history).content

            st.markdown(content)
            st.session_state.messages.append({"role": "assistant", "content": content})
