from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    database_url: str = "postgresql+asyncpg://newshub:newshub123@localhost:5432/newshub"
    rsshub_url: str = "http://localhost:1200"
    ollama_url: str = "http://localhost:11434"
    ollama_model: str = "qwen2.5:7b"
    app_env: str = "development"

    model_config = {"env_file": ".env", "extra": "ignore"}


settings = Settings()
