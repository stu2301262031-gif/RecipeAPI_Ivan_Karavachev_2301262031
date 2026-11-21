from exceptions import NotFound, DuplicationError
from sqlalchemy.orm import Session
from sqlalchemy import select, func
from db.models import Recipe, RecipeIngredient
from services.author_service import AuthorService
from services.category_service import CategoryService

class RecipeService:
    def _get(self, id: int, db_session: Session) -> Recipe:
        recipe = db_session.get(Recipe, id)
        if recipe is None:
            raise NotFound(f"Recipe with id {id} not found")
        return recipe

    #an author can not have two recipes with the same title (case-insensitive)
    def _check_title(self, title: str, author_id: int, db_session: Session, id: int | None = None):
        stmt = select(Recipe).where(Recipe.author_id == author_id).where(
            func.lower(Recipe.title) == title.lower())
        if id is not None:
            stmt = stmt.where(Recipe.id != id)
        if db_session.scalars(stmt).first() is not None:
            raise DuplicationError(
                f"Author with id {author_id} already has a recipe with title {title}")

    #the filters are added to the query only when they are given,
    #several .where() calls are combined with AND
    def get_recipes(self, db_session: Session, title: str | None = None,
                    category_id: int | None = None, max_prep_time: int | None = None) -> list[Recipe]:
        stmt = select(Recipe)
        if title is not None and title.strip():
            stmt = stmt.where(
                func.lower(Recipe.title).contains(title.strip().lower(), autoescape=True))
        if category_id is not None:
            stmt = stmt.where(Recipe.category_id == category_id)
        if max_prep_time is not None:
            stmt = stmt.where(Recipe.prep_time_minutes <= max_prep_time)
        return db_session.scalars(stmt.order_by(Recipe.id)).all()

    def get_recipe(self, id: int, db_session: Session) -> Recipe:
        return self._get(id, db_session)

    def create_recipe(self, data: dict, db_session: Session,
                      author_service: AuthorService, category_service: CategoryService) -> Recipe:
        author = author_service.get_author(data["author_id"], db_session)
        category = None
        if data["category_id"] is not None:
            category = category_service.get_category(data["category_id"], db_session)
        self._check_title(data["title"], author.id, db_session)

        recipe = Recipe(title=data["title"], instructions=data["instructions"],
                        prep_time_minutes=data["prep_time_minutes"], servings=data["servings"],
                        author=author, category=category)
        db_session.add(recipe)
        db_session.commit()
        db_session.refresh(recipe)
        return recipe

    def update_recipe(self, id: int, data: dict, db_session: Session,
                      author_service: AuthorService, category_service: CategoryService) -> Recipe:
        recipe = self._get(id, db_session)
        author = author_service.get_author(data["author_id"], db_session)
        category = None
        if data["category_id"] is not None:
            category = category_service.get_category(data["category_id"], db_session)
        self._check_title(data["title"], author.id, db_session, id)

        recipe.title = data["title"]
        recipe.instructions = data["instructions"]
        recipe.prep_time_minutes = data["prep_time_minutes"]
        recipe.servings = data["servings"]
        recipe.author = author
        recipe.category = category
        db_session.commit()
        db_session.refresh(recipe)
        return recipe

    #the links between the recipe and its ingredients are deleted (ON DELETE CASCADE),
    #the ingredients themselves are not deleted
    def delete_recipe(self, id: int, db_session: Session):
        recipe = self._get(id, db_session)
        db_session.delete(recipe)
        db_session.commit()

    #returns the recipe with quantities recalculated for the requested number of servings.
    #the result is a new dictionary - the ORM objects are not changed,
    #so nothing is written to the database
    def get_scaled_recipe(self, id: int, servings: int, db_session: Session) -> dict:
        recipe = self._get(id, db_session)
        recipe_ingredients = db_session.scalars(
            select(RecipeIngredient)
            .where(RecipeIngredient.recipe_id == id)
            .order_by(RecipeIngredient.id)).all()

        factor = servings / recipe.servings
        return {
            "id": recipe.id,
            "title": recipe.title,
            "instructions": recipe.instructions,
            "prep_time_minutes": recipe.prep_time_minutes,
            "author_id": recipe.author_id,
            "category_id": recipe.category_id,
            "original_servings": recipe.servings,
            "servings": servings,
            "ingredients": [
                {
                    "ingredient": recipe_ingredient.ingredient,
                    "quantity": round(recipe_ingredient.quantity * factor, 2),
                    "unit": recipe_ingredient.unit,
                }
                for recipe_ingredient in recipe_ingredients
            ],
        }

def get_recipe_service() -> RecipeService:
    return RecipeService()
