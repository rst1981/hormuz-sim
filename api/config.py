"""Application configuration via pydantic-settings."""

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """War room dashboard API settings."""

    MAX_SIMS: int = 20
    MAX_MC_JOBS: int = 5
    MC_MAX_RUNS: int = 5000
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    ANTHROPIC_API_KEY: str = ""
    SCRAPE_USER_AGENT: str = "HormuzSim/1.0"
    WAR_START_DATE: str = "2026-02-25"

    model_config = {"env_prefix": "HORMUZ_"}


settings = Settings()
