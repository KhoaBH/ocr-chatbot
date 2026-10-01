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


def search(issue: MergedIssue, per_query: int = 2) -> list[RetrievalResult]:
    client = get_milvus()
    if not client.has_collection(config.MILVUS_COLLECTION):
        raise RuntimeError("Milvus collection not found. Run the ingest script first.")
    client.load_collection(collection_name=config.MILVUS_COLLECTION)

    SKIP = {"please look at this screenshot."}

    queries = [
        q for q in dict.fromkeys(
            [issue.description.strip(), issue.query.strip(), *issue.error_codes]
        )
        if q and not q.isdigit() and q.lower() not in SKIP
    ]
    if not queries:
        return []

    batches = client.search(
        collection_name=config.MILVUS_COLLECTION,
        data=embed(queries),
        limit=per_query * 3,
        output_fields=OUTPUT_FIELDS,
    )

    codes = {c.lower() for c in issue.error_codes}
    chosen: dict[str, RetrievalResult] = {}
    for hits in batches:
        scored = []
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
            print(entry.id, entry.title, round(hit["distance"], 3), score)
            if score >= config.MIN_SCORE:
                scored.append(RetrievalResult(entry=entry, score=score))
        scored.sort(key=lambda r: r.score, reverse=True)
        for r in scored[:per_query]:
            if r.entry.id not in chosen or r.score > chosen[r.entry.id].score:
                chosen[r.entry.id] = r

    return sorted(chosen.values(), key=lambda r: r.score, reverse=True)