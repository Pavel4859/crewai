import os

from crewai import LLM
from dotenv import load_dotenv

load_dotenv()

# Документация: https://proxyapi.ru/docs/openai-text-generation
PROXYAPI_OPENAI_BASE_URL = "https://api.proxyapi.ru/openai/v1"
DEFAULT_MODEL = "gpt-4o-mini"


def get_llm() -> LLM:
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise ValueError(
            "Не задан OPENAI_API_KEY в .env. "
            "Укажите ключ с https://proxyapi.ru"
        )

    base_url = os.getenv("OPENAI_BASE_URL", PROXYAPI_OPENAI_BASE_URL)
    model = (
        os.getenv("OPENAI_MODEL_NAME")
        or os.getenv("MODEL")
        or DEFAULT_MODEL
    )

    return LLM(
        model=model,
        api_key=api_key,
        base_url=base_url,
    )


def get_llm_info() -> dict[str, str]:
    return {
        "provider": "ProxyAPI",
        "base_url": os.getenv("OPENAI_BASE_URL", PROXYAPI_OPENAI_BASE_URL),
        "model": (
            os.getenv("OPENAI_MODEL_NAME")
            or os.getenv("MODEL")
            or DEFAULT_MODEL
        ),
        "api_key_set": bool(os.getenv("OPENAI_API_KEY")),
    }
