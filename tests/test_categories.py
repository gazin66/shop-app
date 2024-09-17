import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from main import app
from app.database import Base, get_db
from app.models import CategoryModel
import psycopg2

DATABASE_URL = "postgresql://postgres:admin@127.0.0.1:5432/test_db"
BASE_URL = "http://127.0.0.1:8000/api"

engine = create_engine(DATABASE_URL)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def create_test_database():
    conn = psycopg2.connect(dbname="postgres", user="postgres", password="admin", host="127.0.0.1")
    conn.autocommit = True
    cursor = conn.cursor()
    cursor.execute("DROP DATABASE IF EXISTS test_db")
    cursor.execute("CREATE DATABASE test_db")
    cursor.close()
    conn.close()


def drop_test_database():
    conn = psycopg2.connect(dbname="postgres", user="postgres", password="admin", host="127.0.0.1")
    conn.autocommit = True
    cursor = conn.cursor()

    cursor.execute(f"""
            SELECT pg_terminate_backend(pg_stat_activity.pid)
            FROM pg_stat_activity
            WHERE pg_stat_activity.datname = 'test_db'
              AND pid <> pg_backend_pid();
        """)

    cursor.execute("DROP DATABASE IF EXISTS test_db")
    cursor.close()
    conn.close()


@pytest.fixture(scope="module")
def test_db():
    create_test_database()
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)
    drop_test_database()


@pytest.fixture()
def clear_db(test_db):
    db = TestingSessionLocal()
    try:
        db.query(CategoryModel).delete()
        db.commit()
    finally:
        db.close()


@pytest.fixture()
def client(test_db, clear_db):
    def override_get_db():
        db = TestingSessionLocal()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db

    with TestClient(app, base_url=BASE_URL) as client:
        yield client


@pytest.fixture()
def category(client):
    category_data = {"name": "Test Category"}
    response = client.post("/categories/", json=category_data)
    assert response.status_code == 200
    return response.json()["id"]


def test_create_category(client):
    category_data = {"name": "Test Category"}
    response = client.post("/categories/", json=category_data)
    assert response.status_code == 200
    assert response.json()["name"] == "Test Category"
    assert "id" in response.json()


def test_read_category(client, category):
    response = client.get(f"/categories/{category}")
    assert response.status_code == 200
    assert response.json()["name"] == "Test Category"
    assert response.json()["id"] == category


def test_read_category_not_found(client):
    response = client.get("/categories/9999")
    assert response.status_code == 404
    assert response.json()["detail"] == "Category not found"


def test_update_category(client, category):
    updated_data = {"name": "Updated Category"}
    response = client.put(f"/categories/{category}", json=updated_data)
    assert response.status_code == 200
    assert response.json()["name"] == "Updated Category"
    assert response.json()["id"] == category


def test_update_category_not_found(client):
    updated_data = {"name": "Updated Category"}
    response = client.put("/categories/9999", json=updated_data)
    assert response.status_code == 404
    assert response.json()["detail"] == "Category not found"

def test_get_all_categories(client):
    category_data_1 = {"name": "Category 1"}
    category_data_2 = {"name": "Category 2"}
    client.post("/categories/", json=category_data_1)
    client.post("/categories/", json=category_data_2)

    response = client.get("/categories/")
    assert response.status_code == 200
    assert len(response.json()) == 2
    assert response.json()[0]["name"] == "Category 1"
    assert response.json()[1]["name"] == "Category 2"