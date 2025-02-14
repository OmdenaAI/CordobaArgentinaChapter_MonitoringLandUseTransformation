from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    ENV_STATE: str
    API_NAME: str
    API_DESCRIPTION: str
    API_VERSION: str
    HOST: str
    PORT: int
    
    TYPE: str
    PROJECT_ID: str
    PRIVATE_KEY_ID: str
    PRIVATE_KEY: str
    CLIENT_EMAIL: str
    CLIENT_ID: str
    AUTH_URI: str
    TOKEN_URI: str
    AUTH_PROVIDER_X509_CERT_URL: str
    CLIENT_X509_CERT_URL: str
    UNIVERSE_DOMAIN: str

    class Config:
        env_file = ".env"


settings = Settings()

