from fastapi import FastAPI
from app.routers import product_router, category_router

app = FastAPI()

app.include_router(product_router, prefix="/api")
app.include_router(category_router, prefix="/api")
