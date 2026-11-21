from fastapi import APIRouter, Depends, Query, status
from models.models import (Recipe, CreateRecipe, UpdateRecipe, ScaledRecipe,
                           RecipeIngredient, AddRecipeIngredient, UpdateRecipeIngredient)
from sqlalchemy.orm import Session
from db.database import get_db
from config import MAX_SERVINGS
from services.author_service import AuthorService, get_author_service
from services.category_service import CategoryService, get_category_service
from services.ingredient_service import IngredientService, get_ingredient_service
from services.recipe_service import RecipeService, get_recipe_service
from services.recipe_ingredient_service import RecipeIngredientService, get_recipe_ingredient_service

router = APIRouter(prefix="/recipes", tags=["Recipes"])

#all query parameters are optional, when several are given they are combined with AND
@router.get("/")
def get_recipes(title: str | None = Query(default=None, description="Part of the title (case-insensitive)"),
                category_id: int | None = Query(default=None, description="Id of the category"),
                max_prep_time: int | None = Query(default=None, gt=0,
                                                  description="Maximum preparation time in minutes (inclusive)"),
                db_session: Session = Depends(get_db),
                recipe_service: RecipeService = Depends(get_recipe_service)) -> list[Recipe]:
    return recipe_service.get_recipes(db_session, title, category_id, max_prep_time)

@router.get("/{id}")
def get_recipe(id: int, db_session: Session = Depends(get_db),
               recipe_service: RecipeService = Depends(get_recipe_service)) -> Recipe:
    return recipe_service.get_recipe(id, db_session)

#recipe with recalculated quantities for the wanted number of servings,
#the data in the database is not changed
@router.get("/{id}/scaled")
def get_scaled_recipe(id: int,
                      servings: int = Query(gt=0, le=MAX_SERVINGS,
                                            description=f"Wanted number of servings (1 - {MAX_SERVINGS})"),
                      db_session: Session = Depends(get_db),
                      recipe_service: RecipeService = Depends(get_recipe_service)) -> ScaledRecipe:
    return recipe_service.get_scaled_recipe(id, servings, db_session)

@router.post("/", status_code=status.HTTP_201_CREATED)
def create_recipe(create_recipe: CreateRecipe, db_session: Session = Depends(get_db),
                  recipe_service: RecipeService = Depends(get_recipe_service),
                  author_service: AuthorService = Depends(get_author_service),
                  category_service: CategoryService = Depends(get_category_service)) -> Recipe:
    return recipe_service.create_recipe(create_recipe.model_dump(), db_session,
                                        author_service, category_service)

@router.put("/{id}")
def update_recipe(id: int, update_recipe: UpdateRecipe, db_session: Session = Depends(get_db),
                  recipe_service: RecipeService = Depends(get_recipe_service),
                  author_service: AuthorService = Depends(get_author_service),
                  category_service: CategoryService = Depends(get_category_service)) -> Recipe:
    return recipe_service.update_recipe(id, update_recipe.model_dump(), db_session,
                                        author_service, category_service)

@router.delete("/{id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_recipe(id: int, db_session: Session = Depends(get_db),
                  recipe_service: RecipeService = Depends(get_recipe_service)):
    recipe_service.delete_recipe(id, db_session)

#----------------------------------- Ingredients of a recipe -----------------------------------

@router.get("/{id}/ingredients")
def get_recipe_ingredients(id: int, db_session: Session = Depends(get_db),
                           recipe_service: RecipeService = Depends(get_recipe_service),
                           recipe_ingredient_service: RecipeIngredientService = Depends(get_recipe_ingredient_service)
                           ) -> list[RecipeIngredient]:
    return recipe_ingredient_service.get_recipe_ingredients(id, db_session, recipe_service)

@router.post("/{id}/ingredients", status_code=status.HTTP_201_CREATED)
def add_recipe_ingredient(id: int, add_ingredient: AddRecipeIngredient, db_session: Session = Depends(get_db),
                          recipe_service: RecipeService = Depends(get_recipe_service),
                          ingredient_service: IngredientService = Depends(get_ingredient_service),
                          recipe_ingredient_service: RecipeIngredientService = Depends(get_recipe_ingredient_service)
                          ) -> RecipeIngredient:
    return recipe_ingredient_service.add_ingredient(id, add_ingredient.model_dump(), db_session,
                                                    recipe_service, ingredient_service)

@router.put("/{id}/ingredients/{ingredient_id}")
def update_recipe_ingredient(id: int, ingredient_id: int, update_ingredient: UpdateRecipeIngredient,
                             db_session: Session = Depends(get_db),
                             recipe_service: RecipeService = Depends(get_recipe_service),
                             recipe_ingredient_service: RecipeIngredientService = Depends(get_recipe_ingredient_service)
                             ) -> RecipeIngredient:
    return recipe_ingredient_service.update_ingredient(id, ingredient_id, update_ingredient.model_dump(),
                                                       db_session, recipe_service)

@router.delete("/{id}/ingredients/{ingredient_id}", status_code=status.HTTP_204_NO_CONTENT)
def remove_recipe_ingredient(id: int, ingredient_id: int, db_session: Session = Depends(get_db),
                             recipe_service: RecipeService = Depends(get_recipe_service),
                             recipe_ingredient_service: RecipeIngredientService = Depends(get_recipe_ingredient_service)):
    recipe_ingredient_service.remove_ingredient(id, ingredient_id, db_session, recipe_service)
