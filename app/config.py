from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    schedule_cache_ttl_seconds: int = 3600


settings = Settings()
