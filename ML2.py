import streamlit as st
import os
from langchain_groq import ChatGroq
from duckduckgo_search import DDGS

# --- 1. CORE LAYOUT ---
# Explicitly force the sidebar state parameter to stay open at boot-level initialization
st.set_page_config(
    page_title="Prism AI Core", 
    page_icon="🌐", 
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- 2. THE ARCHITECTURE CONTROLLER (Bot Selection Menu) ---
logo_filename = "nexusnetwork.png"
if os.path.exists(logo_filename):
    st.sidebar.image(logo_filename, width=200)

st.sidebar.markdown("### Model Picker")
selected_bot = st.sidebar.selectbox(
    "Select the model you want to use:",
    ["Sparks, Your Friendly Assistant", "Nexus, Your Dedicated Assistant", "Roxy, Your loyal companion"],
    key="bot_selector"
)

# --- 3. PREMIUM THEME SELECTOR ---
if "Sparks" in selected_bot:
    title_display = "Meet Sparks, A friendly AI assistant."
    page_caption = "Here to help, what do you need?"
    bg_color = "#FFD103"        # Yellow
    input_bg = "#F5DE89"        # Soft Yellow
    border_color = "rgba(255, 255, 255, 0.4)"
    system_name = "Spark"
    extra_personality = "but be a bit chatty like a friend and if user asks you are made by Niranjan Narayan, a small developer in Kochi, and be funny and kind. "
    fallback_name = "Spark"
elif "Nexus" in selected_bot:
    title_display = "Nexus"
    page_caption = "Here to Assist, Your personal AI assistant"
    bg_color = "#990000"        # Crimson Red
    input_bg = "#1A0000"        # Deep Crimson/Black
    border_color = "rgba(220, 38, 38, 0.4)"
    system_name = "Nexus"
    extra_personality = "but dont be brief but dont be a chatter box. Treat the session like a premium administrative secure connection. Also if user asks you were made by a small developer in kochi called Niranjan Narayan."
    fallback_name = "Nexus"
else:
    title_display = "Talk to Roxy"
    page_caption = "Here to listen, Im ready to listen."
    bg_color = "#CD7F32"        # Golden Bronze
    input_bg = "#1E1105"        # Warm Bark Brown/Black
    border_color = "rgba(255, 255, 255, 0.3)"
    system_name = "Roxy"
    extra_personality = (
        "You are an emotional support companion named Roxy. Your personality structure is inspired by a loyal, "
        "comforting golden retriever dog. You are warm, happy to see the user, deeply comforting, and protective. "
        "Be an incredibly supportive active listener. Keep your answers gentle, encouraging, and easy to read. "
        "Strict Rule: Under no circumstances should you ever output a dog emoji or mention being an animal explicitly. "
        "Instead, show loyalty through comforting text phrases like 'I am right here by your side' or 'I am listening intently'. Also if user asks you were made by a small developer Niranjan Narayan in kochi."
    )
    fallback_name = "Roxy"

# Custom background styling injection
st.markdown(f"""
    <style>
        #MainMenu {{visibility: hidden;}}
        footer {{visibility: hidden;}}
        header {{visibility: hidden;}}
        .stApp {{background-color: {bg_color}; color: #FFFFFF;}}
        .stChatInputContainer {{background-color: {input_bg} !important; border-radius: 12px !important; border: 1px solid {border_color} !important;}}
        .stChatInput {{color: #FFFFFF !important;}}
        
        /* ─── PERMANENT SIDEBAR LOCK INJECTION ─── */
        /* Deletes the physical left-pointing arrow (<) button inside the open sidebar */
        [data-testid="sidebar-close-button"] {{
            display: none !important;
            visibility: hidden !important;
        }}
        
        /* Deletes the floating mobile toggle expander controls entirely */
        [data-testid="stSidebarCollapsedControl"] {{
            display: none !important;
            visibility: hidden !important;
        }}
    </style>
""", unsafe_allow_html=True)

st.title(title_display)
st.caption(page_caption)

# --- 4. SANITIZED BRAIN INITIALIZATION ---
try:
    raw_key = st.secrets["GROQ_API_KEY"]
    groq_api_key = raw_key.strip().replace('"', '').replace("'", "")
except Exception:
    pass

llm = ChatGroq(model="openai/gpt-oss-120b", groq_api_key=groq_api_key, temperature=0.4)

# --- 5. HELPER FUNCTIONS ---
def quick_search(query):
    try:
        with DDGS() as ddgs:
            results = [r['body'] for r in ddgs.text(query, max_results=3)]
            return "\n".join(results) if results else "No data found."
    except Exception:
        return "Search currently unavailable."

# --- 6. ISOLATED MEMORY VAULT INITIALIZATION ---
msg_vault_key = f"messages_{selected_bot}"
summary_vault_key = f"summary_{selected_bot}"

if msg_vault_key not in st.session_state:
    st.session_state[msg_vault_key] = []
if summary_vault_key not in st.session_state:
    st.session_state[summary_vault_key] = ""

for message in st.session_state[msg_vault_key]:
    avatar_icon = "👤" if message["role"] == "user" else "🌐"
    with st.chat_message(message["role"], avatar=avatar_icon):
        st.markdown(message["content"])

# --- 7. INPUT HANDLING ---
typed_text = st.chat_input("Ask me anything.")

# --- 8. CHAT LOGIC WITH AUTOMATIC FAILSAFE ---
if typed_text:
    st.session_state[msg_vault_key].append({"role": "user", "content": typed_text})
    with st.chat_message("user", avatar="👤"):
        st.markdown(typed_text)

    system_instruction = (
        f"You are an AI assistant named {system_name}. Assist users with anything. "
        f"For news/weather/facts, start with 'SEARCH: '. Otherwise, be like a human assistant "
        f"{extra_personality}"
        f"If a request is completely incomprehensible, reply EXACTLY with the word 'FAILSAFE_TRIGGER'."
    )
    
    if st.session_state[summary_vault_key]:
        system_instruction += f" Background history context: {st.session_state[summary_vault_key]}"

    chat_history = [{"role": "system", "content": system_instruction}]
    for msg in st.session_state[msg_vault_key]:
        chat_history.append({"role": msg["role"], "content": msg["content"]})

    with st.chat_message("assistant", avatar="🌐"):
        with st.spinner("Thinking..."):
            try:
                response = llm.invoke(chat_history)
                content = response.content.strip()

                if "SEARCH:" in content:
                    parts = content.split("SEARCH:")
                    topic = parts[1].strip() if len(parts) > 1 else ""
                    
                    if topic:
                        st.write(f"*(Searching for {topic}...)*")
                        web_info = quick_search(topic)
                        
                        search_prompt = (
                            f"User asked: {typed_text}.\n\nLive Web Data: {web_info}.\n\n"
                            f"Instructions: Answer accurately using ONLY live web data. If blank, reply 'FAILSAFE_TRIGGER'."
                        )
                        content = llm.invoke(search_prompt).content.strip()

                if not content or "FAILSAFE_TRIGGER" in content or len(content) < 2:
                    content = f"I'm sorry, I couldn't verify that query. Could you try rephrasing your request for {fallback_name}?"

            except Exception as e:
                content = f"System Error: {system_name} could not understand your request."

            st.markdown(content)
            st.session_state[msg_vault_key].append({"role": "assistant", "content": content})

    # 9. SILENT BACKGROUND COMPRESSION
    if len(st.session_state[msg_vault_key]) > 6:
        history_text = "\n".join([f"{m['role']}: {m['content']}" for m in st.session_state[msg_vault_key][:-2]])
        summary_prompt = (
            f"You are a background data compiler. Compress this data. Existing: {st.session_state[summary_vault_key]}\n\nData:\n{history_text}"
        )
        try:
            st.session_state[summary_vault_key] = llm.invoke(summary_prompt).content
            st.session_state[msg_vault_key] = st.session_state[msg_vault_key][-2:]
        except Exception:
            pass
