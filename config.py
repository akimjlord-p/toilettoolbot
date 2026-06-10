from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    bot_token: str
    api_url: str
    bot_secret: str
    channel_id: str = ""   # канал для публикаций
    chat_id: str = ""      # чат (группа обсуждений) для титулов


settings = Settings()
