import config
from models import MergedIssue, RetrievalResult
from service.azure_client import get_client

SYSTEM_PROMPT = """You are a support assistant. Answer using only the knowledge base articles provided.
- Write one separate section for each detected application error code. Start each section with a heading
  line in this form: **ERROR_CODE: article title**
- Under each heading, give numbered steps from the article whose codes include that error.
- Never merge steps from different errors into one list.
- Ignore plain HTTP status numbers (400, 401, 500) and successful 2xx responses. Only address application error codes.
- If an error code has no matching article, say so under its own heading and ask for more detail.
- Do not invent product behavior, settings, or error meanings."""


def _context(results: list[RetrievalResult]) -> str:
    return "\n\n".join(
        f"[Article {i}] {r.entry.title}\nCovers codes: {', '.join(r.entry.error_codes)}\n{r.entry.solution}"
        for i, r in enumerate(results, 1)
    )


def generate_answer(issue: MergedIssue, results: list[RetrievalResult]) -> str:
    if not results:
        return (
            "I couldn't find a matching article for this issue.\n\n"
            "Try adding the exact error message or code, or attach a clearer screenshot."
        )

    user_prompt = (
        f"User description:\n{issue.description or '(none)'}\n\n"
        f"Text read from screenshot:\n{issue.ocr_text or '(none)'}\n\n"
        f"Detected error codes: {', '.join(issue.error_codes) or '(none)'}\n\n"
        f"Knowledge base articles:\n{_context(results)}"
    )
    resp = get_client().chat.completions.create(
        model=config.CHAT_DEPLOYMENT,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt},
        ],
    )
    return resp.choices[0].message.content.strip()