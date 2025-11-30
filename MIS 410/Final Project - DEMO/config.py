import os
from dotenv import load_dotenv

basedir = os.path.abspath(os.path.dirname(__file__))
load_dotenv()


class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY", "dev-key-change-me")

    INSTANCE_DB_PATH = os.path.join(basedir, "instance", "csusm_event_hub.db")

    SQLALCHEMY_DATABASE_URI = os.environ.get("DATABASE_URL") or \
        f"sqlite:///{INSTANCE_DB_PATH}"

    SQLALCHEMY_TRACK_MODIFICATIONS = False
