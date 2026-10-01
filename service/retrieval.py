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
        raise RuntimeError("Milvus collection not found. Run the ingest script first.")
    client.load_collection(collection_name=config.MILVUS_COLLECTION)

    queries = [q for q in [issue.query.strip(), *issue.error_codes] if q]
    if not queries:
        return []

    batches = client.search(
        collection_name=config.MILVUS_COLLECTION,
        data=embed(queries),
        limit=top_k * 2,
        output_fields=OUTPUT_FIELDS,
    )

    codes = {c.lower() for c in issue.error_codes}
    best: dict[str, RetrievalResult] = {}
    for hits in batches:
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
            score = round(hit["distance"] + CODE_BOOST * matched, 3)
            if score >= config.MIN_SCORE and (entry.id not in best or score > best[entry.id].score):
                best[entry.id] = RetrievalResult(entry=entry, score=score)

    limit = max(top_k, len(issue.error_codes))
    return sorted(best.values(), key=lambda r: r.score, reverse=True)[:limit]