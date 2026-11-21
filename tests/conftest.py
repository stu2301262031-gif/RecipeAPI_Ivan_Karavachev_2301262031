import os
from pathlib import Path

#the tests use their own SQLite file, the environment variable must be set
#before the application (db/database.py) is imported
ROOT = Path(__file__).resolve().parent.parent
TEST_DATABASE = ROOT / "test_recipes.sqlite"
os.environ["DATABASE_URL"] = f"sqlite:///{TEST_DATABASE.as_posix()}"

import pytest
from alembic import command
from alembic.config import Config
from fastapi.testclient import TestClient
from sqlalchemy import delete
from db.database import engine, SessionLocal
from db.models import Author, Category, Ingredient, Recipe, RecipeIngredient
from main import app

@pytest.fixture(scope="session", autouse=True)
def database():
    if TEST_DATABASE.exists():
        TEST_DATABASE.unlink()
    #the schema is created with the Alembic migrations, the same way as the real database
    command.upgrade(Config(str(ROOT / "alembic.ini")), "head")
    yield
    engine.dispose()
    TEST_DATABASE.unlink()

#every test starts with empty tables
@pytest.fixture(autouse=True)
def clean_tables():
    yield
    with SessionLocal() as session:
        for model in (RecipeIngredient, Recipe, Ingredient, Category, Author):
            session.execute(delete(model))
        session.commit()

@pytest.fixture
def client():
    return TestClient(app)
