import os
os.environ["HF_HUB_DISABLE_SYMLINKS_WARNING"] = "1"

import streamlit as st

from src.auth import authenticate_user, create_user
from src.session import init_session, login_user, logout_user, add_transcription, add_translation
from src.ui import inject_css, show_logo, show_title, show_subtitle, show_footer

st.set_page_config(
    page_title="Bámi-Sọ̀rọ̀ (Legacy)",
    page_icon="🎙️",
    layout="wide",
)

inject_css()
init_session()

st.warning(
    "⚠️ **This Streamlit app is deprecated and will be removed soon.** "
    "Please use the full web app at **http://localhost:3000**, which offers "
    "the same transcription and translation features plus recording, history, "
    "admin controls, and more."
)

# =====================================================
# LOGIN / SIGNUP PAGE
# =====================================================

if not st.session_state.logged_in:

    left_col, right_col = st.columns([1, 1])

    with left_col:
        show_logo("assets/logo.png", width=250)
        show_title()
        show_subtitle("Bámi-Sọ̀rọ̀ L'édè Yorùbá 🎙️")

    with right_col:
        st.markdown('<div class="auth-box">', unsafe_allow_html=True)

        tab_login, tab_signup = st.tabs(["🔐 Login", "📝 Sign Up"])

        with tab_login:
            st.subheader("Login")
            login_username = st.text_input("Username", key="login_username")
            login_password = st.text_input("Password", type="password", key="login_password")

            if st.button("Login"):
                ok, msg = authenticate_user(login_username, login_password)
                if ok:
                    login_user(login_username)
                    st.success(msg)
                    st.rerun()
                else:
                    st.error(msg)

        with tab_signup:
            st.subheader("Create Account")
            signup_username = st.text_input("Choose Username", key="signup_username")
            signup_password = st.text_input("Choose Password", type="password", key="signup_password")

            if st.button("Create Account"):
                ok, msg = create_user(signup_username, signup_password)
                if ok:
                    st.success(msg)
                else:
                    st.warning(msg)

        st.markdown("</div>", unsafe_allow_html=True)

# =====================================================
# MAIN APPLICATION
# =====================================================

else:

    from src.speech_model import load_model, transcribe_audio_bytes
    from src.tone_restore import add_yoruba_tones
    from src.translation_model import load_translation_model, translate_text

    show_logo("assets/logo.png", width=150)
    show_title()
    show_subtitle("AI Yoruba Speech-to-Text Platform")
    st.success(f"Welcome, {st.session_state.username}")

    with st.sidebar:
        st.title("🎛️ Control Panel")
        st.write(f"👤 {st.session_state.username}")
        st.markdown("---")

        if st.button("🚪 Logout"):
            logout_user()
            st.rerun()

        if st.button("🗑️ Clear History"):
            st.session_state.history = []
            st.success("History cleared")

    tab_stt, tab_translate, tab_history = st.tabs(
        ["🎙️ Speech-to-Text", "🌍 Translate", "📚 History"]
    )

    # ─────────────────────────────────────────────────
    # TAB 1: SPEECH-TO-TEXT
    # ─────────────────────────────────────────────────

    with tab_stt:

        with st.spinner("Loading Yoruba AI model..."):
            model = load_model()

        st.subheader("🎙️ Yoruba Speech Input")

        col1, col2 = st.columns(2)

        with col1:
            audio_file = st.file_uploader("Upload Audio", type=["wav", "mp3", "m4a"], key="stt_upload")

        with col2:
            audio_value = st.audio_input("Record Yoruba Speech", key="stt_record")

        if audio_file or audio_value:
            try:
                with st.spinner("Processing Yoruba speech..."):
                    audio_bytes = audio_value.read() if audio_value else audio_file.read()
                    filename = audio_file.name if audio_file else "recording.wav"

                    stt_result = transcribe_audio_bytes(model, audio_bytes, filename)
                    raw_text = stt_result["text"]
                    confidence = stt_result.get("confidence", 0.0)
                    word_confidences = stt_result.get("word_confidences", [])
                    quality = stt_result.get("quality", {}) or {}
                    engine = stt_result.get("engine", "local")

                    # OpenAI output already carries correct tone marks; only the
                    # local W2V-BERT output needs the rule-based tone restorer.
                    if engine.startswith("w2v-bert"):
                        final_text = add_yoruba_tones(raw_text)
                    else:
                        final_text = raw_text

                    # Code-switch detection: if text contains mixed
                    # Yoruba and English, translate English parts to Yoruba
                    from common.code_switch import contains_mixed_language, process_mixed_text
                    code_switched = False
                    if contains_mixed_language(final_text):
                        cs_result = process_mixed_text(final_text)
                        if cs_result.get("code_switched"):
                            final_text = cs_result["text"]
                            code_switched = True
                            st.info("🔀 Mixed Yoruba/English detected — translated to unified Yoruba")

                    if final_text != st.session_state.transcript:
                        st.session_state.transcript = final_text
                        st.session_state.inline_translation = None
                        add_transcription(final_text)

                st.success("✅ Transcription Complete")
                st.audio(audio_bytes)

                # Audio quality warnings
                if quality and quality.get("warnings"):
                    for w in quality["warnings"]:
                        st.warning(f"🔊 {w}")
                elif quality:
                    st.success(f"🔊 Good audio quality ({quality.get('duration_sec', 0)}s)")

                if confidence and confidence > 0:
                    conf_pct = int(confidence * 100)
                    conf_color = "green" if confidence >= 0.8 else "yellow" if confidence >= 0.5 else "red"
                    st.markdown(f"**Model Confidence:** :{conf_color}[{conf_pct}%]")

                # Per-word confidence display
                if word_confidences:
                    st.markdown("**Word Confidence:**")
                    word_html = ""
                    for wc in word_confidences:
                        pct = int(wc["confidence"] * 100)
                        if pct >= 80:
                            color = "#22c55e"
                        elif pct >= 50:
                            color = "#eab308"
                        else:
                            color = "#ef4444"
                        word_html += f'<span style="color:{color};padding:2px 4px;margin:1px;border-radius:4px;background:rgba(0,0,0,0.05)" title="Confidence: {pct}%"> {wc["word"]}</span>'
                    st.markdown(word_html, unsafe_allow_html=True)

                st.text_area("📝 Yoruba Transcription", st.session_state.transcript, height=200, key="stt_output")

                c1, c2, c3 = st.columns(3)

                with c1:
                    st.download_button("⬇️ Download", st.session_state.transcript, file_name="yoruba_transcription.txt", key="stt_download")

                with c2:
                    if st.button("🗑️ Clear", key="stt_clear"):
                        st.session_state.transcript = ""
                        st.session_state.inline_translation = None
                        st.rerun()

                with c3:
                    if st.button("🌍 Translate to English", key="stt_translate_btn"):
                        st.session_state.stt_to_translate = st.session_state.transcript
                        st.rerun()

                # ── Inline English translation ──
                st.divider()
                t_tokenizer, t_model, t_device = load_translation_model()
                if st.button("🌍 Show English Translation", key="stt_inline_translate"):
                    if st.session_state.transcript.strip():
                        with st.spinner("Translating to English..."):
                            st.session_state.inline_translation = translate_text(
                                text=st.session_state.transcript,
                                direction="yo2en",
                                tokenizer=t_tokenizer,
                                model=t_model,
                                device=t_device,
                            )
                    else:
                        st.warning("No transcription to translate yet.")

                if st.session_state.get("inline_translation"):
                    best = st.session_state.inline_translation["best_translation"]
                    st.markdown("### 🌍 English Translation")
                    st.text_area("📝 Translation", best, height=160, key="stt_inline_output")
                    col_a, col_b = st.columns(2)
                    with col_a:
                        st.download_button("⬇️ Download Translation", best, file_name="english_translation.txt", key="stt_inline_download")
                    with col_b:
                        if st.button("💾 Save Translation", key="stt_inline_save"):
                            add_translation(st.session_state.transcript, best, "yo2en")
                            st.success("Saved to history!")

            except Exception as e:
                st.error(f"Error: {e}")

    # ─────────────────────────────────────────────────
    # TAB 2: TRANSLATE
    # ─────────────────────────────────────────────────

    with tab_translate:

        translation_load_error = None
        t_tokenizer = t_model = t_device = None

        with st.spinner("Loading translation model..."):
            try:
                t_tokenizer, t_model, t_device = load_translation_model()
            except Exception as e:
                translation_load_error = e

        if translation_load_error:
            st.error(f"Translation model unavailable: {translation_load_error}")
            st.stop()

        st.subheader("🌍 English ⇄ Yoruba Translation")
        st.caption(
            "Auto-detects language. "
            "For best Yoruba results, include tone marks "
            "(ẹ, ọ, ṣ, á, à, é, è, í, ì, ó, ò, ú, ù)."
        )

        prefill = st.session_state.pop("stt_to_translate", "")

        direction = st.radio(
            "Translation Direction",
            ["Auto-detect", "English → Yoruba", "Yoruba → English"],
            horizontal=True,
            key="translate_direction",
        )

        dir_map = {
            "Auto-detect": "auto",
            "English → Yoruba": "en2yo",
            "Yoruba → English": "yo2en",
        }

        source_text = st.text_area(
            "Enter text to translate",
            value=prefill,
            height=180,
            placeholder="Type or paste text here...",
            key="translate_input",
        )

        if st.button("🔄 Translate", key="translate_btn"):
            if source_text.strip():
                try:
                    with st.spinner("Translating..."):
                        # Auto mode: try code-switch first for mixed text
                        direction_key = dir_map[direction]
                        code_switched = False
                        if direction_key == "auto":
                            from common.code_switch import contains_mixed_language, process_mixed_text
                            if contains_mixed_language(source_text):
                                cs_result = process_mixed_text(source_text)
                                if cs_result.get("code_switched"):
                                    result = {
                                        "best_translation": cs_result["text"],
                                        "variants": [{"text": cs_result["text"], "config": "gpt-4o-mini", "quality_score": 0.95}],
                                        "detected_language": "mixed",
                                        "direction": "auto",
                                        "chunks_used": 0,
                                    }
                                    code_switched = True
                                    st.info("🔀 Mixed Yoruba/English detected — translated to unified Yoruba")

                        if not code_switched:
                            result = translate_text(
                                text=source_text,
                                direction=direction_key,
                                num_variants=1,
                                tokenizer=t_tokenizer,
                                model=t_model,
                                device=t_device,
                            )
                except Exception as e:
                    st.error(f"Translation error: {e}")
                    result = None

                if result:
                    detected = result["detected_language"]
                    lang_name = "Yoruba" if detected == "yo" else "Mixed" if detected == "mixed" else "English"
                    st.info(f"Detected language: **{lang_name}**")

                    for i, variant in enumerate(result["variants"]):
                        quality_pct = int(variant["quality_score"] * 100)
                        label = f"🏆 Best — {variant['config']}" if i == 0 else f"Option {i + 1} — {variant['config']}"

                        with st.container():
                            st.markdown(f"**{label}** (Quality: {quality_pct}%)")
                            st.text_area(label, variant["text"], height=120, key=f"variant_{i}", label_visibility="collapsed")

                    best = result["best_translation"]

                    vc1, vc2 = st.columns(2)

                    with vc1:
                        st.download_button("⬇️ Download Translation", best, file_name="yoruba_translation.txt", key="translate_download")

                    with vc2:
                        if st.button("💾 Save to History", key="translate_save"):
                            add_translation(source_text, best, direction)
                            st.success("Saved!")
                else:
                    st.error("Translation failed. Please check your OpenAI API key configuration and try again.")
            else:
                st.warning("Please enter text to translate.")

    # ─────────────────────────────────────────────────
    # TAB 3: HISTORY
    # ─────────────────────────────────────────────────

    with tab_history:

        st.subheader("📚 Activity History")

        has_stt = bool(st.session_state.history)
        has_trans = bool(st.session_state.translation_history)

        if not has_stt and not has_trans:
            st.info("No history yet. Use Speech-to-Text or Translate to get started.")

        if has_stt:
            st.markdown("#### 🎙️ Transcriptions")
            for item in st.session_state.history:
                with st.expander(item["time"]):
                    st.write(item["text"])

        if has_trans:
            st.markdown("#### 🌍 Translations")
            for item in st.session_state.translation_history:
                with st.expander(f"{item['time']} — {item['direction']}"):
                    st.markdown("**Source:**")
                    st.write(item["source"])
                    st.markdown("**Translation:**")
                    st.write(item["translation"])

    show_footer()
