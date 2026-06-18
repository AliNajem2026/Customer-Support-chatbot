import os
import requests
import streamlit as st
from dotenv import load_dotenv

load_dotenv()

BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8000")

st.set_page_config(
    page_title="Customer Support Bot",
    page_icon="💬",
    layout="centered"
)

st.title("Customer Support Bot")
st.caption("Multilingual AI support — English & Arabic")

if "messages" not in st.session_state:
    st.session_state.messages = []

if "user_id" not in st.session_state:
    st.session_state.user_id = "user_001"

with st.sidebar:
    st.header("Session")
    st.session_state.user_id = st.text_input(
        "User ID", value=st.session_state.user_id
    )
    st.divider()
    st.markdown("**Example questions (EN)**")
    st.markdown("- I cannot login to my account")
    st.markdown("- Where can I see my invoice?")
    st.markdown("- I found a bug in the app")
    st.divider()
    st.markdown("**أمثلة (AR)**")
    st.markdown("- لا أستطيع تسجيل الدخول")
    st.markdown("- أين أجد الفاتورة؟")
    st.markdown("- لدي مشكلة في التطبيق")
    st.divider()
    if st.button("Clear Chat", use_container_width=True):
        st.session_state.messages = []
        st.rerun()

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.write(msg["content"])
        if msg["role"] == "assistant" and "meta" in msg:
            meta = msg["meta"]
            st.caption(
                f"Language: `{meta.get('language', 'N/A')}` | "
                f"Intent: `{meta.get('intent', 'N/A')}` | "
                f"Safety: `{meta.get('safety_status', 'N/A')}`"
            )

if prompt := st.chat_input("Type your question here…"):
    st.session_state.messages.append({"role": "user", "content": prompt})

    with st.chat_message("user"):
        st.write(prompt)

    with st.chat_message("assistant"):
        with st.spinner("Thinking…"):
            try:
                resp = requests.post(
                    f"{BACKEND_URL}/chat",
                    json={
                        "user_id": st.session_state.user_id,
                        "message": prompt
                    },
                    timeout=30
                )
                resp.raise_for_status()
                data = resp.json()
                reply = data["response"]

                st.write(reply)
                st.caption(
                    f"Language: `{data.get('language', 'N/A')}` | "
                    f"Intent: `{data.get('intent', 'N/A')}` | "
                    f"Safety: `{data.get('safety_status', 'N/A')}`"
                )

                st.session_state.messages.append({
                    "role": "assistant",
                    "content": reply,
                    "meta": data
                })

            except requests.exceptions.ConnectionError:
                error = "Cannot reach the backend. Make sure the FastAPI server is running on " + BACKEND_URL
                st.error(error)
                st.session_state.messages.append({"role": "assistant", "content": error})

            except Exception as e:
                error = f"Unexpected error: {e}"
                st.error(error)
                st.session_state.messages.append({"role": "assistant", "content": error})
