import os
import tempfile

BASE_DIR = os.path.abspath(os.path.dirname(os.path.dirname(__file__)))

class Config:
    SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret-key-loveletter-poker")
    DATABASE_PATH = os.path.join(BASE_DIR, "poker.db")
    DEBUG = False
    TESTING = False
    SEED_SAMPLE_DATA = False

class DevelopmentConfig(Config):
    DEBUG = True
    SEED_SAMPLE_DATA = True

class TestingConfig(Config):
    TESTING = True
    DATABASE_PATH = os.path.join(tempfile.gettempdir(), "test_poker.db")

config_by_name = {
    "development": DevelopmentConfig,
    "testing": TestingConfig,
    "default": DevelopmentConfig
}
