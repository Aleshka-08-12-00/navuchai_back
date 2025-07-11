import os
from dotenv import load_dotenv
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    raise ValueError("DATABASE_URL не задан в .env файле!")

engine = create_async_engine(DATABASE_URL, echo=True)
SessionLocal = sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)

SECRET_KEY = os.getenv("SECRET_KEY", "superpupersecretkey227")
ALGORITHM = os.getenv("ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", 300))
REFRESH_TOKEN_EXPIRE_DAYS = int(os.getenv("REFRESH_TOKEN_EXPIRE_DAYS", 30))

# MinIO settings
MINIO_URL = os.getenv("MINIO_URL")
MINIO_URL_SERT = os.getenv("MINIO_URL_SERT")
MINIO_ACCESS_KEY = os.getenv("MINIO_ACCESS_KEY")
MINIO_SECRET_KEY = os.getenv("MINIO_SECRET_KEY")
MINIO_BUCKET_NAME = os.getenv("MINIO_BUCKET_NAME", "navuchai")
MINIO_REGION = os.getenv("MINIO_REGION", "us-east-1")

if not all([MINIO_URL, MINIO_ACCESS_KEY, MINIO_SECRET_KEY]):
    raise ValueError("Не все настройки MinIO заданы в .env файле!")

# Email settings
MAIL_USERNAME = os.getenv("MAIL_USERNAME")
MAIL_PASSWORD = os.getenv("MAIL_PASSWORD")
MAIL_FROM = os.getenv("MAIL_FROM")
MAIL_PORT = int(os.getenv("MAIL_PORT", 587))
MAIL_SERVER = os.getenv("MAIL_SERVER", "smtp.gmail.com")
MAIL_TLS = os.getenv("MAIL_TLS", "True").lower() == "true"
MAIL_SSL = os.getenv("MAIL_SSL", "False").lower() == "true"
MAIL_STARTTLS = os.getenv("MAIL_STARTTLS", "True").lower() == "true"
MAIL_SSL_TLS = os.getenv("MAIL_SSL_TLS", "False").lower() == "true"

# Email configuration for password reset
EMAIL_CONFIG = {
    "MAIL_USERNAME": MAIL_USERNAME,
    "MAIL_PASSWORD": MAIL_PASSWORD,
    "MAIL_FROM": MAIL_FROM,
    "MAIL_PORT": MAIL_PORT,
    "MAIL_SERVER": MAIL_SERVER,
    "MAIL_STARTTLS": MAIL_STARTTLS,
    "MAIL_SSL_TLS": MAIL_SSL_TLS,
    "USE_CREDENTIALS": True,
    "VALIDATE_CERTS": True
}
