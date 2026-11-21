from exceptions import NotFound, DuplicationError
from sqlalchemy.orm import Session
from sqlalchemy import select
from db.models import RecipeIngredient
from services.recipe_service import RecipeService
from services.ingredient_service import IngredientService

#manages the many-to-many relationship between recipes and ingredients
class RecipeIngredientService:
    def _find(self, recipe_id: int, ingredient_id: int, db_session: Session) -> RecipeIngredient | None:
        return db_session.scalars(
            select(RecipeIngredient)
            .where(RecipeIngredient.recipe_id == recipe_id)
            .where(RecipeIngredient.ingredient_id == ingredient_id)).first()

    def _get(self, recipe_id: int, ingredient_id: int, db_session: Session) -> RecipeIngredient:
        recipe_ingredient = self._find(recipe_id, ingredient_id, db_session)
        if recipe_ingredient is None:
            raise NotFound(
                f"Ingredient with id {ingredient_id} is not part of recipe with id {recipe_id}")
        return recipe_ingredient

    #404 if the recipe does not exist, empty list if it has no ingredients
    def get_recipe_ingredients(self, recipe_id: int, db_session: Session,
                               recipe_service: RecipeService) -> list[RecipeIngredient]:
        recipe_service.get_recipe(recipe_id, db_session)
        return db_session.scalars(
            select(RecipeIngredient)
            .where(RecipeIngredient.recipe_id == recipe_id)
            .order_by(RecipeIngredient.id)).all()

    #an ingredient can be added only once to a recipe,
    #the second attempt returns 409 and does not change the existing quantity
    def add_ingredient(self, recipe_id: int, data: dict, db_session: Session,
                       recipe_service: RecipeService,
                       ingredient_service: IngredientService) -> RecipeIngredient:
        recipe = recipe_service.get_recipe(recipe_id, db_session)
        ingredient = ingredient_service.get_ingredient(data["ingredient_id"], db_session)
        if self._find(recipe.id, ingredient.id, db_session) is not None:
            raise DuplicationError(
                f"Ingredient with id {ingredient.id} is already added to recipe with id {recipe.id}")

        recipe_ingredient = RecipeIngredient(recipe=recipe, ingredient=ingredient,
                                             quantity=data["quantity"], unit=data["unit"])
        db_session.add(recipe_ingredient)
        db_session.commit()
        db_session.refresh(recipe_ingredient)
        return recipe_ingredient

    def update_ingredient(self, recipe_id: int, ingredient_id: int, data: dict,
                          db_session: Session, recipe_service: RecipeService) -> RecipeIngredient:
        recipe_service.get_recipe(recipe_id, db_session)
        recipe_ingredient = self._get(recipe_id, ingredient_id, db_session)
        recipe_ingredient.quantity = data["quantity"]
        recipe_ingredient.unit = data["unit"]
        db_session.commit()
        db_session.refresh(recipe_ingredient)
        return recipe_ingredient

    #only the link is deleted, the ingredient stays in the database
    def remove_ingredient(self, recipe_id: int, ingredient_id: int, db_session: Session,
                          recipe_service: RecipeService):
        recipe_service.get_recipe(recipe_id, db_session)
        recipe_ingredient = self._get(recipe_id, ingredient_id, db_session)
        db_session.delete(recipe_ingredient)
        db_session.commit()

def get_recipe_ingredient_service() -> RecipeIngredientService:
    return RecipeIngredientService()
