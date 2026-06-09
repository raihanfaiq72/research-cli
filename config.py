import os
from dotenv import load_dotenv

load_dotenv()


class Settings:
    unpaywall_email: str = os.getenv("UNPAYWALL_EMAIL", "")
    core_api_key: str = os.getenv("CORE_API_KEY", "")
    semantic_scholar_api_key: str = os.getenv("SEMANTIC_SCHOLAR_API_KEY", "")

    request_timeout: int = int(os.getenv("REQUEST_TIMEOUT", "30"))
    max_retries: int = int(os.getenv("MAX_RETRIES", "3"))
    cache_enabled: bool = os.getenv("CACHE_ENABLED", "true").lower() == "true"
    cache_ttl: int = int(os.getenv("CACHE_TTL", "3600"))

    reading_list_path: str = os.path.join(
        os.path.dirname(__file__), "data", "reading_list.json"
    )


settings = Settings()
