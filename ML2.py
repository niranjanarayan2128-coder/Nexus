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

# --- 6. CHAT LOGIC ---
if typed_text:
    # 1. Save and show user message instantly
    st.session_state.messages.append({"role": "user", "content": typed_text})
    with st.chat_message("user", avatar="👤"):
        st.markdown(typed_text)

    # 2. Build the payload for the AI brain with your exact system prompt
    system_instruction = (
        "You are an AI assistant named Project Nexus. Assist users with anything. "
        "For news/weather/facts, start with 'SEARCH: '. Otherwise, be like a human assistant "
        "but dont be brief but dont be a chatter box."
    )
    
    # Safely inject the background history context if it exists
    if st.session_state.summary:
        system_instruction += f" Background history context of things you already know about this user: {st.session_state.summary}"

    chat_history = [{"role": "system", "content": system_instruction}]
    
    # Append current conversation backlog
    for msg in st.session_state.messages:
        chat_history.append({"role": msg["role"], "content": msg["content"]})

    # 3. Generate response smoothly
    with st.chat_message("assistant", avatar="🌐"):
        with st.spinner("Thinking..."):
            response = llm.invoke(chat_history)
            content = response.content

            # Handle web search triggers seamlessly
            if "SEARCH:" in content:
                topic = content.split("SEARCH:")[1].strip()
                st.write(f"*(Searching for {topic}...)*")
                web_info = quick_search(topic)
                
                # Strict data guardrail instructions to eliminate hallucinations
                search_prompt = (
                    f"User asked: {typed_text}.\n\n"
                    f"Live Web Data: {web_info}.\n\n"
                    f"Instructions: Answer the user's question accurately using ONLY the live web data provided above. "
                    f"If your internal training data contradicts the live web data, ignore your training data entirely."
                )
                content = llm.invoke(search_prompt).content

            st.markdown(content)
            st.session_state.messages.append({"role": "assistant", "content": content})

    # 4. SILENT BACKGROUND COMPRESSION (Happens after the chat is displayed!)
    if len(st.session_state.messages) > 6:
        # Turn older logs into a raw data string to pass into the engine secretly
        history_text = "\n".join([f"{m['role']}: {m['content']}" for m in st.session_state.messages[:-2]])
        summary_prompt = (
            f"You are a background data compiler. Read this dialogue data and compress it into a tiny list of core facts. "
            f"Do not talk to a user. Just return raw facts. Existing facts: {st.session_state.summary}\n\n"
            f"New dialogue data:\n{history_text}"
        )
        try:
            # Update background state without rendering anything to the webpage
            st.session_state.summary = llm.invoke(summary_prompt).content
            # Safely trim the message history list so token depth resets
            st.session_state.messages = st.session_state.messages[-2:]
        except Exception:
            pass
