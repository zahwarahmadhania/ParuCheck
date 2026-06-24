import os

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'parucheck-secret-key-12345'

    SQLALCHEMY_DATABASE_URI = (
        "mysql+pymysql://root:@localhost/parucheck_db"
    )

    SQLALCHEMY_TRACK_MODIFICATIONS = False