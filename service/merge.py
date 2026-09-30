from models import ImageExtraction, MergedIssue, TextExtraction


def merge(description: str, text_ex: TextExtraction, image_ex: ImageExtraction) -> MergedIssue:
    codes = list(dict.fromkeys(text_ex.error_codes + image_ex.error_codes))
    query = " ".join(part for part in (description.strip(), image_ex.text[:500]) if part)
    return MergedIssue(
        description=description.strip(),
        ocr_text=image_ex.text,
        error_codes=codes,
        keywords=text_ex.keywords,
        query=query,
    )