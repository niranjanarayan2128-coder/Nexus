import streamlit as st
import os
import asyncio
import base64
from langchain_ollama import ChatOllama
from duckduckgo_search import DDGS
from streamlit_mic_recorder import speech_to_text
from gtts import gTTS

# --- 1. THE "FORCE FIX" FOR FFMPEG ---
# This tells Python exactly where your ffmpeg is so you don't get errors
ffmpeg_path = r'C:\ffmpeg-8.1.2-essentials_build\bin'
os.environ["PATH"] += os.pathsep + ffmpeg_path

# --- 2. PAGE SETUP ---
st.set_page_config(page_title="Project Nexus.", page_icon="")
st.title("Project Nexus")
st.markdown("How can I help you?")

# --- 3. INITIALIZE BRAIN ---
llm = ChatOllama(model="llama3.2", temperature=0.7)

# --- 4. HELPER FUNCTIONS ---

def quick_search(query):
    try:
        with DDGS() as ddgs:
            results = [r['body'] for r in ddgs.text(query, max_results=3)]
            return "\n".join(results) if results else "No data found."
    except Exception:
        return "Search currently unavailable."

def speak_text(text):
    try:
        tts = gTTS(text=text, lang='en')
        filename = "temp_voice.mp3"
        tts.save(filename)
        with open(filename, "rb") as f:
            data = f.read()
            b64 = base64.b64encode(data).decode()
            md = f'<audio autoplay="true"><source src="data:audio/mp3;base64,{b64}" type="audio/mp3"></audio>'
            st.markdown(md, unsafe_allow_html=True)
    except Exception as e:
        st.error(f"Voice Error: {e}")

# --- 5. INPUT HANDLING ---
st.sidebar.header("Voice Control")
voice_text = speech_to_text(language='en', start_prompt="🎤 Speak Now", stop_prompt="⏹️ Stop", key='STT')
typed_text = st.chat_input("Type your message here...")

user_query = voice_text if voice_text else typed_text

# --- 6. CHAT SYSTEM ---
if "messages" not in st.session_state:
    st.session_state.messages = []

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

if user_query:
    st.session_state.messages.append({"role": "user", "content": user_query})
    with st.chat_message("user"):
        st.markdown(user_query)

    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            sys_msg = "You are a AI assitant and assist user with anything. For news/weather/facts, start with 'SEARCH: '. Otherwise, be like a human assistant so polite but not too polite."
            response = llm.invoke(f"{sys_msg}\n\nUser: {user_query}")
            content = response.content

            if "SEARCH:" in content:
                topic = content.split("SEARCH:")[1].strip()
                st.write(f"*(Searching for {topic}...)*")
                web_info = quick_search(topic)
                content = llm.invoke(f"User asked: {user_query}. Search info: {web_info}. Answer modestly.").content

            st.markdown(content)
            st.session_state.messages.append({"role": "assistant", "content": content})
            speak_text(content)
