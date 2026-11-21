import os
from sqlalchemy import create_engine, event, MetaData
from sqlalchemy.orm import DeclarativeBase, sessionmaker

#we try to get the database url from the environment variables first
#if there is no env var we use the default recipes.sqlite
DATABASE_URL = os.getenv("DATABASE_URL") or "sqlite:///recipes.sqlite"

engine = create_engine(url=DATABASE_URL, echo=False)

#SQLite does not enforce foreign keys (ON DELETE CASCADE / SET NULL / RESTRICT) by default.
#The PRAGMA must be enabled for every new connection.
#SQLite's built-in lower() works only for ASCII letters, so we replace it with
#Python's str.lower() to get case-insensitive comparisons for Cyrillic text too.
@event.listens_for(engine, "connect")
def configure_sqlite_connection(dbapi_connection, connection_record):
    if engine.dialect.name == "sqlite":
        dbapi_connection.create_function(
            "lower", 1, lambda value: value.lower() if isinstance(value, str) else value,
            deterministic=True)
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

SessionLocal = sessionmaker(bind=engine)

#naming convention gives every constraint a predictable name,
#which Alembic needs to be able to alter constraints later
naming_convention = {
    "ix": "ix_%(column_0_label)s",
    "uq": "uq_%(table_name)s_%(column_0_N_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s",
}

class Base(DeclarativeBase):
    metadata = MetaData(naming_convention=naming_convention)

#get_db is a generator to create new ORM session used in the context of new request
#it works as a Dependency injection into the endpoints
def get_db():
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()
