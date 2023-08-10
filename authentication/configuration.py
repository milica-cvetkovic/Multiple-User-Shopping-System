import os
from datetime import timedelta

# DATABASE_URL = "database" if ( "PRODUCTION" in os.environ ) else "localhost"

DATABASE_URL = os.environ["DATABASE_URL"];

class Configuration:
    SQLALCHEMY_DATABASE_URI = f"mysql+pymysql://root:root@{DATABASE_URL}/authentication";
    JWT_SECRET_KEY ="JWT_SECRET_KEY"
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(minutes=60);
    JWT_REFRESH_TOKEN_EXPIRES = timedelta(days=30);