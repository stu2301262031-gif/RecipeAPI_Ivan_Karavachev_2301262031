from fastapi import APIRouter, Depends, status
from models.models import Category, CreateCategory, UpdateCategory
from sqlalchemy.orm import Session
from db.database import get_db
from services.category_service import CategoryService, get_category_service

router = APIRouter(prefix="/categories", tags=["Categories"])

@router.get("/")
def get_categories(db_session: Session = Depends(get_db),
                   category_service: CategoryService = Depends(get_category_service)) -> list[Category]:
    return category_service.get_categories(db_session)

@router.get("/{id}")
def get_category(id: int, db_session: Session = Depends(get_db),
                 category_service: CategoryService = Depends(get_category_service)) -> Category:
    return category_service.get_category(id, db_session)

@router.post("/", status_code=status.HTTP_201_CREATED)
def create_category(create_category: CreateCategory, db_session: Session = Depends(get_db),
                    category_service: CategoryService = Depends(get_category_service)) -> Category:
    return category_service.create_category(create_category.model_dump(), db_session)

@router.put("/{id}")
def update_category(id: int, update_category: UpdateCategory, db_session: Session = Depends(get_db),
                    category_service: CategoryService = Depends(get_category_service)) -> Category:
    return category_service.update_category(id, update_category.model_dump(), db_session)

@router.delete("/{id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_category(id: int, db_session: Session = Depends(get_db),
                    category_service: CategoryService = Depends(get_category_service)):
    category_service.delete_category(id, db_session)
