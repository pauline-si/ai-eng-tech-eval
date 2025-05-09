from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    OPENAI_API_KEY: str
    OPENAI_LLM: str = "gpt-3.5-turbo"
    VOICE: str = "alloy"
    SPEECH_MODEL: str = "gpt-4o-mini-tts"
    TRANSCRIPTION_MODEL: str = "gpt-4o-transcribe"
    SHOPIFY_API_ACCESS_TOKEN: str = "Your token"
    SHOPIFY_API_VERSION: str = "2023-10"
    SHOPIFY_SHOP_URL: str = "my-test-store-umain.myshopify.com"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()
