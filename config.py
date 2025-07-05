from dotenv import load_dotenv
import os

load_dotenv()

class Config:
    SECRET_KEY = os.getenv("SECRET_KEY")
    SQLALCHEMY_DATABASE_URI = (
        f"mysql+pymysql://{os.getenv('DB_USER')}:{os.getenv('DB_PASSWORD')}@{os.getenv('DB_HOST')}:{os.getenv('DB_PORT')}/{os.getenv('DB_NAME')}"
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # PayGlocal Configuration
    PAYGLOBAL_MERCHANT_ID = os.getenv('PAYGLOBAL_MERCHANT_ID')
    PAYGLOBAL_API_KEY = os.getenv('PAYGLOBAL_API_KEY')
    PAYGLOBAL_API_URL = os.getenv('PAYGLOBAL_API_URL', 'https://api.payglocal.com')
