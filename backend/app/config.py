from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    google_api_key: str

    razorpay_key_id: str
    razorpay_key_secret: str


settings = Settings()