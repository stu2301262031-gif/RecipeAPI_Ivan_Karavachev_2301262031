from enum import Enum
from db.database import Base
from sqlalchemy import ForeignKey, String, Text, CheckConstraint, UniqueConstraint
from sqlalchemy import Enum as SqlEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship

class Unit(str, Enum):
    g = "g"
    ml = "ml"
    pcs = "pcs"

class Author(Base):
    __tablename__ = "author"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100))
    email: Mapped[str] = mapped_column(String(255), unique=True)

    #passive_deletes="all" - the ORM never sets author_id of the recipes to NULL,
    #the database foreign key (ON DELETE RESTRICT) protects an author who has recipes
    recipes: Mapped[list["Recipe"]] = relationship(back_populates="author", passive_deletes="all")

class Category(Base):
    __tablename__ = "category"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100), unique=True)

    #when a category is deleted the database sets category_id of its recipes to NULL (ON DELETE SET NULL)
    recipes: Mapped[list["Recipe"]] = relationship(back_populates="category", passive_deletes=True)

class Ingredient(Base):
    __tablename__ = "ingredient"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100), unique=True)

    #ON DELETE RESTRICT - an ingredient used in a recipe can not be deleted
    recipe_links: Mapped[list["RecipeIngredient"]] = relationship(
        back_populates="ingredient", passive_deletes="all")

class Recipe(Base):
    __tablename__ = "recipe"
    __table_args__ = (
        UniqueConstraint("author_id", "title"),
        CheckConstraint("prep_time_minutes > 0", name="prep_time_positive"),
        CheckConstraint("servings > 0", name="servings_positive"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(String(200))
    instructions: Mapped[str] = mapped_column(Text)
    prep_time_minutes: Mapped[int]
    servings: Mapped[int]
    author_id: Mapped[int] = mapped_column(ForeignKey("author.id", ondelete="RESTRICT"))
    category_id: Mapped[int | None] = mapped_column(ForeignKey("category.id", ondelete="SET NULL"))

    author: Mapped["Author"] = relationship(back_populates="recipes")
    category: Mapped["Category | None"] = relationship(back_populates="recipes")

    #deleting a recipe deletes only its links to the ingredients (ON DELETE CASCADE),
    #the ingredients themselves stay in the database
    ingredient_links: Mapped[list["RecipeIngredient"]] = relationship(
        back_populates="recipe", cascade="all, delete-orphan", passive_deletes=True)

#association model for the many-to-many relationship between Recipe and Ingredient
#with additional fields quantity and unit
class RecipeIngredient(Base):
    __tablename__ = "recipe_ingredient"
    __table_args__ = (
        #an ingredient can be added only once to a recipe
        UniqueConstraint("recipe_id", "ingredient_id"),
        CheckConstraint("quantity > 0", name="quantity_positive"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    recipe_id: Mapped[int] = mapped_column(ForeignKey("recipe.id", ondelete="CASCADE"))
    ingredient_id: Mapped[int] = mapped_column(ForeignKey("ingredient.id", ondelete="RESTRICT"))
    quantity: Mapped[float]
    unit: Mapped[Unit] = mapped_column(SqlEnum(Unit, name="unit", create_constraint=True))

    recipe: Mapped["Recipe"] = relationship(back_populates="ingredient_links")
    ingredient: Mapped["Ingredient"] = relationship(back_populates="recipe_links")
