from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    ARK_API_KEY: str = ""
    ARK_BASE_URL: str = "https://ark.cn-beijing.volces.com/api/coding/v3"
    ARK_CHAT_MODEL: str = "doubao-seed-2-0-code-preview-260215"
    LLM_TEMPERATURE: float = 0.3
    LLM_MAX_TOKENS: int = 4096
    GENERATED_DOCS_DIR: str = "static/generated"
    SUPABASE_URL: str = ""
    SUPABASE_KEY: str = ""

    class Config:
        env_file = ".env"


settings = Settings()
