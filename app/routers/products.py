from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from app.models import ProductModel
from app.schemas import ProductCreate, Product
from app.database import get_db

router = APIRouter(
    prefix="/products",
    tags=["products"],
    responses={404: {"description": "Not found"}},
)


@router.post("/", response_model=Product)
def create_product(product: ProductCreate, db: Session = Depends(get_db)):
    db_product = ProductModel(**product.dict())
    db.add(db_product)
    db.commit()
    db.refresh(db_product)
    return db_product


@router.get("/{product_id}", response_model=Product)
def read_product(product_id: int, db: Session = Depends(get_db)):
    db_product = db.query(ProductModel).filter(ProductModel.id == product_id).first()
    if db_product is None:
        raise HTTPException(status_code=404, detail="Product not found")
    return db_product


@router.put("/{product_id}", response_model=Product)
def update_product(product_id: int, product: ProductCreate, db: Session = Depends(get_db)):
    db_product = db.query(ProductModel).filter(ProductModel.id == product_id).first()
    if db_product is None:
        raise HTTPException(status_code=404, detail="Product not found")
    for key, value in product.dict().items():
        setattr(db_product, key, value)
    db.commit()
    db.refresh(db_product)
    return db_product


@router.delete("/{product_id}", response_model=Product)
def delete_product(product_id: int, db: Session = Depends(get_db)):
    db_product = db.query(ProductModel).filter(ProductModel.id == product_id).first()
    if db_product is None:
        raise HTTPException(status_code=404, detail="Product not found")
    db.delete(db_product)
    db.commit()
    return db_product


@router.get("/", response_model=list[Product])
def filter_products(
    name: str = Query(None, description="Filter by product name"),
    price_min: float = Query(None, description="Filter by minimum price"),
    price_max: float = Query(None, description="Filter by maximum price"),
    db: Session = Depends(get_db)
):
    query = db.query(ProductModel)

    if name:
        query = query.filter(ProductModel.name.ilike(f"%{name}%"))

    if price_min is not None:
        query = query.filter(ProductModel.price >= price_min)

    if price_max is not None:
        query = query.filter(ProductModel.price <= price_max)

    products = query.all()
    return products
