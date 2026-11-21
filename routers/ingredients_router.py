from fastapi import APIRouter, Depends, status
from models.models import Ingredient, CreateIngredient, UpdateIngredient
from sqlalchemy.orm import Session
from db.database import get_db
from services.ingredient_service import IngredientService, get_ingredient_service

router = APIRouter(prefix="/ingredients", tags=["Ingredients"])

@router.get("/")
def get_ingredients(db_session: Session = Depends(get_db),
                    ingredient_service: IngredientService = Depends(get_ingredient_service)) -> list[Ingredient]:
    return ingredient_service.get_ingredients(db_session)

@router.get("/{id}")
def get_ingredient(id: int, db_session: Session = Depends(get_db),
                   ingredient_service: IngredientService = Depends(get_ingredient_service)) -> Ingredient:
    return ingredient_service.get_ingredient(id, db_session)

@router.post("/", status_code=status.HTTP_201_CREATED)
def create_ingredient(create_ingredient: CreateIngredient, db_session: Session = Depends(get_db),
                      ingredient_service: IngredientService = Depends(get_ingredient_service)) -> Ingredient:
    return ingredient_service.create_ingredient(create_ingredient.model_dump(), db_session)

@router.put("/{id}")
def update_ingredient(id: int, update_ingredient: UpdateIngredient, db_session: Session = Depends(get_db),
                      ingredient_service: IngredientService = Depends(get_ingredient_service)) -> Ingredient:
    return ingredient_service.update_ingredient(id, update_ingredient.model_dump(), db_session)

@router.delete("/{id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_ingredient(id: int, db_session: Session = Depends(get_db),
                      ingredient_service: IngredientService = Depends(get_ingredient_service)):
    ingredient_service.delete_ingredient(id, db_session)
