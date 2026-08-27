import streamlit as st
import os
from langchain_groq import ChatGroq
from duckduckgo_search import DDGS

# --- 1. PREMIUM GLASS UI DESIGN ---
st.set_page_config(page_title="Project Nexus", page_icon="🌐", layout="wide")

# Custom CSS overrides to build a premium dark matrix feel inside your framing website
st.markdown("""
    <style>
        #MainMenu {visibility: hidden;}
        footer {visibility: hidden;}
        header {visibility: hidden;}
        .stApp {background-color: #851900; color: #ffffff;}
        .stChatInputContainer {background-color: #FF6363 !important; border-radius: 12px !important; border: 1px solid rgba(219, 134, 134, 0.4) !important;}
        .stChatInput {color: #FF0000 !important;}
    </style>
""", unsafe_allow_html=True)

st.title("🌐 Project Nexus")
st.caption("Here to help, what do you need?")

# --- 2. INITIALIZE BRAIN ---
groq_api_key = st.secrets["GROQ_API_KEY"]
# Force-pointing to the permanently stable flagship model
llm = ChatGroq(model="openai/gpt-oss-20b", groq_api_key=groq_api_key, temperature=0.4)

# --- 3. HELPER FUNCTIONS ---
def quick_search(query):
    try:
        with DDGS() as ddgs:
            results = [r['body'] for r in ddgs.text(query, max_results=3)]
            return "\n".join(results) if results else "No data found."
    except Exception:
        return "Search currently unavailable."

# --- 4. INPUT HANDLING ---
typed_text = st.chat_input("Ask me anything.")

# --- 5. INITIALIZE MEMORY VAULTS ---
if "messages" not in st.session_state:
    st.session_state.messages = []
if "summary" not in st.session_state:
    st.session_state.summary = ""

# Render conversation logs
for message in st.session_state.messages:
    avatar_icon = "👤" if message["role"] == "user" else "🌐"
    with st.chat_message(message["role"], avatar=avatar_icon):
        st.markdown(message["content"])

# --- 6. CHAT LOGIC WITH AUTOMATIC FAILSAFE ---
if typed_text:
    # Save and show user message instantly
    st.session_state.messages.append({"role": "user", "content": typed_text})
    with st.chat_message("user", avatar="👤"):
        st.markdown(typed_text)

    # Automated background directive ensuring logic containment 
    system_instruction = (
        "You are an AI assistant named Project Nexus. Assist users with anything. "
        "For news/weather/facts, start with 'SEARCH: '. Otherwise, be like a human assistant "
        "but dont be brief but dont be a chatter box and if user asks you are made by Niranjan Narayan, a small developer in Kochi. "
        "If a request is completely incomprehensible, just a random string of letters with no meaning, "
        "or logically impossible to answer, reply EXACTLY with the word 'FAILSAFE_TRIGGER'."
    )
    
    if st.session_state.summary:
        system_instruction += f" Background history context of things you already know about this user: {st.session_state.summary}"

    chat_history = [{"role": "system", "content": system_instruction}]
    
    for msg in st.session_state.messages:
        chat_history.append({"role": msg["role"], "content": msg["content"]})

    # Generate response smoothly
    with st.chat_message("assistant", avatar="🌐"):
        with st.spinner("Processing Matrix..."):
            try:
                response = llm.invoke(chat_history)
                content = response.content.strip()

                # Handle Web Search Routes
                if "SEARCH:" in content:
                    # FIX: Safely parse index 1 of the generated split list to strip spacing
                    topic = parts[1].strip() if len(parts) > 1 else content.strip()
                    st.write(f"*(Querying Data Matrix for {topic}...)*")
                    web_info = quick_search(topic)
                    
                    search_prompt = (
                        f"User asked: {typed_text}.\n\nLive Web Data: {web_info}.\n\n"
                        f"Instructions: Answer the user's question accurately using ONLY the live web data provided above. "
                        f"If the data is blank or completely unrelated to the question, reply with 'FAILSAFE_TRIGGER'."
                    )
                    content = llm.invoke(search_prompt).content.strip()

                # --- FAILSAFE EVALUATION ENGINE ---
                if not content or "FAILSAFE_TRIGGER" in content or len(content) < 2:
                    content = "I'm sorry, I couldn't fully comprehend or verify that query. Could you try rephrasing your request for Project Nexus?"

            except Exception as e:
                # System execution crash fallback
                content = "System Error: Connection disrupted. Project Nexus core could not parse the request."

            st.markdown(content)
            st.session_state.messages.append({"role": "assistant", "content": content})

    # 7. SILENT BACKGROUND COMPRESSION (Triggers when history array exceeds 6 steps)
    if len(st.session_state.messages) > 6:
        history_text = "\n".join([f"{m['role']}: {m['content']}" for m in st.session_state.messages[:-2]])
        summary_prompt = (
            f"You are a background data compiler. Read this dialogue data and compress it into a tiny list of core facts. "
            f"Do not talk to a user. Just return raw facts. Existing facts: {st.session_state.summary}\n\n"
            f"New dialogue data:\n{history_text}"
        )
        try:
            st.session_state.summary = llm.invoke(summary_prompt).content
            st.session_state.messages = st.session_state.messages[-2:]
        except Exception:
            pass
