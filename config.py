from pydantic import BaseModel
from pydantic_settings import BaseSettings, SettingsConfigDict


class TGSettings(BaseModel):
    api_id: str
    api_hash: str
    user: str
    phone: str


class ProxySettings(BaseModel):
    host: str = "127.0.0.1"
    port: int = 1080
    secret: str


class SchedulerConfig(BaseModel):
    source_channel: str
    target_channel: str
    posts_num: int = 5


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_nested_delimiter="__",
        extra="ignore",
    )

    tg_settings: TGSettings
    proxy: ProxySettings
    scheduler: SchedulerConfig


def get_settings() -> Settings:
    settings = Settings()
    return settings