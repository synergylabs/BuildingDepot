class Config:
    MONGODB_DATABASE = 'BuildingDepot'
    MONGODB_HOST = '127.0.0.1'
    MONGODB_PORT = 27017

    SECRET_KEY = 'This Is Secret Key. Please Make It Complicated'
    TOKEN_EXPIRATION = 3600

    @staticmethod
    def init_app(self):
        pass


class DevModeConfig(Config):
    DEBUG = True

config = {
    'dev': DevModeConfig
}
