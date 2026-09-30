import re

from models import TextExtraction

_HTTP = re.compile(r"\b([45]\d{2})\b")
_CONST = re.compile(r"\b([A-Z][A-Z0-9]*_[A-Z0-9_]{2,})\b")
_EXC = re.compile(r"\b([A-Za-z]+(?:Error|Exception))\b")
_WORD = re.compile(r"[a-zA-Z]{4,}")
_STOP = {
    "this", "that", "with", "from", "have", "when", "then", "there", "they", "just",
    "please", "look", "screenshot", "issue", "error", "cannot", "still", "after",
}


def _dedupe(items):
    return list(dict.fromkeys(items))


def extract_from_text(text: str) -> TextExtraction:
    codes = _HTTP.findall(text) + _CONST.findall(text) + _EXC.findall(text)
    words = [w.lower() for w in _WORD.findall(text)]
    keywords = [w for w in words if w not in _STOP]
    return TextExtraction(error_codes=_dedupe(codes), keywords=_dedupe(keywords))