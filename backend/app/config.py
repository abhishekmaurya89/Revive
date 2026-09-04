from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=Path(__file__).resolve().parents[1] / ".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    google_api_key: str
    gemini_model: str = "gemini-3.5-flash-lite"

    razorpay_key_id: str
    razorpay_key_secret: str
    razorpay_webhook_secret: str

    mongodb_url: str = "mongodb://localhost:27017"
    mongodb_database: str = "revive"

    max_auto_recovery_amount: int = 100_000
    max_retries: int = 2

    # Stopping rules / compliant escalation (applies to receivables + repeated
    # outreach across every recovery channel: email, SMS, voice, mandate retry).
    max_contact_attempts: int = 5
    contact_cooldown_hours: int = 24
    receivable_reminder_days: int = 15
    receivable_chase_days: int = 30
    receivable_escalate_days: int = 60
    max_auto_receivable_amount: int = 200_000


settings = Settings()
