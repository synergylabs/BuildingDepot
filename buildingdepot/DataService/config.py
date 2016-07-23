"""
DataService.config
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Contains the configuration definitions needed for the Dataservice.
This sample config file for example requires that a DataService be
registered in the CentralService with the name "ds1".

@copyright: (c) 2016 SynergyLabs
@license: UCSD License. See License file for details.
"""

class Config:
    MONGODB_DATABASE_DS = 'dataservice'
    MONGODB_DATABASE_BD = 'buildingdepot'
    MONGODB_HOST = '127.0.0.1'
    MONGODB_PORT = 27017

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
