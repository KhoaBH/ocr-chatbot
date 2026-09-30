# app.py
# Requires: streamlit >= 1.43  (uses st.chat_input(accept_file=True))

import time

import streamlit as st

st.set_page_config(
    page_title="Support Assistant",
    page_icon=":material/support_agent:",
    layout="centered",
    initial_sidebar_state="expanded",
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

html, body, [class*="st-"], .stApp { font-family: 'IBM Plex Sans', system-ui, sans-serif; }
.stApp { background: var(--canvas); color: var(--ink); }

/* remove default Streamlit chrome */
#MainMenu, footer, [data-testid="stToolbar"], [data-testid="stDecoration"] { display: none; }
header[data-testid="stHeader"] { background: transparent; }
.block-container { max-width: 820px; padding-top: 1.5rem; padding-bottom: 7rem; }

/* header */
.app-header { display: flex; align-items: center; gap: .75rem; padding-bottom: 1rem;
  border-bottom: 1px solid var(--line); margin-bottom: 1.25rem; }
.app-header .mark { width: 36px; height: 36px; border-radius: 9px; background: var(--accent);
  color: #fff; display: grid; place-items: center; font-weight: 600; }
.app-header h1 { font-size: 1.05rem; font-weight: 600; margin: 0; padding: 0; line-height: 1.2; }
.app-header p { margin: 0; font-size: .82rem; color: var(--muted); }
.app-header .status { margin-left: auto; font-size: .8rem; color: var(--muted);
  display: flex; align-items: center; gap: .4rem; }
.app-header .dot { width: 8px; height: 8px; border-radius: 50%; background: var(--ok); }

/* messages */
[data-testid="stChatMessage"] { background: transparent; padding: .5rem 0; gap: .9rem; }
[data-testid="stChatMessage"]:has([data-testid="stChatMessageAvatarUser"]) .stMarkdown {
  background: var(--accent-soft); border: 1px solid #dbe1fa; border-radius: 12px;
  padding: .65rem .9rem; width: fit-content; max-width: 100%; }
[data-testid="stChatMessage"] p { line-height: 1.6; }

/* empty state */
.empty { text-align: center; padding: 3rem 0 1.25rem; }
.empty h2 { font-size: 1.35rem; font-weight: 600; margin-bottom: .35rem; }
.empty p { color: var(--muted); font-size: .95rem; }

/* pipeline step list */
.steps { display: flex; flex-direction: column; gap: .35rem; font-size: .88rem; }
.steps .row { display: flex; align-items: center; gap: .6rem; }
.steps .badge { width: 8px; height: 8px; border-radius: 50%; background: var(--idle); flex: none; }
.steps .badge.done { background: var(--ok); }
.steps .name { font-weight: 500; }
.steps .note { color: var(--muted); }

/* sidebar */
[data-testid="stSidebar"] { background: #fff; border-right: 1px solid var(--line); }
[data-testid="stSidebar"] h3 { font-size: .95rem; font-weight: 600; }

/* buttons + input */
.stButton > button { border-radius: 8px; border: 1px solid var(--line); background: #fff;
  color: var(--ink); font-weight: 500; transition: border-color .15s, background .15s; }
.stButton > button:hover { border-color: var(--accent); color: var(--accent); background: #fff; }
.stButton > button:focus-visible, [data-testid="stChatInput"] textarea:focus-visible {
  outline: 2px solid var(--accent); outline-offset: 2px; }
[data-testid="stChatInput"] { border-radius: 12px; border: 1px solid var(--line); background: #fff; }

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

if "messages" not in st.session_state:
    st.session_state.messages = []
if "pending" not in st.session_state:
    st.session_state.pending = None


# --------------------------------------------------------------- pipeline
def run_pipeline(text: str, image_bytes: bytes | None) -> dict:
    steps = []

    # Screenshot processing
    steps.append(
        {
            "name": "Screenshot OCR",
            "note": "Screenshot uploaded and ready for OCR" if image_bytes else "No screenshot provided",
            "done": True,
        }
    )

    # Text processing
    if text.strip():
        steps.append(
            {"name": "Text extraction", "note": f"{len(text)} characters received", "done": True}
        )
    else:
        steps.append({"name": "Text extraction", "note": "No text supplied", "done": False})

    # Retrieval query
    query_text = text.strip()
    steps.append({"name": "Query construction", "note": "Retrieval query prepared", "done": True})

    # Retrieval placeholder
    steps.append({"name": "Knowledge retrieval", "note": "Milvus not connected yet", "done": False})

    answer = (
        "### Debug\n\n"
        "**Query**\n\n"
        "```text\n" + query_text + "\n```\n\n"
        "---\n\n"
        "**Proposed solution will appear here**"
    )
    return {"steps": steps, "answer": answer}


def render_steps(steps: list[dict]) -> None:
    rows = "".join(
        f'<div class="row"><span class="badge {"done" if s["done"] else ""}"></span>'
        f'<span class="name">{s["name"]}</span><span class="note">{s["note"]}</span></div>'
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
  <div class="status"><span class="dot"></span>Online</div>
</div>
""",
    unsafe_allow_html=True,
)

# ------------------------------------------------------------ chat history
if not st.session_state.messages:
    st.markdown(
        '<div class="empty"><h2>What are you running into?</h2>'
        "<p>Describe the problem in a sentence or two. A screenshot of the error helps.</p></div>",
        unsafe_allow_html=True,
    )
    cols = st.columns(len(SUGGESTIONS))
    for col, text in zip(cols, SUGGESTIONS):
        if col.button(text, use_container_width=True):
            st.session_state.pending = text
            st.rerun()

for m in st.session_state.messages:
    render_message(m)

# -------------------------------------------------------------- user input
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
    user_msg = {"role": "user", "content": user_text, "image": image_bytes}
    st.session_state.messages.append(user_msg)
    render_message(user_msg)

    with st.chat_message("assistant", avatar=AVATARS["assistant"]):
        with st.status("Analyzing issue", expanded=False) as status:
            result = run_pipeline(user_text, image_bytes)
            time.sleep(0.4)  # remove once the real pipeline is in place
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