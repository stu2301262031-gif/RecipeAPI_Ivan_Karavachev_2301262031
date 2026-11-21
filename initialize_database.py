#fills the database with sample data, so the API can be tried directly in Swagger (/docs)
#the tables must already exist - run "alembic upgrade head" first
from sqlalchemy import select
from db.database import SessionLocal
from db.models import Author, Category, Ingredient, Recipe, RecipeIngredient
from enums import Unit, Difficulty

def initialize_database():
    session = SessionLocal()
    try:
        if session.scalars(select(Author)).first() is not None:
            print("The database already contains data - nothing was added")
            return

        ivan = Author(name="Ivan Petrov", email="ivan.petrov@example.com")
        maria = Author(name="Maria Georgieva", email="maria.georgieva@example.com")
        session.add_all([ivan, maria])

        soups = Category(name="Супи")
        pastry = Category(name="Тестени")
        desserts = Category(name="Десерти")
        session.add_all([soups, pastry, desserts])

        names = ["Кисело мляко", "Краставица", "Чесън", "Орехи", "Олио", "Брашно",
                 "Яйца", "Прясно мляко", "Захар", "Сирене", "Кори за баница", "Домати"]
        ingredients = {name: Ingredient(name=name) for name in names}
        session.add_all(ingredients.values())

        tarator = Recipe(title="Таратор", instructions="Нарежете краставицата, добавете киселото мляко, "
                         "водата, чесъна и орехите. Овкусете и сервирайте студен.",
                         prep_time_minutes=15, servings=4, difficulty=Difficulty.easy,
                         author=ivan, category=soups)
        tarator.ingredient_links = [
            RecipeIngredient(ingredient=ingredients["Кисело мляко"], quantity=800, unit=Unit.g),
            RecipeIngredient(ingredient=ingredients["Краставица"], quantity=1, unit=Unit.pcs),
            RecipeIngredient(ingredient=ingredients["Чесън"], quantity=10, unit=Unit.g),
            RecipeIngredient(ingredient=ingredients["Орехи"], quantity=50, unit=Unit.g),
            RecipeIngredient(ingredient=ingredients["Олио"], quantity=30, unit=Unit.ml),
        ]

        banitsa = Recipe(title="Баница", instructions="Разбийте яйцата с киселото мляко и сиренето. "
                         "Редете корите с плънката и печете 40 минути на 200 градуса.",
                         prep_time_minutes=60, servings=6, difficulty=Difficulty.medium,
                         author=maria, category=pastry)
        banitsa.ingredient_links = [
            RecipeIngredient(ingredient=ingredients["Кори за баница"], quantity=400, unit=Unit.g),
            RecipeIngredient(ingredient=ingredients["Сирене"], quantity=300, unit=Unit.g),
            RecipeIngredient(ingredient=ingredients["Яйца"], quantity=4, unit=Unit.pcs),
            RecipeIngredient(ingredient=ingredients["Кисело мляко"], quantity=400, unit=Unit.g),
            RecipeIngredient(ingredient=ingredients["Олио"], quantity=100, unit=Unit.ml),
        ]

        pancakes = Recipe(title="Палачинки", instructions="Смесете брашното, яйцата, млякото и захарта. "
                          "Изпържете в тиган с малко олио.",
                          prep_time_minutes=30, servings=4, difficulty=Difficulty.easy,
                          author=ivan, category=desserts)
        pancakes.ingredient_links = [
            RecipeIngredient(ingredient=ingredients["Брашно"], quantity=250, unit=Unit.g),
            RecipeIngredient(ingredient=ingredients["Яйца"], quantity=3, unit=Unit.pcs),
            RecipeIngredient(ingredient=ingredients["Прясно мляко"], quantity=500, unit=Unit.ml),
            RecipeIngredient(ingredient=ingredients["Захар"], quantity=20, unit=Unit.g),
        ]

        #recipe without category
        salad = Recipe(title="Шопска салата", instructions="Нарежете доматите и краставицата, "
                       "посолете и настържете сирене отгоре.",
                       prep_time_minutes=10, servings=2, difficulty=Difficulty.easy,
                       author=maria, category=None)
        salad.ingredient_links = [
            RecipeIngredient(ingredient=ingredients["Домати"], quantity=3, unit=Unit.pcs),
            RecipeIngredient(ingredient=ingredients["Краставица"], quantity=1, unit=Unit.pcs),
            RecipeIngredient(ingredient=ingredients["Сирене"], quantity=150, unit=Unit.g),
        ]

        session.add_all([tarator, banitsa, pancakes, salad])
        session.commit()
        print("Sample data added: 2 authors, 3 categories, 12 ingredients, 4 recipes")
    finally:
        session.close()

if __name__ == "__main__":
    initialize_database()
