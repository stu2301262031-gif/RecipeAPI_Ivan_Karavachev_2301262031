from pydantic import BaseModel, Field, ConfigDict, EmailStr, field_validator

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
