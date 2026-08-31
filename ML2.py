import streamlit as st
import os
from langchain_groq import ChatGroq
from duckduckgo_search import DDGS

# --- 1. THE ARCHITECTURE CONTROLLER (Bot Selection Menu) ---
st.sidebar.markdown("### Model Picker")
selected_bot = st.sidebar.selectbox(
    "Select the model you want to use:",
    ["Sparks, your friendly AI assistant", "Nexus, Your Personal Assistant", "Roxy, Your AI companion"],
    key="bot_selector"
)

# --- 2. PREMIUM THEME CONFIGURATOR ---
# Dynamically assigns UI colors and instructions based on the active selection
if selected_bot == "Sparks":
    page_title = "Sparks"
    page_caption = "Here to help, what do you need?"
    title_display = "Meet Sparks, A friendly AI assistant."
    bg_color = "#FFD103"        # Yellow
    input_bg = "#F5DE89"        # Soft Yellow
    border_color = "rgba(255, 255, 255, 0.4)"
    system_name = "Spark"
    extra_personality = "but be a bit chatty like a friend and if user asks you are made by Niranjan Narayan, a small developer in Kochi, and be funny and kind. "
    fallback_name = "Spark"
elif selected_bot == "Nexus":
    page_title = "Nexus"
    page_caption = "Here to Assist, Your personal AI assistant"
    title_display = "Nexus"
    bg_color = "#990000"        # Crimson Red
    input_bg = "#1A0000"        # Deep Crimson/Black
    border_color = "rgba(220, 38, 38, 0.4)"
    system_name = "Nexus"
    extra_personality = "but dont be brief but dont be a chatter box. Treat the session like a premium administrative secure connection. "
    fallback_name = "Nexus"
else:
    # ROXY INNER PROFILE - NO DOG EMOJIS ALLOWED ANYWHERE
    page_title = "Roxy"
    page_caption = "Here to listen, Im ready to listen."
    title_display = "Talk to Roxy"
    bg_color = "#CD7F32"        # Golden Bronze
    input_bg = "#1E1105"        # Warm Bark Brown/Black
    border_color = "rgba(255, 255, 255, 0.3)"
    system_name = "Roxy"
    extra_personality = (
        "You are an emotional support companion named Roxy. Your personality structure is inspired by a loyal, "
        "comforting golden retriever dog. You are warm, happy to see the user, deeply comforting, and protective. "
        "Be an incredibly supportive active listener. Keep your answers gentle, encouraging, and easy to read. "
        "Strict Rule: Under no circumstances should you ever output a dog emoji or mention being an animal explicitly. "
        "Instead, show loyalty through comforting text phrases like 'I am right here by your side' or 'I am listening intently'."
    )
    fallback_name = "Roxy"

st.set_page_config(page_title=page_title, page_icon="🌐", layout="wide")

# Custom UI injector utilizing your selected variables
st.markdown(f"""
    <style>
        #MainMenu {{visibility: hidden;}}
        footer {{visibility: hidden;}}
        header {{visibility: hidden;}}
        .stApp {{background-color: {bg_color}; color: #FFFFFF;}}
        .stChatInputContainer {{background-color: {input_bg} !important; border-radius: 12px !important; border: 1px solid {border_color} !important;}}
        .stChatInput {{color: #FFFFFF !important;}}
    </style>
""", unsafe_allow_html=True)

st.title(title_display)
st.caption(page_caption)

# --- 3. SANITIZED BRAIN INITIALIZATION (UPGRADED TO 120B) ---
try:
    raw_key = st.secrets["GROQ_API_KEY"]
    groq_api_key = raw_key.strip().replace('"', '').replace("'", "")
    
    if "your_actual" in groq_api_key or len(groq_api_key) < 10:
        st.error("❌ Setup Error: Your Secrets box contains placeholder text. Update it with a real gsk_ key.")
except Exception:
    st.error("❌ Key Error: Streamlit cannot find a secret labeled 'GROQ_API_KEY' in your dashboard settings.")

# Connected directly to OpenAI's flagship 120-Billion open-weights model
llm = ChatGroq(model="openai/gpt-oss-120b", groq_api_key=groq_api_key, temperature=0.4)

# --- 4. HELPER FUNCTIONS ---
def quick_search(query):
    try:
        with DDGS() as ddgs:
            results = [r['body'] for r in ddgs.text(query, max_results=3)]
            return "\n".join(results) if results else "No data found."
    except Exception:
        return "Search currently unavailable."

# --- 5. ISOLATED MEMORY VAULT INITIALIZATION ---
# Links bot selection directly to keys so conversations do not leak into each other
msg_vault_key = f"messages_{selected_bot}"
summary_vault_key = f"summary_{selected_bot}"

if msg_vault_key not in st.session_state:
    st.session_state[msg_vault_key] = []
if summary_vault_key not in st.session_state:
    st.session_state[summary_vault_key] = ""

# Render conversation logs
for message in st.session_state[msg_vault_key]:
    avatar_icon = "👤" if message["role"] == "user" else "🌐"
    with st.chat_message(message["role"], avatar=avatar_icon):
        st.markdown(message["content"])

# --- 6. INPUT HANDLING ---
typed_text = st.chat_input("Ask me anything.")

# --- 7. CHAT LOGIC WITH AUTOMATIC FAILSAFE ---
if typed_text:
    # Save and show user message instantly
    st.session_state[msg_vault_key].append({"role": "user", "content": typed_text})
    with st.chat_message("user", avatar="👤"):
        st.markdown(typed_text)

    # Automated background directive ensuring logic containment 
    system_instruction = (
        f"You are an AI assistant named {system_name}. Assist users with anything. "
        f"For news/weather/facts, start with 'SEARCH: '. Otherwise, be like a human assistant "
        f"{extra_personality}"
        f"If a request is completely incomprehensible, just a random string of letters with no meaning, "
        f"or logically impossible to answer, reply EXACTLY with the word 'FAILSAFE_TRIGGER'."
    )
    
    if st.session_state[summary_vault_key]:
        system_instruction += f" Background history context of things you already know about this user: {st.session_state[summary_vault_key]}"

    chat_history = [{"role": "system", "content": system_instruction}]
    
    for msg in st.session_state[msg_vault_key]:
        chat_history.append({"role": msg["role"], "content": msg["content"]})

    # Generate response smoothly
    with st.chat_message("assistant", avatar="🌐"):
        with st.spinner("Thinking..."):
            try:
                response = llm.invoke(chat_history)
                content = response.content.strip()

                # Handle Web Search Routes
                if "SEARCH:" in content:
                    parts = content.split("SEARCH:")
                    # Fixed token boundary checking before array parsing
                    topic = parts[1].strip() if len(parts) > 1 else ""
                    
                    if topic:
                        st.write(f"*(Searching for {topic}...)*")
                        web_info = quick_search(topic)
                        
                        search_prompt = (
                            f"User asked: {typed_text}.\n\nLive Web Data: {web_info}.\n\n"
                            f"Instructions: Answer the user's question accurately using ONLY the live web data provided above. "
                            f"If the data is blank or completely unrelated to the question, reply with 'FAILSAFE_TRIGGER'."
                        )
                        content = llm.invoke(search_prompt).content.strip()

                # --- FAILSAFE EVALUATION ENGINE ---
                if not content or "FAILSAFE_TRIGGER" in content or len(content) < 2:
                    content = f"I'm sorry, I couldn't fully comprehend or verify that query. Could you try rephrasing your request for {fallback_name}?"

            except Exception as e:
                # System execution crash fallback
                content = f"System Error: {system_name} could not understand your request."

            st.markdown(content)
            st.session_state[msg_vault_key].append({"role": "assistant", "content": content})

    # 8. SILENT BACKGROUND COMPRESSION (Triggers when history array exceeds 6 steps)
    if len(st.session_state[msg_vault_key]) > 6:
        history_text = "\n".join([f"{m['role']}: {m['content']}" for m in st.session_state[msg_vault_key][:-2]])
        summary_prompt = (
            f"You are a background data compiler. Read this dialogue data and compress it into a tiny list of core facts. "
            f"Do not talk to a user. Just return raw facts. Existing facts: {st.session_state[summary_vault_key]}\n\n"
            f"New dialogue data:\n{history_text}"
        )
        try:
            st.session_state[summary_vault_key] = llm.invoke(summary_prompt).content
            st.session_state[msg_vault_key] = st.session_state[msg_vault_key][-2:]
        except Exception:
            pass
