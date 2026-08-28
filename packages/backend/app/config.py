from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    database_url: str
    jwt_secret: str
    jwt_expires_in_minutes: int = 60
    port: int = 8000

    class Config:
        env_file = ".env"


settings = Settings()