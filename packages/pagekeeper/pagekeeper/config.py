from datetime import timedelta

from environs import Env


class AppConfig:
    def __init__(self: 'AppConfig', db_name: str | None = None) -> None:
        self.env = Env()
        self.env.read_env('.env')

        self.ACCESS_TOKEN_EXPIRATION = timedelta(hours=24)
        self.SECRET_KEY = self.env.str('PAGEKEEPER_SECRET_KEY')
        self.MONGODB_URL = self.env.str('PAGEKEEPER_MONGODB_URL')
        self.PORT = self.env.int('PAGEKEEPER_PORT', default=454545)
        self.DATABASE_NAME = self.env.str('PAGEKEEPER_DATABASE_NAME') if db_name is None else db_name
