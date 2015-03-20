class Config:
    MONGODB_DATABASE = 'dataservice'
    MONGODB_HOST = '127.0.0.1'
    MONGODB_PORT = 27020

    SECRET_KEY = 'This Is Secret Key. Please Make It Complicated'
    TOKEN_EXPIRATION = 3600

    NAME = 'ds1'

    @staticmethod
    def init_app(self):
        pass


class DevModeConfig(Config):
    DEBUG = True

config = {
    'dev': DevModeConfig
}
