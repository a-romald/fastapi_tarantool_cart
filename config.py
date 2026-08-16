from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    HOST: str
    PORT: int
    API_KEY_NAME: str
    VALID_API_KEY: str    
    DEFAULT_TARANTOOL_TTL: int
    CURRENT_UTC: int
    TIMEZONE_NAME: str

    class Config:
        env_file = ".env"


settings = Settings()
