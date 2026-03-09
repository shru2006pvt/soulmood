from __future__ import annotations

import json
import hashlib
from datetime import date, datetime, timedelta
from pathlib import Path

import altair as alt
import pandas as pd
import streamlit as st

st.set_page_config(page_title="SoulMood", page_icon="✨", layout="wide")

DATA_DIR = Path("data")
DATA_FILE = DATA_DIR / "mood_data.csv"
CUSTOM_MOODS_FILE = DATA_DIR / "custom_moods.json"
USERS_FILE = DATA_DIR / "users.json"
LOGO_FILES = [Path("assets/Amitylogo.jpeg"), Path("assets/happinesslogo.png")]
DATA_COLUMNS = ["Date", "Time", "Mood", "Journal"]


def load_css(path: str) -> None:
    css_path = Path(path)
    if css_path.exists():
        st.markdown(f"<style>{css_path.read_text(encoding='utf-8')}</style>", unsafe_allow_html=True)
    else:
        st.warning("CSS file not found. Expected: styles/style.css")


def ensure_data_store() -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    if not DATA_FILE.exists():
        pd.DataFrame(columns=DATA_COLUMNS).to_csv(DATA_FILE, index=False)
    if not CUSTOM_MOODS_FILE.exists():
        CUSTOM_MOODS_FILE.write_text("[]", encoding="utf-8")
    if not USERS_FILE.exists():
        USERS_FILE.write_text("[]", encoding="utf-8")


@st.cache_data(show_spinner=False)
def load_entries() -> pd.DataFrame:
    try:
        return pd.read_csv(DATA_FILE)
    except Exception:
        return pd.DataFrame(columns=DATA_COLUMNS)


def save_entry(mood: str, journal_text: str) -> None:
    entry = pd.DataFrame(
        [
            {
                "Date": date.today().isoformat(),
                "Time": datetime.now().strftime("%H:%M"),
                "Mood": mood,
                "Journal": journal_text.strip(),
            }
        ]
    )
    entry.to_csv(DATA_FILE, mode="a", header=False, index=False)
    load_entries.clear()


def calculate_streak(df: pd.DataFrame) -> int:
    if df.empty or "Date" not in df.columns:
        return 0
    days = set(pd.to_datetime(df["Date"], errors="coerce").dt.date.dropna())
    streak = 0
    today = date.today()
    while (today - timedelta(days=streak)) in days:
        streak += 1
    return streak


def mood_questions(mood_name: str) -> list[str]:
    prompts = {
        "Happy": [
            "What made you feel happy today?",
            "Who or what are you grateful for right now?",
            "How can you carry this energy through the day?",
        ],
        "Sad": [
            "What feels heaviest in your heart right now?",
            "What kind of support would help you today?",
            "What is one gentle thing you can do for yourself now?",
        ],
        "Anxious": [
            "What thought keeps repeating right now?",
            "What part of this situation is in your control?",
            "What can help your body feel safer in this moment?",
        ],
        "Angry": [
            "What triggered this feeling?",
            "Which boundary or value feels crossed?",
            "How can you express this safely and clearly?",
        ],
        "Fear": [
            "What feels threatening or uncertain right now?",
            "What is one fact that helps you stay grounded?",
            "Who or what can help you feel safer today?",
        ],
        "Overwhelmed": [
            "What is taking up most of your mental space right now?",
            "Which one task matters most at this moment?",
            "What can you postpone, delegate, or simplify today?",
        ],
    }
    return prompts.get(
        mood_name,
        [
            f"What is most present in your {mood_name.lower()} mood right now?",
            "What do you need most in this moment?",
            "What is one kind step you can take next?",
        ],
    )


def read_custom_moods() -> list[dict]:
    try:
        raw = json.loads(CUSTOM_MOODS_FILE.read_text(encoding="utf-8"))
        return raw if isinstance(raw, list) else []
    except Exception:
        return []


def write_custom_moods(custom_moods: list[dict]) -> None:
    CUSTOM_MOODS_FILE.write_text(json.dumps(custom_moods, indent=2), encoding="utf-8")


def read_users() -> list[dict]:
    try:
        raw = json.loads(USERS_FILE.read_text(encoding="utf-8"))
        return raw if isinstance(raw, list) else []
    except Exception:
        return []


def write_users(users: list[dict]) -> None:
    USERS_FILE.write_text(json.dumps(users, indent=2), encoding="utf-8")


def password_hash(password: str) -> str:
    return hashlib.sha256(password.encode("utf-8")).hexdigest()


def register_user(username: str, password: str) -> tuple[bool, str]:
    users = read_users()
    uname = username.strip().lower()
    if any(u.get("username") == uname for u in users):
        return False, "Username already exists."
    users.append({"username": uname, "password_hash": password_hash(password)})
    write_users(users)
    return True, "Account created. Please sign in."


def authenticate_user(username: str, password: str) -> bool:
    uname = username.strip().lower()
    p_hash = password_hash(password)
    return any(u.get("username") == uname and u.get("password_hash") == p_hash for u in read_users())


def render_login_page() -> None:
    st.markdown('<h1 class="brand-title">SoulMood</h1>', unsafe_allow_html=True)
    st.markdown(
        """
        <section class="hero mood-halo">
            <div class="hero-mark">✦</div>
            <h2>Sign in to continue</h2>
            <p>Use your SoulMood account to access your private mood journal.</p>
        </section>
        """,
        unsafe_allow_html=True,
    )

    sign_in_tab, sign_up_tab = st.tabs(["Sign In", "Create Account"])

    with sign_in_tab:
        with st.form("signin_form", clear_on_submit=False):
            username = st.text_input("Username", placeholder="Enter your username")
            password = st.text_input("Password", type="password", placeholder="Enter your password")
            login_clicked = st.form_submit_button("Log In", type="primary")
        if login_clicked:
            if authenticate_user(username, password):
                st.session_state.user_info = {"username": username.strip().lower()}
                st.success("Login successful.")
                st.rerun()
            else:
                st.error("Invalid username or password.")

    with sign_up_tab:
        with st.form("signup_form", clear_on_submit=True):
            new_username = st.text_input("Create username", placeholder="Choose a username")
            new_password = st.text_input("Create password", type="password", placeholder="Choose a password")
            confirm_password = st.text_input("Confirm password", type="password", placeholder="Re-enter password")
            signup_clicked = st.form_submit_button("Create Account")
        if signup_clicked:
            if len(new_username.strip()) < 3:
                st.warning("Username must be at least 3 characters.")
            elif len(new_password) < 6:
                st.warning("Password must be at least 6 characters.")
            elif new_password != confirm_password:
                st.warning("Passwords do not match.")
            else:
                ok, msg = register_user(new_username, new_password)
                if ok:
                    st.success(msg)
                else:
                    st.warning(msg)

    st.stop()


def require_login() -> None:
    if st.query_params.get("logout") == "1":
        st.session_state.pop("user_info", None)
        st.query_params.clear()
        st.rerun()

    if st.session_state.get("user_info"):
        st.markdown(
            """
            <form method="get" class="corner-signout-form">
                <input type="hidden" name="logout" value="1">
                <button type="submit" class="corner-signout" title="Sign out" aria-label="Sign out">⏻</button>
            </form>
            """,
            unsafe_allow_html=True,
        )
        return

    render_login_page()


BASE_MOODS = {
    "Happy": {
        "emoji": "☀️",
        "subtitle": "Radiate your inner sunshine",
        "shade": "#f8bf4f",
        "gita": (
            "Happiness born from steady awareness gradually ends suffering and "
            "grows from inner clarity. (BG 18.37)"
        ),
        "buddha": "Happiness does not diminish when shared; one candle lights many.",
        "movie": "Everything Everywhere All at Once",
        "song": "Here Comes The Sun - The Beatles",
    },
    "Sad": {
        "emoji": "💧",
        "subtitle": "Tears water the seeds of growth",
        "shade": "#79c8ff",
        "gita": "Birth and death are natural cycles; impermanence is part of life. (BG 2.27)",
        "buddha": "Pain is certain; suffering depends on how we respond.",
        "movie": "Inside Out",
        "song": "Breathe Me - Sia",
    },
    "Anxious": {
        "emoji": "🌊",
        "subtitle": "Breathe, the storm will pass",
        "shade": "#72dfc5",
        "gita": "Fear softens when we stay rooted in what is real and enduring. (BG 2.16)",
        "buddha": "Freedom grows when we stop living in fear of what may happen.",
        "movie": "Life of Pi",
        "song": "Float On - Modest Mouse",
    },
    "Angry": {
        "emoji": "🔥",
        "subtitle": "Transform fire into wisdom",
        "shade": "#ff8c7a",
        "gita": "Anger clouds judgment, disturbs memory, and weakens discernment. (BG 2.63)",
        "buddha": "Holding anger is like holding a hot coal; you are burned first.",
        "movie": "Kung Fu Panda",
        "song": "Weightless - Marconi Union",
    },
    "Fear": {
        "emoji": "🌫️",
        "subtitle": "Courage begins with one steady breath",
        "shade": "#9ea7ff",
        "gita": "Stand steady in your true nature; what is real in you cannot be destroyed. (BG 2.16)",
        "buddha": "Fear lessens when we meet this moment directly, with awareness and compassion.",
        "movie": "The Secret Life of Walter Mitty",
        "song": "Holocene - Bon Iver",
    },
    "Overwhelmed": {
        "emoji": "🌀",
        "subtitle": "Slow down, simplify, and return to center",
        "shade": "#c8a2ff",
        "gita": "A disciplined mind, returned again and again, becomes a friend to itself. (BG 6.5)",
        "buddha": "When everything feels too much, come back to one breath and one step.",
        "movie": "Soul",
        "song": "Weightless - Marconi Union",
    },
}

SOUNDS = {
    "Silent": None,
    "Soft Piano": "assets/audios/piano.mp3",
    "Nature Sounds": "assets/audios/nature.mp3",
    "Wind Chimes": "assets/audios/chimes.mp3",
}


def all_moods() -> dict[str, dict]:
    moods = dict(BASE_MOODS)
    for item in read_custom_moods():
        name = item.get("name", "").strip()
        if not name:
            continue
        moods[name] = {
            "emoji": item.get("emoji", "🌟"),
            "subtitle": item.get("subtitle", "Your custom emotional space"),
            "shade": item.get("shade", "#d9b76a"),
            "gita": item.get("gita", "Observe your mind with compassion and patience."),
            "buddha": item.get("buddha", "You are allowed to feel this and still move gently forward."),
            "movie": item.get("movie", "Choose a movie that soothes your heart"),
            "song": item.get("song", "Choose music that matches your breath"),
        }
    return moods


def hex_to_rgb(hex_color: str) -> tuple[int, int, int]:
    color = hex_color.strip().lstrip("#")
    if len(color) != 6:
        return (217, 183, 106)
    try:
        return tuple(int(color[i : i + 2], 16) for i in (0, 2, 4))
    except ValueError:
        return (217, 183, 106)


def rgb_to_hex(r: int, g: int, b: int) -> str:
    return f"#{max(0, min(255, r)):02x}{max(0, min(255, g)):02x}{max(0, min(255, b)):02x}"


def darken(hex_color: str, factor: float) -> str:
    r, g, b = hex_to_rgb(hex_color)
    return rgb_to_hex(int(r * factor), int(g * factor), int(b * factor))


def apply_mood_theme(mood_meta: dict | None) -> None:
    if not mood_meta:
        return
    shade = mood_meta.get("shade", "#d9b76a")
    deep_1 = darken(shade, 0.24)
    deep_2 = darken(shade, 0.14)
    st.markdown(
        f"""
        <style>
            .stApp {{
                background:
                    radial-gradient(circle at 16% 14%, {shade}66, transparent 30%),
                    radial-gradient(circle at 85% 16%, {shade}4d, transparent 36%),
                    radial-gradient(circle at 50% 78%, {shade}33, transparent 40%),
                    linear-gradient(155deg, {deep_1}, #140833 52%, {deep_2}) !important;
            }}
            .mood-page-title {{
                color: {shade};
            }}
            .mood-halo {{
                box-shadow: 0 0 0 1px {shade}55, 0 0 38px {shade}22 inset;
            }}
            .hero,
            .recommend-card,
            .quote-card,
            div[data-testid="stMetric"] {{
                border-color: {shade}66 !important;
            }}
        </style>
        """,
        unsafe_allow_html=True,
    )


def render_dashboard(moods: dict[str, dict], entries_df: pd.DataFrame, streak: int) -> None:
    logo_col, head_col, streak_col = st.columns([1, 3, 2])
    with logo_col:
        existing_logos = [logo for logo in LOGO_FILES if logo.exists()]
        if existing_logos:
            l_col1, l_col2 = st.columns(2)
            if len(existing_logos) >= 1:
                with l_col1:
                    st.image(str(existing_logos[0]), width=66)
            if len(existing_logos) >= 2:
                with l_col2:
                    st.image(str(existing_logos[1]), width=78)
    with head_col:
        st.markdown('<h1 class="brand-title">SoulMood</h1>', unsafe_allow_html=True)
    with streak_col:
        st.markdown(
            f"""
            <div class="streak-pill">
                <span>🔥</span><span><b>{streak} day streak</b></span>
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.markdown(
        """
        <section class="hero mood-halo">
            <div class="hero-mark">✦</div>
            <h2>Sacred check-in for your inner world</h2>
            <p>Select a mood to open your dedicated reflection page.</p>
        </section>
        """,
        unsafe_allow_html=True,
    )

    with st.popover("🎧 Choose your sound"):
        selected_sound = st.radio("Sound options", list(SOUNDS.keys()), label_visibility="collapsed")
        sound_path = SOUNDS[selected_sound]
        if sound_path:
            st.audio(sound_path, loop=True)

    st.markdown('<p class="section-title">Select your current mood</p>', unsafe_allow_html=True)

    mood_names = list(moods.keys())
    for i in range(0, len(mood_names), 3):
        row = mood_names[i : i + 3]
        cols = st.columns(3)
        for col, mood_name in zip(cols, row):
            mood = moods[mood_name]
            with col:
                if st.button(f"{mood['emoji']} {mood_name}", key=f"open_{mood_name}", use_container_width=True):
                    st.session_state.page = "mood"
                    st.session_state.selected_mood = mood_name
                    st.rerun()
                st.markdown(f'<p class="mood-subtitle">{mood["subtitle"]}</p>', unsafe_allow_html=True)

    with st.expander("Add your own mood"):
        with st.form("add_mood_form", clear_on_submit=True):
            new_name = st.text_input("Mood name", max_chars=24, placeholder="Hopeful")
            new_emoji = st.text_input("Emoji", max_chars=4, placeholder="🌈")
            new_subtitle = st.text_input("Short line", max_chars=70, placeholder="Soft optimism for a fresh start")
            new_shade = st.color_picker("Mood shade", value="#d6b86a")
            submitted = st.form_submit_button("Save custom mood")

            if submitted:
                mood_name = new_name.strip().title()
                if not mood_name:
                    st.warning("Mood name is required.")
                elif mood_name in moods:
                    st.warning("That mood already exists.")
                else:
                    custom_moods = read_custom_moods()
                    custom_moods.append(
                        {
                            "name": mood_name,
                            "emoji": new_emoji.strip() or "🌟",
                            "subtitle": new_subtitle.strip() or "Your custom emotional space",
                            "shade": new_shade,
                        }
                    )
                    write_custom_moods(custom_moods)
                    st.success(f"Added mood: {mood_name}")
                    st.rerun()

    st.divider()
    st.markdown("### My Journey")
    st.metric("Current Streak", f"{streak} days")
    if entries_df.empty:
        st.info("Log a mood to start your journey.")
        return

    st.markdown("#### Mood of the Week")
    weekly_df = entries_df.copy()
    weekly_df["Date"] = pd.to_datetime(weekly_df["Date"], errors="coerce")
    weekly_df = weekly_df.dropna(subset=["Date"])
    if not weekly_df.empty:
        end_day = pd.Timestamp(date.today())
        start_day = end_day - pd.Timedelta(days=6)
        weekly_df = weekly_df[(weekly_df["Date"] >= start_day) & (weekly_df["Date"] <= end_day)]

        if not weekly_df.empty:
            weekly_df["Day"] = weekly_df["Date"].dt.strftime("%a")
            weekly_counts = (
                weekly_df.groupby(["Day", "Mood"], as_index=False)
                .size()
                .rename(columns={"size": "Count"})
            )

            day_order = [
                (start_day + pd.Timedelta(days=i)).strftime("%a")
                for i in range(7)
            ]
            palette_domain = list(moods.keys())
            palette_range = [moods[name].get("shade", "#d9b76a") for name in palette_domain]

            weekly_line = (
                alt.Chart(weekly_counts)
                .mark_line(point=True, strokeWidth=3)
                .encode(
                    x=alt.X("Day:N", sort=day_order, title=""),
                    y=alt.Y("Count:Q", title="Entries"),
                    color=alt.Color(
                        "Mood:N",
                        scale=alt.Scale(domain=palette_domain, range=palette_range),
                        legend=alt.Legend(title="Mood"),
                    ),
                    tooltip=["Day", "Mood", "Count"],
                )
                .properties(height=280)
            )
            st.altair_chart(weekly_line, use_container_width=True)
        else:
            st.caption("No entries in the last 7 days yet.")
    else:
        st.caption("No valid dates available for weekly chart.")

    st.markdown("#### Overall Mood Distribution")
    mood_counts = entries_df["Mood"].value_counts().rename_axis("Mood").reset_index(name="Count")
    palette_domain = list(moods.keys())
    palette_range = [moods[name].get("shade", "#d9b76a") for name in palette_domain]

    chart = (
        alt.Chart(mood_counts)
        .mark_line(point=True, strokeWidth=3)
        .encode(
            x=alt.X("Mood:N", title=""),
            y=alt.Y("Count:Q", title="Entries"),
            color=alt.Color("Mood:N", scale=alt.Scale(domain=palette_domain, range=palette_range), legend=None),
            tooltip=["Mood", "Count"],
        )
        .properties(height=300)
    )
    st.altair_chart(chart, use_container_width=True)

    with st.expander("Read past entries"):
        st.dataframe(entries_df.sort_values(["Date", "Time"], ascending=False), use_container_width=True)

    st.markdown(
        """
        <section class="creator-card">
            <p class="creator-title">Created by</p>
            <p class="creator-names">Shruti Saxena • Srishti Saxena • Aparnna J • Misha Arora</p>
        </section>
        """,
        unsafe_allow_html=True,
    )


def render_mood_page(moods: dict[str, dict], selected_mood: str, streak: int) -> None:
    mood_data = moods[selected_mood]
    apply_mood_theme(mood_data)

    top_col, back_col = st.columns([4, 1])
    with top_col:
        st.markdown(f'<h1 class="mood-page-title">{mood_data["emoji"]} {selected_mood}</h1>', unsafe_allow_html=True)
        st.markdown(f'<p class="mood-subtitle">{mood_data["subtitle"]}</p>', unsafe_allow_html=True)
    with back_col:
        if st.button("Back", use_container_width=True):
            st.session_state.page = "dashboard"
            st.rerun()

    st.markdown(
        """
        <section class="hero mood-halo">
            <h2>Welcome to your mood space</h2>
            <p>Breathe slowly, write honestly, and let this page hold the moment.</p>
        </section>
        """,
        unsafe_allow_html=True,
    )

    with st.popover("🎧 Choose your sound"):
        selected_sound = st.radio("Sound options", list(SOUNDS.keys()), label_visibility="collapsed")
        sound_path = SOUNDS[selected_sound]
        if sound_path:
            st.audio(sound_path, loop=True)

    st.markdown("### Journal and Wisdom")
    st.markdown(
        f"""
        <article class="quote-card">
            <p class="quote-label">Bhagavad Gita</p>
            <p class="quote-text"><em>"{mood_data['gita']}"</em></p>
        </article>
        """,
        unsafe_allow_html=True,
    )
    st.markdown(
        f"""
        <article class="quote-card">
            <p class="quote-label">Buddhist Reflection</p>
            <p class="quote-text"><em>"{mood_data['buddha']}"</em></p>
        </article>
        """,
        unsafe_allow_html=True,
    )

    st.markdown("#### Guided reflection")
    questions = mood_questions(selected_mood)
    answers: list[str] = []

    with st.form(f"journal_form_{selected_mood}"):
        for i, question in enumerate(questions, start=1):
            answer = st.text_area(
                f"{i}. {question}",
                key=f"{selected_mood}_q_{i}",
                height=90,
                placeholder="Write your response...",
            )
            answers.append(answer.strip())

        journal_entry = st.text_area(
            "Final journal entry",
            height=180,
            placeholder="Now write your full reflection...",
        )
        save_col, _ = st.columns([1, 4])
        with save_col:
            submit_entry = st.form_submit_button("Save", type="primary")

    if submit_entry:
        if journal_entry.strip():
            guided_block = "\n".join(
                [
                    "Guided Reflection:",
                    *[f"Q{i}. {q}\nA{i}. {a or '(no response)'}" for i, (q, a) in enumerate(zip(questions, answers), start=1)],
                    "",
                    "Journal Entry:",
                    journal_entry.strip(),
                ]
            )
            save_entry(selected_mood, guided_block)
            st.toast("Entry saved to your local journal.")
            st.rerun()
        else:
            st.warning("Please complete the final journal entry before saving.")

    st.markdown("### Gentle suggestions")
    movie_col, song_col, streak_col = st.columns(3)
    with movie_col:
        st.markdown(
            f"""
            <article class="recommend-card">
                <p class="recommend-label">Movie</p>
                <h4>{mood_data['movie']}</h4>
            </article>
            """,
            unsafe_allow_html=True,
        )
    with song_col:
        st.markdown(
            f"""
            <article class="recommend-card">
                <p class="recommend-label">Music</p>
                <h4>{mood_data['song']}</h4>
            </article>
            """,
            unsafe_allow_html=True,
        )
    with streak_col:
        st.metric("Streak", f"{streak} days")

    st.caption("Your responses are private and stored only on this device.")


ensure_data_store()
load_css("styles/style.css")
require_login()
all_mood_data = all_moods()
entries = load_entries()
streak_days = calculate_streak(entries)

if "page" not in st.session_state:
    st.session_state.page = "dashboard"
if "selected_mood" not in st.session_state:
    st.session_state.selected_mood = next(iter(all_mood_data))

if st.session_state.page == "mood":
    selected = st.session_state.selected_mood
    if selected not in all_mood_data:
        st.session_state.page = "dashboard"
        st.rerun()
    render_mood_page(all_mood_data, selected, streak_days)
else:
    render_dashboard(all_mood_data, entries, streak_days)
