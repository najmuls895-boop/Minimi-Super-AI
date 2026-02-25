import streamlit as st
import g4f
import os
import base64
from stability_sdk import client
import stability_sdk.interfaces.gooseai.generation.v1.generation_pb2 as generation

# --- Configuration ---
STABILITY_API_KEY = os.environ.get("STABILITY_API_KEY")

st.set_page_config(page_title="MiniMi Super AI", page_icon="🤖", layout="wide")

# --- JavaScript: Microphone & Male Voice Logic ---
def load_js_logic():
    js_code = """
    <script>
    const recognition = new (window.SpeechRecognition || window.webkitSpeechRecognition)();
    recognition.lang = 'hi-IN'; 
    recognition.interimResults = false;

    window.startRecognition = () => { recognition.start(); };

    recognition.onresult = (event) => {
        const text = event.results[0][0].transcript;
        const input = window.parent.document.querySelector('input[data-testid="stChatInputTextField"]');
        if (input) {
            input.value = text;
            input.dispatchEvent(new Event('input', { bubbles: true }));
        }
    };

    window.speakText = (text, lang) => {
        window.speechSynthesis.cancel(); 
        const msg = new SpeechSynthesisUtterance(text);
        msg.lang = lang;
        const voices = window.speechSynthesis.getVoices();
        // Male voice dhoondna (Google Voice 1 aksar Male hota hai)
        const maleVoice = voices.find(v => v.lang.includes(lang) && (v.name.includes('Male') || v.name.includes('Voice 1')));
        if (maleVoice) msg.voice = maleVoice;
        window.speechSynthesis.speak(msg);
    };
    </script>
    """
    st.components.v1.html(js_code, height=0)

load_js_logic()

# --- Custom UI Styling ---
st.markdown("""
    <style>
    .main { background-color: #0e1117; }
    .stChatInput { border-radius: 20px; }
    </style>
    """, unsafe_allow_html=True)

st.title("🤖 MiniMi Super AI")
st.caption("Hindi | Bengali | English | Voice | Image Generation")

# --- Session State for History ---
if "messages" not in st.session_state:
    st.session_state.messages = []

# Sidebar for Microphone
with st.sidebar:
    st.header("Controls")
    if st.button("🎤 Tap to Speak (Boliye)"):
        st.components.v1.html("<script>window.parent.startRecognition();</script>", height=0)
    st.write("---")
    st.info("💡 **Tips:**\n1. Normal baat karein.\n2. Image ke liye likhein: 'Create image of...' ya 'Photo banao...'")

# Display Chat History
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        if msg.get("type") == "image":
            st.image(msg["content"])
        else:
            st.markdown(msg["content"])

# --- Main Logic ---
if user_input := st.chat_input("Puchiye ya Bolkar likhein..."):
    # User Message
    st.chat_message("user").markdown(user_input)
    st.session_state.messages.append({"role": "user", "content": user_input})

    # 1. Check if Image Request
    image_keywords = ["create image", "generate image", "photo banao", "tasveer banao", "chobi banao"]
    if any(key in user_input.lower() for key in image_keywords):
        if not STABILITY_API_KEY:
            st.error("API Key missing! Please add STABILITY_API_KEY in Secrets.")
        else:
            with st.chat_message("assistant"):
                with st.spinner("🎨 MiniMi painting kar raha hai..."):
                    try:
                        stability_api = client.StabilityInference(key=STABILITY_API_KEY, engine="stable-diffusion-xl-1024-v1-0")
                        answers = stability_api.generate(prompt=user_input, steps=30, width=1024, height=1024, samples=1)
                        for resp in answers:
                            for artifact in resp.artifacts:
                                if artifact.type == generation.ARTIFACT_IMAGE:
                                    img_base64 = base64.b64encode(artifact.binary).decode("utf-8")
                                    img_str = f"data:image/png;base64,{img_base64}"
                                    st.image(img_str, caption="Result by MiniMi")
                                    st.session_state.messages.append({"role": "assistant", "type": "image", "content": img_str})
                                    st.components.v1.html("<script>window.parent.speakText('Maine aapki tasveer bana di hai', 'hi-IN');</script>", height=0)
                    except Exception as e:
                        st.error(f"Error: {e}")

    # 2. Otherwise, Give Text Answer
    else:
        with st.chat_message("assistant"):
            with st.spinner("🧠 MiniMi soch raha hai..."):
                try:
                    # G4F for free AI response
                    response = g4f.ChatCompletion.create(
                        model=g4f.models.gpt_4,
                        messages=[{"role": "system", "content": "Tumhara naam MiniMi hai. Tum Hindi, Bengali aur English bolte ho. Hamesha dosti se jawab do."}] + 
                                 [{"role": m["role"], "content": m["content"]} for m in st.session_state.messages if m.get("type") != "image"]
                    )
                    st.markdown(response)
                    
                    # Detect Language for Voice
                    lang = 'en-US'
                    if any(w in response.lower() for w in ['hai', 'hoon', 'aap', 'kaise']): lang = 'hi-IN'
                    elif any(w in response.lower() for w in ['ami', 'tumi', 'bhalo', 'kemon']): lang = 'bn-IN'
                    
                    # Speak response
                    clean_res = response.replace("'", "").replace("\n", " ")
                    st.components.v1.html(f"<script>window.parent.speakText('{clean_res}', '{lang}');</script>", height=0) 
                    
                    st.session_state.messages.append({"role": "assistant", "content": response})
                except Exception as e:
                    st.error("Service busy hai, please thodi der baad try karein.") 
