from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    ZHIPUAI_API_KEY: str = ""
    GLM_MODEL: str = "glm-4-plus"
    GLM_TEMPERATURE: float = 0.3
    GLM_MAX_TOKENS: int = 4096
    GENERATED_DOCS_DIR: str = "static/generated"

    class Config:
        env_file = ".env"


settings = Settings()
