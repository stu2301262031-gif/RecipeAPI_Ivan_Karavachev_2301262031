import pytest
from config import MAX_SERVINGS

#----------------------------------- helpers -----------------------------------

def create_author(client, name="Ivan Petrov", email="ivan@example.com"):
    response = client.post("/authors/", json={"name": name, "email": email})
    assert response.status_code == 201
    return response.json()

def create_category(client, name="Desserts"):
    response = client.post("/categories/", json={"name": name})
    assert response.status_code == 201
    return response.json()

def create_ingredient(client, name):
    response = client.post("/ingredients/", json={"name": name})
    assert response.status_code == 201
    return response.json()

def recipe_data(author_id, **fields):
    data = {"title": "Pancakes", "instructions": "Mix and fry.", "prep_time_minutes": 30,
            "servings": 4, "difficulty": "easy", "author_id": author_id, "category_id": None}
    data.update(fields)
    return data

def create_recipe(client, author_id, **fields):
    response = client.post("/recipes/", json=recipe_data(author_id, **fields))
    assert response.status_code == 201
    return response.json()

def add_ingredient(client, recipe_id, ingredient_id, quantity, unit):
    return client.post(f"/recipes/{recipe_id}/ingredients",
                       json={"ingredient_id": ingredient_id, "quantity": quantity, "unit": unit})

#----------------------------------- authors -----------------------------------

def test_create_author_trims_name_and_lowercases_email(client):
    author = create_author(client, name="  Ivan Petrov ", email=" Ivan@Example.COM ")
    assert author["name"] == "Ivan Petrov"
    assert author["email"] == "ivan@example.com"

def test_author_email_must_be_unique(client):
    create_author(client, email="ivan@example.com")
    response = client.post("/authors/", json={"name": "Other", "email": "IVAN@example.com"})
    assert response.status_code == 409
    assert "error_message" in response.json()

def test_different_authors_can_have_the_same_name(client):
    create_author(client, name="Ivan Petrov", email="first@example.com")
    create_author(client, name="ivan petrov", email="second@example.com")
    assert len(client.get("/authors/").json()) == 2

def test_update_author_email_conflict(client):
    create_author(client, email="first@example.com")
    second = create_author(client, email="second@example.com")
    response = client.put(f"/authors/{second['id']}", json={"name": "X", "email": "first@example.com"})
    assert response.status_code == 409

@pytest.mark.parametrize("data", [
    {"name": "   ", "email": "a@example.com"},
    {"name": "", "email": "a@example.com"},
    {"name": "Ivan", "email": "not-an-email"},
    {"name": "Ivan"},
])
def test_author_validation(client, data):
    assert client.post("/authors/", json=data).status_code == 422

def test_missing_author_returns_404(client):
    assert client.get("/authors/999").status_code == 404
    assert client.put("/authors/999", json={"name": "X", "email": "x@example.com"}).status_code == 404
    assert client.delete("/authors/999").status_code == 404

#----------------------------------- categories and ingredients -----------------------------------

def test_category_name_is_unique_case_insensitive(client):
    category = create_category(client, name="  Супи ")
    assert category["name"] == "Супи"
    assert client.post("/categories/", json={"name": "СУПИ"}).status_code == 409
    assert client.post("/categories/", json={"name": "   "}).status_code == 422

def test_ingredient_name_is_unique_case_insensitive(client):
    create_ingredient(client, "Flour")
    sugar = create_ingredient(client, "Sugar")
    assert client.post("/ingredients/", json={"name": " FLOUR "}).status_code == 409
    assert client.put(f"/ingredients/{sugar['id']}", json={"name": "flour"}).status_code == 409
    assert client.put(f"/ingredients/{sugar['id']}", json={"name": "SUGAR"}).status_code == 200

#----------------------------------- recipes -----------------------------------

def test_create_recipe(client):
    author = create_author(client)
    category = create_category(client)
    recipe = create_recipe(client, author["id"], title=" Pancakes ", category_id=category["id"],
                           difficulty="medium")
    assert recipe["title"] == "Pancakes"
    assert recipe["category_id"] == category["id"]
    assert recipe["difficulty"] == "medium"

@pytest.mark.parametrize("fields", [
    {"servings": 0},
    {"servings": "4"},
    {"prep_time_minutes": -5},
    {"prep_time_minutes": 10.5},
    {"title": "  "},
    {"instructions": ""},
    {"difficulty": "extreme"},
])
def test_recipe_validation(client, fields):
    author = create_author(client)
    assert client.post("/recipes/", json=recipe_data(author["id"], **fields)).status_code == 422

def test_recipe_difficulty_is_required(client):
    author = create_author(client)
    data = recipe_data(author["id"])
    del data["difficulty"]
    assert client.post("/recipes/", json=data).status_code == 422

def test_recipe_with_missing_author_or_category_returns_404(client):
    author = create_author(client)
    assert client.post("/recipes/", json=recipe_data(999)).status_code == 404
    assert client.post("/recipes/", json=recipe_data(author["id"], category_id=999)).status_code == 404

def test_author_can_not_have_two_recipes_with_the_same_title(client):
    ivan = create_author(client, email="ivan@example.com")
    maria = create_author(client, name="Maria", email="maria@example.com")
    create_recipe(client, ivan["id"], title="Pancakes")
    assert client.post("/recipes/", json=recipe_data(ivan["id"], title=" PANCAKES ")).status_code == 409
    #another author can use the same title
    create_recipe(client, maria["id"], title="Pancakes")

def test_update_recipe_title_conflict(client):
    author = create_author(client)
    create_recipe(client, author["id"], title="Pancakes")
    cake = create_recipe(client, author["id"], title="Cake")
    response = client.put(f"/recipes/{cake['id']}", json=recipe_data(author["id"], title="pancakes"))
    assert response.status_code == 409
    response = client.put(f"/recipes/{cake['id']}", json=recipe_data(author["id"], title="Chocolate cake"))
    assert response.status_code == 200
    assert response.json()["title"] == "Chocolate cake"

def test_filter_recipes(client):
    author = create_author(client)
    soups = create_category(client, "Soups")
    desserts = create_category(client, "Desserts")
    create_recipe(client, author["id"], title="Pancakes", category_id=desserts["id"], prep_time_minutes=20)
    create_recipe(client, author["id"], title="Chocolate cake", category_id=desserts["id"], prep_time_minutes=90)
    create_recipe(client, author["id"], title="Таратор", category_id=soups["id"], prep_time_minutes=15)

    def titles(params):
        response = client.get("/recipes/", params=params)
        assert response.status_code == 200
        return sorted(recipe["title"] for recipe in response.json())

    assert titles({"title": "CAKE"}) == ["Chocolate cake", "Pancakes"]
    assert titles({"title": "тарат"}) == ["Таратор"]
    assert titles({"category_id": desserts["id"]}) == ["Chocolate cake", "Pancakes"]
    assert titles({"max_prep_time": 20}) == ["Pancakes", "Таратор"]
    assert titles({"title": "cake", "category_id": desserts["id"], "max_prep_time": 30}) == ["Pancakes"]
    assert titles({"title": "cake", "category_id": soups["id"]}) == []
    assert titles({}) == ["Chocolate cake", "Pancakes", "Таратор"]

#----------------------------------- related records -----------------------------------

def test_author_recipes(client):
    ivan = create_author(client, email="ivan@example.com")
    maria = create_author(client, name="Maria", email="maria@example.com")
    create_recipe(client, ivan["id"], title="Pancakes")
    create_recipe(client, ivan["id"], title="Cake")
    assert len(client.get(f"/authors/{ivan['id']}/recipes").json()) == 2
    response = client.get(f"/authors/{maria['id']}/recipes")
    assert response.status_code == 200 and response.json() == []
    assert client.get("/authors/999/recipes").status_code == 404

def test_recipe_ingredients_of_missing_or_empty_recipe(client):
    author = create_author(client)
    recipe = create_recipe(client, author["id"])
    response = client.get(f"/recipes/{recipe['id']}/ingredients")
    assert response.status_code == 200 and response.json() == []
    assert client.get("/recipes/999/ingredients").status_code == 404

def test_add_ingredient_to_recipe(client):
    author = create_author(client)
    recipe = create_recipe(client, author["id"])
    flour = create_ingredient(client, "Flour")
    response = add_ingredient(client, recipe["id"], flour["id"], 200, "g")
    assert response.status_code == 201
    assert response.json() == {"ingredient": {"id": flour["id"], "name": "Flour"}, "quantity": 200.0, "unit": "g"}

def test_ingredient_can_be_added_only_once(client):
    author = create_author(client)
    recipe = create_recipe(client, author["id"])
    flour = create_ingredient(client, "Flour")
    add_ingredient(client, recipe["id"], flour["id"], 200, "g")
    assert add_ingredient(client, recipe["id"], flour["id"], 999, "ml").status_code == 409
    #the existing quantity is not changed
    ingredients = client.get(f"/recipes/{recipe['id']}/ingredients").json()
    assert ingredients[0]["quantity"] == 200.0 and ingredients[0]["unit"] == "g"

def test_same_ingredient_in_different_recipes(client):
    author = create_author(client)
    pancakes = create_recipe(client, author["id"], title="Pancakes")
    cake = create_recipe(client, author["id"], title="Cake")
    flour = create_ingredient(client, "Flour")
    assert add_ingredient(client, pancakes["id"], flour["id"], 200, "g").status_code == 201
    assert add_ingredient(client, cake["id"], flour["id"], 350, "g").status_code == 201
    assert client.get(f"/recipes/{cake['id']}/ingredients").json()[0]["quantity"] == 350.0

@pytest.mark.parametrize("quantity, unit", [(0, "g"), (-1, "g"), (100, "kg")])
def test_add_ingredient_validation(client, quantity, unit):
    author = create_author(client)
    recipe = create_recipe(client, author["id"])
    flour = create_ingredient(client, "Flour")
    assert add_ingredient(client, recipe["id"], flour["id"], quantity, unit).status_code == 422

def test_add_ingredient_with_missing_recipe_or_ingredient(client):
    author = create_author(client)
    recipe = create_recipe(client, author["id"])
    flour = create_ingredient(client, "Flour")
    assert add_ingredient(client, 999, flour["id"], 1, "g").status_code == 404
    assert add_ingredient(client, recipe["id"], 999, 1, "g").status_code == 404

def test_update_recipe_ingredient(client):
    author = create_author(client)
    recipe = create_recipe(client, author["id"])
    flour = create_ingredient(client, "Flour")
    sugar = create_ingredient(client, "Sugar")
    add_ingredient(client, recipe["id"], flour["id"], 200, "g")

    response = client.put(f"/recipes/{recipe['id']}/ingredients/{flour['id']}", json={"quantity": 250, "unit": "g"})
    assert response.status_code == 200 and response.json()["quantity"] == 250.0
    #ingredient that is not part of the recipe
    response = client.put(f"/recipes/{recipe['id']}/ingredients/{sugar['id']}", json={"quantity": 1, "unit": "g"})
    assert response.status_code == 404
    response = client.put(f"/recipes/{recipe['id']}/ingredients/{flour['id']}", json={"quantity": 0, "unit": "g"})
    assert response.status_code == 422

def test_remove_ingredient_from_recipe_keeps_the_ingredient(client):
    author = create_author(client)
    recipe = create_recipe(client, author["id"])
    flour = create_ingredient(client, "Flour")
    add_ingredient(client, recipe["id"], flour["id"], 200, "g")

    assert client.delete(f"/recipes/{recipe['id']}/ingredients/{flour['id']}").status_code == 204
    assert client.delete(f"/recipes/{recipe['id']}/ingredients/{flour['id']}").status_code == 404
    assert client.get(f"/recipes/{recipe['id']}/ingredients").json() == []
    assert client.get(f"/ingredients/{flour['id']}").status_code == 200

#----------------------------------- servings scaling -----------------------------------

def test_scaled_recipe(client):
    author = create_author(client)
    recipe = create_recipe(client, author["id"], servings=4)
    flour = create_ingredient(client, "Flour")
    eggs = create_ingredient(client, "Eggs")
    add_ingredient(client, recipe["id"], flour["id"], 250, "g")
    add_ingredient(client, recipe["id"], eggs["id"], 2, "pcs")

    response = client.get(f"/recipes/{recipe['id']}/scaled", params={"servings": 6})
    assert response.status_code == 200
    scaled = response.json()
    assert scaled["original_servings"] == 4 and scaled["servings"] == 6
    assert [(i["ingredient"]["name"], i["quantity"], i["unit"]) for i in scaled["ingredients"]] == [
        ("Flour", 375.0, "g"), ("Eggs", 3.0, "pcs")]

    #the data in the database is not changed
    assert client.get(f"/recipes/{recipe['id']}").json()["servings"] == 4
    assert [i["quantity"] for i in client.get(f"/recipes/{recipe['id']}/ingredients").json()] == [250.0, 2.0]

def test_scaled_recipe_servings_limit(client):
    #50 + the last two digits of the faculty number 2301262031
    assert MAX_SERVINGS == 81
    author = create_author(client)
    recipe = create_recipe(client, author["id"])
    assert client.get(f"/recipes/{recipe['id']}/scaled", params={"servings": 81}).status_code == 200
    assert client.get(f"/recipes/{recipe['id']}/scaled", params={"servings": 82}).status_code == 422
    assert client.get(f"/recipes/{recipe['id']}/scaled", params={"servings": 0}).status_code == 422
    assert client.get(f"/recipes/{recipe['id']}/scaled").status_code == 422
    assert client.get("/recipes/999/scaled", params={"servings": 2}).status_code == 404

#----------------------------------- delete rules -----------------------------------

def test_delete_recipe_keeps_the_ingredients(client):
    author = create_author(client)
    recipe = create_recipe(client, author["id"])
    flour = create_ingredient(client, "Flour")
    add_ingredient(client, recipe["id"], flour["id"], 200, "g")

    assert client.delete(f"/recipes/{recipe['id']}").status_code == 204
    assert client.get(f"/recipes/{recipe['id']}").status_code == 404
    assert client.get(f"/ingredients/{flour['id']}").status_code == 200
    #the link is deleted, so the ingredient is not used anymore and can be deleted
    assert client.delete(f"/ingredients/{flour['id']}").status_code == 204

def test_delete_category_keeps_its_recipes(client):
    author = create_author(client)
    category = create_category(client)
    recipe = create_recipe(client, author["id"], category_id=category["id"])

    assert client.delete(f"/categories/{category['id']}").status_code == 204
    response = client.get(f"/recipes/{recipe['id']}")
    assert response.status_code == 200
    assert response.json()["category_id"] is None

def test_delete_author_with_recipes_returns_409(client):
    author = create_author(client)
    create_recipe(client, author["id"])
    assert client.delete(f"/authors/{author['id']}").status_code == 409
    assert client.get(f"/authors/{author['id']}").status_code == 200

def test_delete_author_without_recipes(client):
    author = create_author(client)
    assert client.delete(f"/authors/{author['id']}").status_code == 204
    assert client.get(f"/authors/{author['id']}").status_code == 404

def test_delete_ingredient_used_in_recipe_returns_409(client):
    author = create_author(client)
    recipe = create_recipe(client, author["id"])
    flour = create_ingredient(client, "Flour")
    add_ingredient(client, recipe["id"], flour["id"], 200, "g")
    assert client.delete(f"/ingredients/{flour['id']}").status_code == 409
    assert client.get(f"/ingredients/{flour['id']}").status_code == 200
