from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    database_url: str
    jwt_secret: str
    jwt_algorithm: str = "HS256"
    websocket_server_port: int = 8766
    place_cooldown_seconds: float = 4.0

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")
