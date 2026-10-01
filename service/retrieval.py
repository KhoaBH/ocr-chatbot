from functools import lru_cache

import config
from models import KBEntry, MergedIssue, RetrievalResult
from service.embedding import embed
from pymilvus import MilvusClient

OUTPUT_FIELDS = ["title", "solution", "error_codes", "keywords"]
CODE_BOOST = 0.15  # added per matching error code, so exact codes outrank fuzzy matches


@lru_cache(maxsize=1)
def get_milvus() -> MilvusClient:
    return MilvusClient(uri=config.MILVUS_URI)


def search(issue: MergedIssue, top_k: int = 3) -> list[RetrievalResult]:
    client = get_milvus()
    if not client.has_collection(config.MILVUS_COLLECTION):
        raise RuntimeError(
            "Milvus collection not found. Run: python -m script.ingest_kb"
        )
    client.load_collection(collection_name=config.MILVUS_COLLECTION)

    query = issue.query.strip()
    if not query:
        return []

    hits = client.search(
        collection_name=config.MILVUS_COLLECTION,
        data=[embed([query])[0]],
        limit=top_k * 2,
        output_fields=OUTPUT_FIELDS,
    )[0]

    codes = {c.lower() for c in issue.error_codes}
    results = []
    for hit in hits:
        e = hit["entity"]
        entry = KBEntry(
            id=str(hit["id"]),
            title=e["title"],
            error_codes=e.get("error_codes", []),
            keywords=e.get("keywords", []),
            solution=e["solution"],
        )
        matched = len(codes & {c.lower() for c in entry.error_codes})
        score = hit["distance"] + CODE_BOOST * matched  # COSINE: higher is closer
        if score >= config.MIN_SCORE:
            results.append(RetrievalResult(entry=entry, score=round(score, 3)))
    return sorted(results, key=lambda r: r.score, reverse=True)[:top_k]