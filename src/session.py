import streamlit as st


def init_session():
    defaults = {
        "logged_in": False,
        "username": "",
        "history": [],
        "transcript": "",
        "translation_history": [],
        "inline_translation": None,
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


def login_user(username):
    st.session_state.logged_in = True
    st.session_state.username = username


def logout_user():
    st.session_state.logged_in = False
    st.session_state.username = ""
    st.session_state.history = []
    st.session_state.transcript = ""
    st.session_state.translation_history = []


def add_transcription(text):
    from datetime import datetime
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    st.session_state.history.insert(0, {
        "time": timestamp,
        "text": text,
        "type": "transcription",
    })


def add_translation(source, translation, direction):
    from datetime import datetime
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    st.session_state.translation_history.insert(0, {
        "time": timestamp,
        "source": source,
        "translation": translation,
        "direction": direction,
    })
