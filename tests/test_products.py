import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from main import app
from app.database import Base, get_db
from app.models import ProductModel, CategoryModel
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
        db.query(ProductModel).delete()
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


@pytest.fixture()
def product(client, category):
    product_data = {
        "name": "Test Product",
        "description": "This is a test product",
        "price": 10.99,
        "category_id": category
    }
    response = client.post("/products/", json=product_data)
    assert response.status_code == 200
    return response.json()["id"]


def test_create_product(client, category):
    product_data = {
        "name": "Test Product",
        "description": "This is a test product",
        "price": 10.99,
        "category_id": category
    }
    response = client.post("/products/", json=product_data)
    assert response.status_code == 200
    assert response.json()["name"] == "Test Product"
    assert response.json()["description"] == "This is a test product"
    assert response.json()["price"] == 10.99
    assert response.json()["category_id"] == category
    assert "id" in response.json()


def test_read_product(client, product):
    response = client.get(f"/products/{product}")
    assert response.status_code == 200
    assert response.json()["name"] == "Test Product"
    assert response.json()["description"] == "This is a test product"
    assert response.json()["price"] == 10.99
    assert "category_id" in response.json()
    assert response.json()["id"] == product


def test_read_product_not_found(client):
    response = client.get("/products/9999")
    assert response.status_code == 404
    assert response.json()["detail"] == "Product not found"


def test_update_product(client, product, category):
    updated_data = {
        "name": "Updated Product",
        "description": "This is an updated product",
        "price": 15.99,
        "category_id": category
    }
    response = client.put(f"/products/{product}", json=updated_data)
    assert response.status_code == 200
    assert response.json()["name"] == "Updated Product"
    assert response.json()["description"] == "This is an updated product"
    assert response.json()["price"] == 15.99
    assert response.json()["category_id"] == category
    assert response.json()["id"] == product


def test_update_product_not_found(client, category):
    updated_data = {
        "name": "Updated Product",
        "description": "This is an updated product",
        "price": 15.99,
        "category_id": category
    }
    response = client.put("/products/9999", json=updated_data)
    assert response.status_code == 404
    assert response.json()["detail"] == "Product not found"


def test_delete_product(client, product):
    response = client.delete(f"/products/{product}")
    assert response.status_code == 200
    assert response.json()["name"] == "Test Product"
    assert response.json()["description"] == "This is a test product"
    assert response.json()["price"] == 10.99
    assert "category_id" in response.json()
    assert response.json()["id"] == product


def test_delete_product_not_found(client):
    response = client.delete("/products/9999")
    assert response.status_code == 404
    assert response.json()["detail"] == "Product not found"


def test_filter_products(client, category):
    client.post("/products/", json={
        "name": "Product A",
        "description": "This is product A",
        "price": 5.99,
        "category_id": category
    })
    client.post("/products/", json={
        "name": "Product B",
        "description": "This is product B",
        "price": 15.99,
        "category_id": category
    })
    client.post("/products/", json={
        "name": "Product C",
        "description": "This is product C",
        "price": 25.99,
        "category_id": category
    })

    response = client.get("/products/?name=Product&price_min=10&price_max=20")
    assert response.status_code == 200
    products = response.json()
    assert len(products) == 1
    assert products[0]["name"] == "Product B"
    assert products[0]["description"] == "This is product B"
    assert products[0]["price"] == 15.99
    assert products[0]["category_id"] == category
