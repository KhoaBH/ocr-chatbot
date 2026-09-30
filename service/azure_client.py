from functools import lru_cache

from openai import OpenAI

import config


@lru_cache(maxsize=1)
def get_client() -> OpenAI:
    config.require_key()
    return OpenAI(base_url=config.AZURE_BASE_URL, api_key=config.AZURE_API_KEY)