from exceptions import NotFound, DuplicationError, ConflictError
from sqlalchemy.orm import Session
from sqlalchemy import select, func
from db.models import Ingredient, RecipeIngredient

class IngredientService:
    def _get(self, id: int, db_session: Session) -> Ingredient:
        ingredient = db_session.get(Ingredient, id)
        if ingredient is None:
            raise NotFound(f"Ingredient with id {id} not found")
        return ingredient

    def _check_name(self, name: str, db_session: Session, id: int | None = None):
        stmt = select(Ingredient).where(func.lower(Ingredient.name) == name.lower())
        if id is not None:
            stmt = stmt.where(Ingredient.id != id)
        if db_session.scalars(stmt).first() is not None:
            raise DuplicationError(f"Ingredient with name {name} already exists")

    def get_ingredients(self, db_session: Session) -> list[Ingredient]:
        return db_session.scalars(select(Ingredient).order_by(Ingredient.id)).all()

    def get_ingredient(self, id: int, db_session: Session) -> Ingredient:
        return self._get(id, db_session)

    def create_ingredient(self, data: dict, db_session: Session) -> Ingredient:
        self._check_name(data["name"], db_session)
        ingredient = Ingredient(name=data["name"])
        db_session.add(ingredient)
        db_session.commit()
        db_session.refresh(ingredient)
        return ingredient

    def update_ingredient(self, id: int, data: dict, db_session: Session) -> Ingredient:
        ingredient = self._get(id, db_session)
        self._check_name(data["name"], db_session, id)
        ingredient.name = data["name"]
        db_session.commit()
        db_session.refresh(ingredient)
        return ingredient

    #an ingredient used in a recipe can not be deleted (ON DELETE RESTRICT)
    def delete_ingredient(self, id: int, db_session: Session):
        ingredient = self._get(id, db_session)
        recipes_count = db_session.scalar(
            select(func.count()).select_from(RecipeIngredient)
            .where(RecipeIngredient.ingredient_id == id))
        if recipes_count > 0:
            raise ConflictError(
                f"Ingredient with id {id} is used in {recipes_count} recipe(s) and can not be deleted")
        db_session.delete(ingredient)
        db_session.commit()

def get_ingredient_service() -> IngredientService:
    return IngredientService()
