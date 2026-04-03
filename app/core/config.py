from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file='.env', env_file_encoding='utf-8', extra='ignore')

    app_name: str = 'Top 3 Picks Backend'
    apisports_api_key: str
    apisports_base_url: str = 'https://v3.football.api-sports.io'
    tz: str = 'Europe/Madrid'


settings = Settings()
