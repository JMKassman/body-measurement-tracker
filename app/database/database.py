from sqlmodel import SQLModel, create_engine, Session
import os
from sqlalchemy.engine.url import URL

url = URL.create(
    os.environ["DB_TYPE"],
    os.environ["DB_USER"],
    os.environ["DB_PASSWORD"],
    os.environ["DB_HOST"],
    os.environ["DB_PORT"],
    os.environ["DB_DATABASE"],
)

engine = create_engine(url)


def create_db_and_tables():
    SQLModel.metadata.create_all(engine)


def get_session():
    with Session(engine) as session:
        yield session
