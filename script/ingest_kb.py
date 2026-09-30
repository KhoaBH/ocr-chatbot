"""Embed data/kb.json and load it into Milvus. Run from chatbot/: python -m scripts.ingest_kb"""
import json

from pymilvus import MilvusClient

import config
from services.embeddings import embed


def main() -> None:
    with open(config.KB_PATH, encoding="utf-8") as f:
        entries = json.load(f)

    texts = [
        f'{e["title"]}. {" ".join(e["keywords"])}. {" ".join(e["error_codes"])}. {e["solution"]}'
        for e in entries
    ]
    vectors = embed(texts)

    client = MilvusClient(uri=config.MILVUS_URI)
    if client.has_collection(config.MILVUS_COLLECTION):
        client.drop_collection(config.MILVUS_COLLECTION)
    client.create_collection(
        collection_name=config.MILVUS_COLLECTION,
        dimension=config.EMBEDDING_DIM,
        metric_type="COSINE",
        id_type="string",
        max_length=64,
    )
    client.insert(
        collection_name=config.MILVUS_COLLECTION,
        data=[
            {
                "id": e["id"],
                "vector": v,
                "title": e["title"],
                "solution": e["solution"],
                "error_codes": e["error_codes"],
                "keywords": e["keywords"],
            }
            for e, v in zip(entries, vectors)
        ],
    )
    print(f"Ingested {len(entries)} articles into '{config.MILVUS_COLLECTION}' at {config.MILVUS_URI}")


if __name__ == "__main__":
    main()