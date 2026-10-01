from service.azure_client import get_client

import config


def embed(texts: list[str]) -> list[list[float]]:
	"""Create embeddings through the configured Azure OpenAI deployment."""
	if not texts:
		return []

	response = get_client().embeddings.create(
		model=config.EMBEDDING_DEPLOYMENT,
		input=texts,
	)
	vectors = [item.embedding for item in response.data]
	if any(len(vector) != config.EMBEDDING_DIM for vector in vectors):
		raise RuntimeError(
			f"Embedding dimension does not match Milvus configuration ({config.EMBEDDING_DIM})"
		)
	return vectors
