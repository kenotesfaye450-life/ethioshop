import os
from pathlib import Path
from urllib.parse import quote_plus

from dotenv import load_dotenv

# Always load backend/.env (overrides broken system-level DATABASE_URL)
_BACKEND_ENV = Path(__file__).resolve().parent / '.env'
load_dotenv(_BACKEND_ENV, override=True)


def _build_database_uri() -> str:
    """
    Prefer DB_* parts so passwords with @ are URL-encoded correctly.
    A raw DATABASE_URL with 9Wisdomlife1@ breaks parsing (host becomes @aws-...).
    """
    db_host = os.getenv('DB_HOST', '').strip()
    if db_host:
        db_user = os.getenv('DB_USER', 'postgres')
        db_password = os.getenv('DB_PASSWORD', '')
        db_port = os.getenv('DB_PORT', '5432')
        db_name = os.getenv('DB_NAME', 'postgres')
        if db_password:
            pwd = quote_plus(db_password)
            return f"postgresql+psycopg2://{db_user}:{pwd}@{db_host}:{db_port}/{db_name}"
        return f"postgresql+psycopg2://{db_user}@{db_host}:{db_port}/{db_name}"

    return os.getenv('DATABASE_URL', 'sqlite:///ethioshop_dev.db')


class BaseConfig:
    FLASK_ENV = os.getenv('FLASK_ENV', 'development')
    DEBUG = FLASK_ENV != 'production'
    TESTING = False

    SECRET_KEY = os.getenv('SECRET_KEY', '')

    SQLALCHEMY_DATABASE_URI = _build_database_uri()
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {'pool_pre_ping': True}

    CLOUDINARY_CLOUD_NAME = os.getenv('CLOUDINARY_CLOUD_NAME', '')
    CLOUDINARY_API_KEY = os.getenv('CLOUDINARY_API_KEY', '')
    CLOUDINARY_API_SECRET = os.getenv('CLOUDINARY_API_SECRET', '')

    TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN', '')
    TELEGRAM_WEBHOOK_URL = os.getenv('TELEGRAM_WEBHOOK_URL', '')

    REDIS_URL = os.getenv('REDIS_URL', 'redis://localhost:6379/0') if FLASK_ENV != 'production' else os.getenv('REDIS_URL', '')

    JWT_SECRET_KEY = os.getenv('JWT_SECRET_KEY', '')
    JWT_ACCESS_TOKEN_EXPIRES = int(os.getenv('JWT_ACCESS_TOKEN_EXPIRES', '28800'))

    SESSION_TYPE = 'redis'
    SESSION_PERMANENT = False
    SESSION_USE_SIGNER = True
    SESSION_COOKIE_SECURE = True
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    REMEMBER_COOKIE_SECURE = True

    MAX_CONTENT_LENGTH = int(os.getenv('MAX_CONTENT_LENGTH', 10 * 1024 * 1024))
    UPLOAD_MAX_SIZE = int(os.getenv('UPLOAD_MAX_SIZE', 5 * 1024 * 1024))
    ALLOWED_IMAGE_EXTENSIONS = frozenset({'png', 'jpg', 'jpeg', 'webp', 'gif'})

    _cors_default = 'http://localhost:8080,http://localhost:5500,https://ethioshop.et'
    CORS_ORIGINS = [
        o.strip() for o in os.getenv('CORS_ORIGINS', _cors_default).split(',') if o.strip()
    ]
    PREFERRED_URL_SCHEME = 'https'
    JSON_SORT_KEYS = False

    # Business rules
    MINIMUM_ORDER_ETB = float(os.getenv('MINIMUM_ORDER_ETB', '500'))
    MAX_CREDIT_PERCENTAGE = float(os.getenv('MAX_CREDIT_PERCENTAGE', '0.5'))
    MAX_CREDIT_ETB = float(os.getenv('MAX_CREDIT_ETB', '500'))
    REFERRAL_REWARD_ETB = float(os.getenv('REFERRAL_REWARD_ETB', '50'))

    @classmethod
    def validate(cls):
        required = []
        if cls.FLASK_ENV == 'production':
            required = [
                'SECRET_KEY',
                'JWT_SECRET_KEY',
                'CLOUDINARY_CLOUD_NAME',
                'CLOUDINARY_API_KEY',
                'CLOUDINARY_API_SECRET',
                'REDIS_URL'
            ]

        missing = [var for var in required if not getattr(cls, var)]
        if cls.FLASK_ENV == 'production' and not cls.SQLALCHEMY_DATABASE_URI:
            missing.append('DATABASE_URL or DB_HOST')
        if missing:
            raise EnvironmentError(f"Missing required environment variables: {', '.join(missing)}")

class DevelopmentConfig(BaseConfig):
    DEBUG = True
    SESSION_COOKIE_SECURE = False
    REMEMBER_COOKIE_SECURE = False
    REDIS_URL = os.getenv('REDIS_URL', 'redis://localhost:6379/0')

class StagingConfig(BaseConfig):
    DEBUG = False

class ProductionConfig(BaseConfig):
    DEBUG = False
    TESTING = False

class ConfigFactory:
    @staticmethod
    def get():
        env = os.getenv('FLASK_ENV', 'development').lower()
        if env == 'production':
            return ProductionConfig
        if env == 'staging':
            return StagingConfig
        return DevelopmentConfig

Config = ConfigFactory.get()
