# app.py
# Requires: streamlit >= 1.43  (uses st.chat_input(accept_file=True))

import html

import streamlit as st

from service.image_extraction import extract_from_image
from service.llm_service import generate_answer
from service.merge import merge
from service.retrieval import search
from service.text_extraction import extract_from_text

st.set_page_config(
    page_title="Support Assistant",
    page_icon=":material/support_agent:",
    layout="centered",
    initial_sidebar_state="auto",
)

# ---------------------------------------------------------------- styling
st.markdown(
    """
<style>
@import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Sans:wght@400;500;600&display=swap');

:root {
  --ink: #1b2330;
  --muted: #667085;
  --line: #e4e7ec;
  --canvas: #f7f8fa;
  --accent: #2f4ed1;
  --accent-soft: #eef1fd;
  --ok: #157f4b;
  --idle: #98a2b3;
}

/* Font: set on text elements only, so Material icon glyphs keep their own font */
.stApp, .stApp :is(p, li, label, button, input, textarea, summary, h1, h2, h3, h4) {
  font-family: 'IBM Plex Sans', system-ui, sans-serif;
}
span[data-testid="stIconMaterial"] { font-family: 'Material Symbols Rounded' !important; }

.stApp { background: var(--canvas); color: var(--ink); }

/* hide default chrome without touching the sidebar toggle */
#MainMenu, footer { display: none; }
header[data-testid="stHeader"] { background: transparent; }
.block-container { max-width: 820px; padding-top: 1.5rem; padding-bottom: 8rem; }

/* header */
.app-header { display: flex; align-items: center; gap: .75rem; padding-bottom: 1rem;
  border-bottom: 1px solid var(--line); margin-bottom: 1.25rem; }
.app-header .mark { width: 36px; height: 36px; border-radius: 9px; background: var(--accent);
  color: #fff; display: grid; place-items: center; font-weight: 600; flex: none; }
.app-header h1 { font-size: 1.05rem; font-weight: 600; margin: 0; padding: 0; line-height: 1.2; }
.app-header p { margin: 0; font-size: .82rem; color: var(--muted); }

/* chat messages */
[data-testid="stChatMessage"] { background: transparent; padding: .6rem 0; gap: .9rem; }
[data-testid="stChatMessage"] p { line-height: 1.6; }
[data-testid="stChatMessage"]:has([data-testid="stChatMessageAvatarUser"])
  [data-testid="stMarkdownContainer"] {
  background: var(--accent-soft); border: 1px solid #dbe1fa; border-radius: 12px;
  padding: .6rem .9rem; width: fit-content; max-width: 100%; }
[data-testid="stChatMessage"] [data-testid="stMarkdownContainer"] p:last-child { margin-bottom: 0; }
[data-testid="stExpander"] { background: #fff; border: 1px solid var(--line); border-radius: 10px; }
[data-testid="stExpander"] summary { font-size: .88rem; color: var(--muted); }

/* empty state */
.empty { text-align: center; padding: 3rem 0 1.25rem; }
.empty h2 { font-size: 1.35rem; font-weight: 600; margin: 0 0 .35rem; padding: 0; }
.empty p { color: var(--muted); font-size: .95rem; margin: 0; }

/* pipeline step list */
.steps { display: flex; flex-direction: column; gap: .4rem; font-size: .88rem; }
.steps .row { display: flex; align-items: flex-start; gap: .6rem; }
.steps .badge { width: 8px; height: 8px; border-radius: 50%; background: var(--idle);
  flex: none; margin-top: .45rem; }
.steps .badge.done { background: var(--ok); }
.steps .text { min-width: 0; overflow-wrap: anywhere; }
.steps .name { font-weight: 500; }
.steps .note { color: var(--muted); display: block; }

/* sidebar */
[data-testid="stSidebar"] { background: #fff; border-right: 1px solid var(--line); }
[data-testid="stSidebar"] h3 { font-size: .95rem; font-weight: 600; margin-top: .5rem; }

/* buttons + input */
.stButton > button { border-radius: 8px; border: 1px solid var(--line); background: #fff;
  color: var(--ink); font-weight: 500; min-height: 3.2rem; line-height: 1.3;
  transition: border-color .15s, color .15s; }
.stButton > button:hover { border-color: var(--accent); color: var(--accent); background: #fff; }
.stButton > button:focus-visible { outline: 2px solid var(--accent); outline-offset: 2px; }
[data-testid="stChatInput"] { border-radius: 12px; }
[data-testid="stChatInput"]:focus-within { border-color: var(--accent); }

@media (prefers-reduced-motion: reduce) { * { transition: none !important; } }
</style>
""",
    unsafe_allow_html=True,
)

# ------------------------------------------------------------------ state
AVATARS = {"user": ":material/person:", "assistant": ":material/support_agent:"}

SUGGESTIONS = [
    "The app crashes on login",
    "I get a 500 error when saving",
    "Payment fails at checkout",
]

st.session_state.setdefault("messages", [])
st.session_state.setdefault("pending", None)
st.session_state.setdefault("last_steps", None)


# --------------------------------------------------------------- pipeline
def run_pipeline(text: str, image_bytes: bytes | None) -> dict:
    steps = []

    image_ex = extract_from_image(image_bytes)
    steps.append({"name": "Screenshot OCR", "note": image_ex.note, "done": image_ex.available})

    text_ex = extract_from_text(text)
    steps.append(
        {
            "name": "Text extraction",
            "note": f"{len(text_ex.error_codes)} error codes, {len(text_ex.keywords)} keywords",
            "done": True,
        }
    )

    issue = merge(text, text_ex, image_ex)
    steps.append({"name": "Query construction", "note": "Retrieval query prepared", "done": True})

    try:
        results = search(issue)
        steps.append(
            {"name": "Knowledge retrieval", "note": f"{len(results)} matching articles", "done": True}
        )
    except Exception as exc:
        steps.append({"name": "Knowledge retrieval", "note": f"Failed: {exc}", "done": False})
        return {"steps": steps, "answer": f"Retrieval failed.\n\n`{exc}`"}

    try:
        answer = generate_answer(issue, results)
        steps.append({"name": "Answer generation", "note": "Generated from retrieved articles", "done": True})
    except Exception as exc:
        steps.append({"name": "Answer generation", "note": f"Failed: {exc}", "done": False})
        answer = f"Answer generation failed.\n\n`{exc}`"

    return {"steps": steps, "answer": answer}


# -------------------------------------------------------------- rendering
def render_steps(steps: list[dict]) -> None:
    # Escape everything: notes can contain error text with < > & that would break the HTML.
    rows = "".join(
        f'<div class="row"><span class="badge {"done" if s["done"] else ""}"></span>'
        f'<span class="text"><span class="name">{html.escape(str(s["name"]))}</span>'
        f'<span class="note">{html.escape(str(s["note"]))}</span></span></div>'
        for s in steps
    )
    st.markdown(f'<div class="steps">{rows}</div>', unsafe_allow_html=True)


def render_message(msg: dict) -> None:
    with st.chat_message(msg["role"], avatar=AVATARS[msg["role"]]):
        if msg.get("image"):
            st.image(msg["image"], width=320)
        st.markdown(msg["content"])
        if msg.get("steps"):
            with st.expander("How this was analyzed"):
                render_steps(msg["steps"])


# ----------------------------------------------------------------- header
st.markdown(
    """
<div class="app-header">
  <div class="mark">S</div>
  <div><h1>Support Assistant</h1><p>Describe an issue or attach an error screenshot</p></div>
</div>
""",
    unsafe_allow_html=True,
)

# -------------------------------------------------------------- user input
# Read input first so the history below already contains the new message.
submission = st.chat_input(
    "Describe the issue",
    accept_file=True,
    file_type=["png", "jpg", "jpeg"],
)

user_text, image_bytes = None, None
if submission:
    user_text = (submission.text or "").strip()
    if submission.files:
        image_bytes = submission.files[0].getvalue()
    if not user_text and image_bytes:
        user_text = "Please look at this screenshot."
elif st.session_state.pending:
    user_text = st.session_state.pending
    st.session_state.pending = None

if user_text:
    st.session_state.messages.append({"role": "user", "content": user_text, "image": image_bytes})

# ------------------------------------------------------------ chat history
if not st.session_state.messages:
    st.markdown(
        '<div class="empty"><h2>What are you running into?</h2>'
        "<p>Describe the problem in a sentence or two. A screenshot of the error helps.</p></div>",
        unsafe_allow_html=True,
    )
    cols = st.columns(len(SUGGESTIONS))
    for i, (col, text) in enumerate(zip(cols, SUGGESTIONS)):
        if col.button(text, key=f"suggestion_{i}", use_container_width=True):
            st.session_state.pending = text
            st.rerun()

for m in st.session_state.messages:
    render_message(m)

# --------------------------------------------------------------- response
if user_text:
    with st.chat_message("assistant", avatar=AVATARS["assistant"]):
        with st.status("Analyzing issue", expanded=False) as status:
            result = run_pipeline(user_text, image_bytes)
            status.update(label="Analysis complete", state="complete")
        st.markdown(result["answer"])
        with st.expander("How this was analyzed"):
            render_steps(result["steps"])

    st.session_state.messages.append(
        {
            "role": "assistant",
            "content": result["answer"],
            "steps": result["steps"],
            "image": None,
        }
    )
    st.session_state.last_steps = result["steps"]

# ---------------------------------------------------------------- sidebar
# Rendered last so it shows the analysis that just ran.
with st.sidebar:
    st.markdown("### Session")
    if st.button("New conversation", icon=":material/add:", use_container_width=True):
        st.session_state.messages = []
        st.session_state.pending = None
        st.session_state.last_steps = None
        st.rerun()

    st.markdown("### Last analysis")
    if st.session_state.last_steps:
        render_steps(st.session_state.last_steps)
    else:
        st.caption("Appears after your first message.")
    st.caption("Attach a PNG or JPG screenshot with the paperclip in the message box.")