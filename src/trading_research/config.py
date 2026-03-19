from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_name: str = "Intelligent Trading Research Platform"
    environment: str = "development"

    openai_api_key: str | None = Field(default=None, alias="OPENAI_API_KEY")
    anthropic_api_key: str | None = Field(default=None, alias="ANTHROPIC_API_KEY")
    alpha_vantage_api_key: str | None = Field(default=None, alias="ALPHA_VANTAGE_API_KEY")
    news_api_key: str | None = Field(default=None, alias="NEWS_API_KEY")
    finnhub_api_key: str | None = Field(default=None, alias="FINNHUB_API_KEY")
    langsmith_api_key: str | None = Field(default=None, alias="LANGSMITH_API_KEY")
    langsmith_tracing: bool = Field(default=False, alias="LANGSMITH_TRACING")
    langsmith_project: str = Field(default="trading-research-platform", alias="LANGSMITH_PROJECT")

    postgres_url: str = Field(
        default="postgresql://postgres:postgres@localhost:5432/trading_research",
        alias="POSTGRES_URL",
    )
    redis_url: str = Field(default="redis://localhost:6379/0", alias="REDIS_URL")
    chroma_persist_directory: Path = Field(default=Path("./chroma"), alias="CHROMA_PERSIST_DIRECTORY")
    report_output_dir: Path = Field(default=Path("./reports"), alias="REPORT_OUTPUT_DIR")

    default_model: str = Field(default="gpt-4o-mini", alias="DEFAULT_MODEL")
    openai_embedding_model: str = Field(
        default="text-embedding-3-small",
        alias="OPENAI_EMBEDDING_MODEL",
    )
    market_benchmark: str = Field(default="SPY", alias="MARKET_BENCHMARK")


settings = Settings()

