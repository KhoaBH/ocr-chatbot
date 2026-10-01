import config
from models import MergedIssue, RetrievalResult
from service.azure_client import get_client

SYSTEM_PROMPT = """You are a support assistant. Answer using only the knowledge base articles provided.
- If error codes are listed, write one separate section per code. Start each with **ERROR_CODE: article title**
  and give numbered steps from the article that covers that code.
- If no error code was given, the user described a symptom. Choose the article or articles that best fit it
  and give their steps. If more than one could fit, give a short section for each and end by asking which
  error message the user sees.
- Never merge steps from different articles into one list.
- HTTP status numbers (400, 401, 500) are context only. Never use one as a section heading.
- After each step taken from an article, cite it with the article id in square brackets, like [KB-1005].
- Always address the typed problem. If the screenshot shows a different error than the one the user describes,
  say so in one sentence, then answer both separately.
- If the articles clearly do not fit the problem, say so and ask for the exact error message.
- Do not invent product behavior, settings, or error meanings."""


def _context(results: list[RetrievalResult]) -> str:
    return "\n\n".join(
        f"[{r.entry.id}] {r.entry.title}\nCovers codes: {', '.join(r.entry.error_codes)}\n{r.entry.solution}"
        for r in results
    )

def generate_answer(issue: MergedIssue, results: list[RetrievalResult]) -> str:
    if not results:
        return (
            "I couldn't find a matching article for this issue.\n\n"
            "Try adding the exact error message or code, or attach a clearer screenshot."
        )

    app_codes = [c for c in issue.error_codes if not c.isdigit()]
    http_codes = [c for c in issue.error_codes if c.isdigit()]

    if app_codes:
        codes_line = f"Detected error codes to answer: {', '.join(app_codes)}"
    else:
        codes_line = "No error code detected. The user described a symptom."
    if http_codes:
        codes_line += f"\nHTTP status seen (context only): {', '.join(http_codes)}"

    user_prompt = (
        f"User description:\n{issue.description or '(none)'}\n\n"
        f"Text read from screenshot:\n{issue.ocr_text or '(none)'}\n\n"
        f"{codes_line}\n\n"
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