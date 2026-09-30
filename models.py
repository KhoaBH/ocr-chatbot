from dataclasses import dataclass, field


@dataclass
class TextExtraction:
    error_codes: list[str] = field(default_factory=list)
    keywords: list[str] = field(default_factory=list)


@dataclass
class ImageExtraction:
    text: str = ""
    error_codes: list[str] = field(default_factory=list)
    available: bool = False  # True only if OCR actually ran
    note: str = ""


@dataclass
class MergedIssue:
    description: str
    ocr_text: str
    error_codes: list[str]
    keywords: list[str]
    query: str


@dataclass
class KBEntry:
    id: str
    title: str
    error_codes: list[str]
    keywords: list[str]
    solution: str


@dataclass
class RetrievalResult:
    entry: KBEntry
    score: float