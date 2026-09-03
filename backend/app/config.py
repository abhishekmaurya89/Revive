from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=Path(__file__).resolve().parents[1] / ".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    google_api_key: str

    razorpay_key_id: str
    razorpay_key_secret: str

    razorpay_webhook_secret: str


settings = Settings()

