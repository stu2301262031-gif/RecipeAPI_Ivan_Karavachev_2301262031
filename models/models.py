from pydantic import BaseModel, Field, ConfigDict, EmailStr, field_validator
from enums import Unit

#required text fields can not be empty or contain only spaces.
#the spaces at the beginning and at the end are removed before the value is stored
def validate_not_blank(value: str) -> str:
    value = value.strip()
    if not value:
        raise ValueError("The field can not be empty or contain only spaces")
    return value

#----------------------------------- Author -----------------------------------

class Author(BaseModel):
    #Setting model_config to ConfigDict(from_attributes=True) tells pydantic to read
    #the values from the attributes of the ORM object instead of expecting dictionary
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    email: str

class CreateAuthor(BaseModel):
    name: str = Field(max_length=100)
    email: EmailStr

    @field_validator("name")
    @classmethod
    def validate_name(cls, name):
        return validate_not_blank(name)

    #emails are compared and stored in lower case
    @field_validator("email")
    @classmethod
    def validate_email(cls, email):
        return email.lower()

class UpdateAuthor(CreateAuthor):
    pass

#----------------------------------- Category -----------------------------------

class Category(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str

class CreateCategory(BaseModel):
    name: str = Field(max_length=100)

    @field_validator("name")
    @classmethod
    def validate_name(cls, name):
        return validate_not_blank(name)

class UpdateCategory(CreateCategory):
    pass

#----------------------------------- Ingredient -----------------------------------

class Ingredient(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str

class CreateIngredient(BaseModel):
    name: str = Field(max_length=100)

    @field_validator("name")
    @classmethod
    def validate_name(cls, name):
        return validate_not_blank(name)

class UpdateIngredient(CreateIngredient):
    pass

#----------------------------------- Recipe -----------------------------------

class Recipe(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    instructions: str
    prep_time_minutes: int
    servings: int
    author_id: int
    category_id: int | None

class CreateRecipe(BaseModel):
    title: str = Field(max_length=200)
    instructions: str
    #strict=True - only whole numbers are accepted (not "30", 30.5 or true)
    prep_time_minutes: int = Field(gt=0, strict=True)
    servings: int = Field(gt=0, strict=True)
    author_id: int
    category_id: int | None = None

    @field_validator("title", "instructions")
    @classmethod
    def validate_text(cls, value):
        return validate_not_blank(value)

class UpdateRecipe(CreateRecipe):
    pass

#----------------------------------- Recipe ingredients -----------------------------------

#an ingredient of a recipe together with its quantity and unit
class RecipeIngredient(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    ingredient: Ingredient
    quantity: float
    unit: Unit

class AddRecipeIngredient(BaseModel):
    ingredient_id: int
    quantity: float = Field(gt=0, allow_inf_nan=False)
    unit: Unit

class UpdateRecipeIngredient(BaseModel):
    quantity: float = Field(gt=0, allow_inf_nan=False)
    unit: Unit

#recipe with quantities recalculated for the requested number of servings
#(the data in the database is not changed)
class ScaledRecipe(BaseModel):
    id: int
    title: str
    instructions: str
    prep_time_minutes: int
    author_id: int
    category_id: int | None
    original_servings: int
    servings: int
    ingredients: list[RecipeIngredient]
