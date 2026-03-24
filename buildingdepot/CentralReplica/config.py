import os


class Config:
    MONGODB_DATABASE = "buildingdepot"
    MONGODB_HOST = os.environ.get("MONGODB_HOST", "127.0.0.1")
    MONGODB_PORT = int(os.environ.get("MONGODB_PORT", 27017))
    MONGODB_USERNAME = os.environ.get("MONGODB_USERNAME", "")
    MONGODB_PWD = os.environ.get("MONGODB_PWD", "")
    SECRET_KEY = os.environ.get("SECRET_KEY", "This Is Secret Key. Please Make It Complicated")
    TOKEN_EXPIRATION = 3600
    REDIS_HOST = os.environ.get("REDIS_HOST", "localhost")
    REDIS_PWD = os.environ.get("REDIS_PWD", "")
