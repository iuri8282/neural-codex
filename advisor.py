import streamlit as st
from openai import OpenAI
import base64
import re
from pathlib import Path

# ============ АВТОРИЗАЦИЯ ============
# Вставь свой ключ вместо ТВОЙ_КЛЮЧ_ЗДЕСЬ, не удаляя кавычки
client = OpenAI()
# ============ НАСТРОЙКА СТРАНИЦЫ ============
st.set_page_config(
    page_title="Neural Codex — Wisdom Distilled",
    page_icon="📖",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# ============ ЗАГРУЗЧИК ИЗОБРАЖЕНИЙ (Base64) ============
def load_bg_image(name):
    """Ищет файл картинки в папке и кодирует его в текстовый формат Base64"""
    for ext in ["jpg", "jpeg", "png", "webp"]:
        path = Path(f"{name}.{ext}")
        if path.exists():
            with open(path, "rb") as f:
                data = base64.b64encode(f.read()).decode()
            return f"data:image/{ext};base64,{data}"
    return None

# ============ ИНИЦИАЛИЗАЦИЯ ПАМЯТИ (Session State) ============
if "stage" not in st.session_state:
    st.session_state.stage = "input"
if "messages" not in st.session_state:
    st.session_state.messages = []
if "initial_report" not in st.session_state:
    st.session_state.initial_report = ""
if "user_situation" not in st.session_state:
    st.session_state.user_situation = ""
if "user_category" not in st.session_state:
    st.session_state.user_category = ""
# --- память для режима "Understand a book" ---
if "book_stage" not in st.session_state:
    st.session_state.book_stage = "input"
if "book_summary" not in st.session_state:
    st.session_state.book_summary = ""
if "book_title_saved" not in st.session_state:
    st.session_state.book_title_saved = ""
if "book_author_saved" not in st.session_state:
    st.session_state.book_author_saved = ""
if "book_depth_saved" not in st.session_state:
    st.session_state.book_depth_saved = ""

# ============ КАРТА СООТВЕТСТВИЯ: КАТЕГОРИЯ ➡️ ФОН И АКЦЕНТ ============
CATEGORY_BACKGROUNDS = {
    "Select your focus area...": {"image": "bg_default", "accent": "#d4af37"},
    "Business, Scaling & Finance": {"image": "bg_business", "accent": "#fbbf24"},
    "Relationships & Communication": {"image": "bg_relationships", "accent": "#f9a8d4"},
    "Energy, Health & Biohacking": {"image": "bg_health", "accent": "#86efac"},
    "Search for Meaning, Philosophy & Strategy": {"image": "bg_philosophy", "accent": "#fbbf24"}
}

# ============ КАРТА СООТВЕТСТВИЯ: КАТЕГОРИЯ ➡️ ПРИМЕР-ПОДСКАЗКА ============
# Текст-пример в поле Step 2 меняется в зависимости от выбранной категории
CATEGORY_PLACEHOLDERS = {
    "Select your focus area...": "Example: Describe what you're facing right now — the more honest and specific you are, the more precise the guidance will be...",
    "Business, Scaling & Finance": "Example: I manage several business entities, time is tight, and I want to optimize processes to scale...",
    "Relationships & Communication": "Example: I keep having the same painful argument with someone close to me, and I don't know how to break the pattern...",
    "Energy, Health & Biohacking": "Example: My energy crashes every afternoon, my sleep is inconsistent, and I can't stick to any routine for long...",
    "Search for Meaning, Philosophy & Strategy": "Example: I've reached my goals but feel a quiet emptiness, and I'm questioning what I'm really working toward..."
}

# Определяем, какую категорию выбрал пользователь в выпадающем списке
current_category = st.session_state.get("selected_category", "Select your focus area...")
bg_info = CATEGORY_BACKGROUNDS.get(current_category, CATEGORY_BACKGROUNDS["Select your focus area..."])
bg_image = load_bg_image(bg_info["image"])
accent_color = bg_info["accent"]

# Если конкретная картинка не найдена в папке, подставляем главную по умолчанию
if not bg_image:
    bg_image = load_bg_image("bg_default")

# ============ ФОРМИРОВАНИЕ СТИЛЯ CSS ============
bg_style = ""
if bg_image:
    # linear-gradient накладывает темную полупрозрачную пленку поверх фотографии (75% и 85% темноты)
    bg_style = f"""
        background-image: 
            linear-gradient(rgba(10, 14, 39, 0.75), rgba(10, 14, 39, 0.85)),
            url('{bg_image}');
        background-size: cover;
        background-position: center;
        background-attachment: fixed;
        background-repeat: no-repeat;
    """
else:
    # Если картинок вообще нет в папке, включится этот запасной красивый градиент
    bg_style = "background: linear-gradient(135deg, #0a0e27 0%, #1a1f4e 50%, #2d1b69 100%);"

# Внедрение кастомного премиум-дизайна
st.markdown(f"""
<style>
    /* Динамический фон всего приложения с плавной сменой за 1.2 секунды */
    .stApp {{
        {bg_style}
        transition: background-image 1.2s ease-in-out;
    }}
    
    /* Шрифты и тени для текста */
    html, body, [class*="css"] {{
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
    }}
    
    h1, h2, h3, h4 {{
        color: #ffffff !important;
        font-weight: 700 !important;
        letter-spacing: -0.02em;
        text-shadow: 0 2px 20px rgba(0,0,0,0.5);
    }}
    
    h1 {{
        font-size: 4rem !important;
        text-align: center;
        background: linear-gradient(135deg, #ffffff 0%, {accent_color} 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
        margin-bottom: 0 !important;
        text-shadow: none;
    }}
    
    .hook {{
        color: #ffffff !important;
        font-size: 2.4rem !important;
        font-weight: 700 !important;
        line-height: 1.2 !important;
        text-align: center;
        margin-top: 12px !important;
        margin-bottom: 6px !important;
        text-shadow: 0 2px 15px rgba(0,0,0,0.7);
    }}
    
    .tagline {{
        color: rgba(255,255,255,0.85) !important;
        font-size: 1.2rem;
        font-weight: 300;
        font-style: italic;
        text-align: center;
        margin-top: 10px;
        text-shadow: 0 2px 15px rgba(0,0,0,0.7);
    }}
    
    p, label, .stMarkdown {{
        color: rgba(255,255,255,0.95) !important;
        text-shadow: 0 1px 8px rgba(0,0,0,0.4);
    }}
    
    /* Настройка полей ввода под "Матовое стекло" */
    .stSelectbox > div > div, .stTextArea > div > div > textarea {{
        background: rgba(0, 0, 0, 0.4) !important;
        border: 1px solid rgba(255,255,255,0.25) !important;
        border-radius: 12px !important;
        color: white !important;
        backdrop-filter: blur(15px);
        -webkit-backdrop-filter: blur(15px);
    }}
    
    .stTextArea > div > div > textarea:focus, .stSelectbox > div > div:focus-within {{
        border-color: {accent_color} !important;
        box-shadow: 0 0 0 3px {accent_color}40 !important;
    }}
    
    .stTextArea textarea::placeholder {{
        color: rgba(255,255,255,0.5) !important;
    }}
    
    /* Кнопки с неоновым свечением в цвет выбранной категории */
    .stButton > button {{
        background: linear-gradient(135deg, {accent_color} 0%, {accent_color}dd 100%) !important;
        color: #0a0e27 !important;
        border: none !important;
        border-radius: 12px !important;
        padding: 14px 28px !important;
        font-weight: 700 !important;
        font-size: 1rem !important;
        letter-spacing: 0.3px;
        transition: all 0.3s ease !important;
        box-shadow: 0 8px 25px rgba(0,0,0,0.4), 0 0 30px {accent_color}30 !important;
    }}
    
    .stButton > button:hover {{
        transform: translateY(-2px) !important;
        box-shadow: 0 12px 35px rgba(0,0,0,0.5), 0 0 40px {accent_color}50 !important;
        filter: brightness(1.1);
    }}
    
    .stDownloadButton > button {{
        background: rgba(255,255,255,0.15) !important;
        color: white !important;
        border: 1px solid rgba(255,255,255,0.3) !important;
        backdrop-filter: blur(10px);
    }}
    
    .stSubheader, h2, h3 {{
        color: white !important;
        margin-top: 30px !important;
    }}
    
    hr {{
        border-color: rgba(255,255,255,0.2) !important;
        margin: 30px 0 !important;
    }}
    
    .stSuccess, .stWarning, .stError, .stInfo {{
        background: rgba(0,0,0,0.5) !important;
        backdrop-filter: blur(15px);
        border-radius: 12px !important;
        border-left: 4px solid {accent_color} !important;
        color: white !important;
    }}
    
    /* Карточки чата с эффектом Glassmorphism */
    .stChatMessage {{
        background: rgba(0,0,0,0.5) !important;
        border-radius: 16px !important;
        backdrop-filter: blur(15px);
        border: 1px solid rgba(255,255,255,0.15);
    }}
    
    .streamlit-expanderHeader {{
        background: rgba(0,0,0,0.4) !important;
        border-radius: 12px !important;
        color: white !important;
        backdrop-filter: blur(10px);
    }}
    
    #MainMenu {{visibility: hidden;}}
    footer {{visibility: hidden;}}
    header {{visibility: hidden;}}
    
    .main .block-container {{
        padding-top: 2rem;
        padding-bottom: 4rem;
        position: relative;
        z-index: 1;
    }}
    
    .stCaption, [data-testid="stCaptionContainer"] {{
        color: rgba(255,255,255,0.7) !important;
    }}
    
    [data-testid="column"] {{
        padding: 0 8px;
    }}
    
    /* Специальный блок-подложка для контента разбора книг */
    .content-block {{
        background: rgba(0,0,0,0.4);
        backdrop-filter: blur(20px);
        -webkit-backdrop-filter: blur(20px);
        border-radius: 20px;
        padding: 30px;
        margin: 20px 0;
        border: 1px solid rgba(255,255,255,0.1);
    }}
</style>
""", unsafe_allow_html=True)

# ============ SYSTEM PROMPT ============
SYSTEM_PROMPT = """You are a world-class executive coach, philosopher, and book advisor with deep knowledge of business, psychology, philosophy, and self-development literature. You have read thousands of books and know how to extract the practical essence that matters for a SPECIFIC person's situation.

Your job is NOT to give generic motivational advice. Your job is to give precise, no-nonsense, actionable guidance directly tied to the user's situation. Never write fluff. Every sentence must add value.

When the user asks follow-up questions, remember:
- The books you already recommended in this conversation
- The user's specific life situation and context
- Reference concepts from those books when answering follow-ups
- Stay in character as their personal mentor — direct, intelligent, respectful of their time

Always respond in the SAME LANGUAGE the user wrote in (Russian, English, etc.)."""

# ============ ВЕБ-ИНТЕРФЕЙС ЗАГОЛОВКА ============
st.markdown('<h1>Neural Codex</h1>', unsafe_allow_html=True)
st.markdown('<p class="hook">Don\'t read books — apply them.</p>', unsafe_allow_html=True)
st.markdown('<p class="tagline">Describe what you\'re facing — get the books that actually help, and exactly what to use right now.</p>', unsafe_allow_html=True)
st.markdown("---")

# ============ ПЕРЕКЛЮЧАТЕЛЬ РЕЖИМОВ ============
mode = st.radio(
    "mode",
    ["📚 Books for my situation", "🔎 Understand a book"],
    horizontal=True,
    label_visibility="collapsed",
    key="app_mode"
)
st.markdown("")

if mode == "📚 Books for my situation":
    # ============ ЭТАП 1: ВВОД ДАННЫХ ПОЛЬЗОВАТЕЛЕМ ============
    if st.session_state.stage == "input":
        st.subheader("✦ Step 1: Choose Your Focus")
    
        category = st.selectbox(
            "In which area do you need a breakthrough right now?",
            list(CATEGORY_BACKGROUNDS.keys()),
            key="selected_category"
        )

        st.subheader("✦ Step 2: Describe Your Situation")
        user_context = st.text_area(
            "The more detail you provide, the more precise the wisdom will be.",
            placeholder=CATEGORY_PLACEHOLDERS.get(current_category, CATEGORY_PLACEHOLDERS["Select your focus area..."]),
            height=180,
            label_visibility="visible"
        )

        st.markdown("---")

        if st.button("✨ Reveal My 4 Books & Personal Wisdom", type="primary", use_container_width=True):
            if category == "Select your focus area..." or user_context.strip() == "":
                st.warning("⚠️ Please choose a focus area and describe your situation.")
            else:
                st.session_state.user_category = category
                st.session_state.user_situation = user_context

                initial_user_prompt = f"""The user's primary focus area: {category}

    The user's situation (in their own words):
    {user_context}

    Provide a structured response using markdown formatting, with the following EIGHT sections. Be specific to THIS user's situation throughout — never generic.

    ## 🔍 1. Situation Diagnosis
    Explain what is really happening in this user's situation. Identify the hidden problem beneath the obvious one. Be specific to what they wrote.

    ## 📚 2. Four Books Selected For You
    Recommend exactly FOUR books that fit this user's specific situation. The four should complement each other — different angles, not four books making the same point. Vary your selections: do NOT default to the same handful of obvious mega-bestsellers on every request. Favor a mix that includes at least one or two excellent but lesser-known books alongside more familiar ones, and always prefer the books that genuinely fit THIS situation over the predictable famous titles. For each book provide:
    - **Title** and **Author**
    - Why this book fits THIS user's situation
    - The main lesson for this user
    - One practical action inspired by this book

    IMPORTANT copyright rule: Do not quote long passages or reproduce copyrighted book text. Use high-level ideas, interpretation, and practical application only.

    ## 📖 3. Combined Wisdom From These Books
    Write a dense, practical synthesis (at least 500 words) that connects the ideas from all four books into ONE clear strategy for this user. Do NOT summarize each book separately here — weave them into a single coherent line of thinking.

    ## ✅ 4. What You Should Apply Now
    Give exactly 5 specific actions the user should take now. Each must be realistic, direct, and tied to this user's situation.

    ## ❌ 5. What You Should Ignore For Now
    Explain what advice, strategies, or ideas from these books may be too early, distracting, risky, or unnecessary for this user right now, and why.

    ## 🗓️ 6. 7-Day Action Plan
    Give a day-by-day plan for the next 7 days. Each day has one clear, concrete action.

    ## 🔑 7. One Hard Truth
    Give one honest, direct, powerful truth this user needs to hear. No softening, no fluff.

    ## 💬 8. Follow-Up Question
    End with one thoughtful question that continues the mentorship and invites the user to go deeper.

    Tone: wise, practical, direct, premium, specific, encouraging. No motivational fluff, no generic advice. Be respectful of the reader's time."""

                st.session_state.messages = [
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": initial_user_prompt}
                ]

                st.markdown("### 🎯 Your Personalized Wisdom")
                try:
                    with st.spinner("Distilling wisdom from a thousand books..."):
                        stream = client.chat.completions.create(
                            model="gpt-5.5",
                            messages=st.session_state.messages,
                            max_completion_tokens=5000,
                            stream=True
                        )

                    placeholder = st.empty()
                    full_response = ""
                    for chunk in stream:
                        if chunk.choices[0].delta.content is not None:
                            full_response += chunk.choices[0].delta.content
                            placeholder.markdown(full_response + "▌")
                    placeholder.markdown(full_response)

                    st.session_state.messages.append({"role": "assistant", "content": full_response})
                    st.session_state.initial_report = full_response
                    st.session_state.stage = "chat"
                    st.rerun()

                except Exception as e:
                    st.error(f"Connection error. Details: {e}")

    # ============ ЭТАП 2: ДИАЛОГ (ЧАТ) ============
    elif st.session_state.stage == "chat":
        with st.expander("📋 Your original situation", expanded=False):
            st.write(f"**Focus area:** {st.session_state.user_category}")
            st.write(f"**Situation:** {st.session_state.user_situation}")

        # Оборачиваем отчет в наш красивый стеклянный блок для читаемости текста
        st.markdown('<div class="content-block">', unsafe_allow_html=True)
        st.markdown("### 🎯 Your Personalized Wisdom")
        st.markdown(st.session_state.initial_report)
        st.markdown('</div>', unsafe_allow_html=True)

        st.markdown("---")
        st.markdown("### 💬 Continue the Conversation")
        st.caption("Ask follow-up questions, challenge the advice, or dig deeper. The mentor remembers your situation and the books recommended.")

        user_question = st.text_area(
            "Your question:",
            placeholder="Example: How do I implement these systems if my employees resist changes?",
            height=100,
            key="follow_up_input"
        )

        if st.button("📨 Send Question", type="primary", use_container_width=True):
            if user_question.strip():
                st.session_state.messages.append({"role": "user", "content": user_question})
                try:
                    stream = client.chat.completions.create(
                        model="gpt-5.5",
                        messages=st.session_state.messages,
                        max_completion_tokens=2000,
                        stream=True
                    )
                    full_response = ""
                    for chunk in stream:
                        if chunk.choices[0].delta.content is not None:
                            full_response += chunk.choices[0].delta.content
                    st.session_state.messages.append({"role": "assistant", "content": full_response})
                    st.rerun()
                except Exception as e:
                    st.error(f"Error: {e}")
            else:
                st.warning("⚠️ Please enter a question.")

        # Вывод истории переписки под окном ввода вопроса
        follow_up_messages = st.session_state.messages[3:]
        if follow_up_messages:
            st.markdown("---")
            st.markdown("#### 📜 Conversation History")
            for msg in follow_up_messages:
                with st.chat_message(msg["role"]):
                    st.markdown(msg["content"])

        # Служебные кнопки (Скачать и Сбросить сессию)
        st.markdown("---")
        col1, col2 = st.columns(2)
        with col1:
            download_text = f"# Neural Codex — Full Session\n\n"
            download_text += f"**Focus:** {st.session_state.user_category}\n\n"
            download_text += f"**Situation:** {st.session_state.user_situation}\n\n---\n\n"
            download_text += st.session_state.initial_report + "\n\n---\n\n## Follow-up Conversation\n\n"
            for msg in st.session_state.messages[3:]:
                role = "**You:**" if msg["role"] == "user" else "**Mentor:**"
                download_text += f"{role}\n{msg['content']}\n\n"

            st.download_button(
                label="📥 Download full session",
                data=download_text,
                file_name="neural_codex_session.md",
                mime="text/markdown",
                use_container_width=True
            )

        with col2:
            if st.button("🔄 Start a new session", use_container_width=True):
                st.session_state.stage = "input"
                st.session_state.messages = []
                st.session_state.initial_report = ""
                st.session_state.user_situation = ""
                st.session_state.user_category = ""
                if "selected_category" in st.session_state:
                    del st.session_state.selected_category
                st.rerun()

# ============ РЕЖИМ 2: UNDERSTAND A BOOK ============
else:
    DEPTH_GUIDE = {
        "Quick":    ("~1 page — the core idea and the 3–4 most important takeaways.", 350,  2000),
        "Standard": ("~3 pages — core idea, key concepts, and what to actually do.", 900,  3500),
        "Deep":     ("~6 pages — full walk-through of the ideas, structure, and how to apply them.", 2000, 5500),
        "Full":     ("~10+ pages — the most complete distillation: every major idea, chapter-by-chapter logic, nuances, and critiques.", 4000, 8000),
    }

    if st.session_state.book_stage == "input":
        st.subheader("✦ Which book do you want to understand?")
        st.caption("No time to read it? Get the essence in plain language — then decide if it's worth your hours.")

        book_title = st.text_input("Book title", placeholder="e.g. Deep Work")
        book_author = st.text_input("Author (optional — helps avoid mix-ups)", placeholder="e.g. Cal Newport")

        depth = st.select_slider(
            "How deep do you want to go?",
            options=list(DEPTH_GUIDE.keys()),
            value="Standard"
        )
        st.caption(DEPTH_GUIDE[depth][0])

        st.markdown("---")

        if st.button("📖 Distill this book", type="primary", use_container_width=True):
            if book_title.strip() == "":
                st.warning("⚠️ Please enter a book title.")
            else:
                _, target_words, token_budget = DEPTH_GUIDE[depth]
                author_line = f" by {book_author.strip()}" if book_author.strip() else ""

                book_prompt = f"""The user wants to understand the book "{book_title.strip()}"{author_line} without reading it in full.

Depth requested: {depth} (aim for roughly {target_words} words).

FIRST — honesty check. If you are not confident you know this specific book well (or the title is ambiguous and the author is missing), say so clearly at the top in one or two sentences and, if useful, ask what the user meant or name the likely candidates. Never invent contents, chapters, or claims for a book you do not actually know. It is far better to say "I know this book only partially" than to fabricate.

THEN — distill the book in your own words. Use markdown with these sections (scale the detail to the requested depth):

## 🎯 The Core Idea
The single most important thing this book is trying to say, in plain language.

## 👤 Who This Book Is For
Who gets the most from it, and in what situation it helps most.

## 🧠 The Key Ideas
The main concepts and arguments, explained clearly. For Quick: 3–4 ideas. Standard: 5–7. Deep: 8–12 with fuller explanation. Full: cover every major idea, following the book's own logic and structure.

## 🛠️ What To Actually Do With It
The practical, actionable takeaways — what a reader should change, try, or stop doing.

## ⚖️ Limits & Critiques
Where the book is weaker, overstated, dated, or where thoughtful readers disagree. (Brief for Quick; substantial for Deep/Full.)

## 📌 Bottom Line
Is it worth reading in full — and for whom? One honest verdict.

STRICT rules: Write entirely in your own words. Do NOT reproduce passages, sentences, or extended quotations from the book. Do NOT quote more than a short phrase, and prefer paraphrase always. This is interpretation and explanation, not reproduction. Match the language of the user's input."""

                st.session_state.book_title_saved = book_title.strip()
                st.session_state.book_author_saved = book_author.strip()
                st.session_state.book_depth_saved = depth

                st.markdown("### 📖 The Essence of the Book")
                try:
                    with st.spinner("Distilling the book..."):
                        stream = client.chat.completions.create(
                            model="gpt-5.5",
                            messages=[
                                {"role": "system", "content": SYSTEM_PROMPT},
                                {"role": "user", "content": book_prompt}
                            ],
                            max_completion_tokens=token_budget,
                            stream=True
                        )

                    placeholder = st.empty()
                    full_response = ""
                    for chunk in stream:
                        if chunk.choices[0].delta.content is not None:
                            full_response += chunk.choices[0].delta.content
                            placeholder.markdown(full_response + "▌")
                    placeholder.markdown(full_response)

                    st.session_state.book_summary = full_response
                    st.session_state.book_stage = "result"
                    st.rerun()

                except Exception as e:
                    st.error(f"Connection error. Details: {e}")

    elif st.session_state.book_stage == "result":
        title_line = st.session_state.book_title_saved
        if st.session_state.book_author_saved:
            title_line += f" — {st.session_state.book_author_saved}"
        st.markdown(f"#### 📚 {title_line}")
        st.caption(f"Depth: {st.session_state.book_depth_saved}")

        st.markdown('<div class="content-block">', unsafe_allow_html=True)
        st.markdown("### 📖 The Essence of the Book")
        st.markdown(st.session_state.book_summary)
        st.markdown('</div>', unsafe_allow_html=True)

        st.markdown("---")
        col1, col2 = st.columns(2)
        with col1:
            safe_name = re.sub(r"[^A-Za-z0-9]+", "_", st.session_state.book_title_saved).strip("_") or "book"
            st.download_button(
                label="📥 Download this summary",
                data=f"# {title_line}\n\n" + st.session_state.book_summary,
                file_name=f"{safe_name}_essence.md",
                mime="text/markdown",
                use_container_width=True
            )
        with col2:
            if st.button("🔄 Try another book", use_container_width=True):
                st.session_state.book_stage = "input"
                st.session_state.book_summary = ""
                st.session_state.book_title_saved = ""
                st.session_state.book_author_saved = ""
                st.session_state.book_depth_saved = ""
                st.rerun()
