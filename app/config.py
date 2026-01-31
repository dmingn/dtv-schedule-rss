from pydantic import Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    schedule_cache_ttl_seconds: int = Field(
        default=3600, description="Cache TTL for fetched schedules in seconds."
    )


settings = Settings()
