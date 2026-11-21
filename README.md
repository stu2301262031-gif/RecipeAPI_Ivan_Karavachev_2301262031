# Recipe Catalog REST API

Курсов проект по **Уеб сървърни езици** – REST API за каталог с рецепти, автори, категории и съставки.

- **Автор:** Иван Каравачев, фак. № 2301262031
- **Технологии:** FastAPI, SQLAlchemy 2 (ORM), Pydantic 2, Alembic, SQLite

## Стартиране

```bash
# 1. Виртуална среда
python -m venv .venv
.venv\Scripts\activate          # Windows
source .venv/bin/activate       # Linux / macOS

# 2. Зависимости
pip install -r requirements.txt

# 3. Създаване на базата данни чрез миграциите
alembic upgrade head

# 4. (по желание) Примерни данни – автори, категории, съставки и рецепти
python initialize_database.py

# 5. Стартиране на сървъра
python main.py                  # или: fastapi dev main.py
```

Swagger документацията е на адрес **http://127.0.0.1:8000/docs**.

Базата данни (`recipes.sqlite`) се създава **само** чрез Alembic миграции – `Base.metadata.create_all()` не се използва.

## Структура на проекта

```
main.py                 приложението, регистриране на routers и обработка на грешки
config.py               MAX_SERVINGS = 50 + 31 = 81
exceptions.py           NotFound (404), DuplicationError / ConflictError (409)
enums.py                Unit (g, ml, pcs), Difficulty (easy, medium, hard)
db/database.py          engine, SessionLocal, Base, get_db (Dependency Injection)
db/models.py            SQLAlchemy ORM модели
models/models.py        Pydantic модели за API заявките и отговорите
services/               бизнес логика и заявки към базата данни
routers/                FastAPI ендпойнти (контролери)
alembic/versions/       миграции
initialize_database.py  примерни данни за тестване в Swagger
```

Router-ите получават сесията към базата и съответния service чрез `Depends(...)`.
ORM моделите (`db/models.py`) и Pydantic моделите (`models/models.py`) са отделени.

## Модел на данните

| Таблица | Полета |
|---|---|
| `author` | id, name, email (уникален) |
| `category` | id, name (уникално) |
| `ingredient` | id, name (уникално) |
| `recipe` | id, title, instructions, prep_time_minutes, servings, difficulty, author_id, category_id |
| `recipe_ingredient` | id, recipe_id, ingredient_id, quantity (> 0), unit (g / ml / pcs) |

- **One-to-Many:** Author → Recipe, Category → Recipe
- **Many-to-Many:** Recipe ↔ Ingredient чрез асоциативния модел `RecipeIngredient`

### Миграции

1. `a37b1c5e6f0f_create_initial_tables` – създава всички таблици.
2. `f6cb03ba7b07_add_difficulty_to_recipe` – добавя задължителното поле `difficulty`.
   Вече съществуващите рецепти получават стойност `medium` чрез временна стойност по подразбиране.

## Ендпойнти

### CRUD

| Метод | Път | Описание |
|---|---|---|
| GET / POST | `/authors/` | списък / създаване на автор |
| GET / PUT / DELETE | `/authors/{id}` | автор по id |
| GET / POST | `/categories/` | списък / създаване на категория |
| GET / PUT / DELETE | `/categories/{id}` | категория по id |
| GET / POST | `/ingredients/` | списък / създаване на съставка |
| GET / PUT / DELETE | `/ingredients/{id}` | съставка по id |
| GET / POST | `/recipes/` | списък (с филтри) / създаване на рецепта |
| GET / PUT / DELETE | `/recipes/{id}` | рецепта по id |

### Бизнес логика

| Метод | Път | Описание |
|---|---|---|
| GET | `/authors/{id}/recipes` | всички рецепти на автор |
| GET | `/recipes/{id}/ingredients` | съставките на рецепта с количество и мерна единица |
| POST | `/recipes/{id}/ingredients` | добавяне на съществуваща съставка към рецепта |
| PUT | `/recipes/{id}/ingredients/{ingredient_id}` | промяна на количеството и мерната единица |
| DELETE | `/recipes/{id}/ingredients/{ingredient_id}` | премахване на съставка от рецепта (съставката остава) |
| GET | `/recipes/{id}/scaled?servings=8` | рецепта с преизчислени количества (базата не се променя) |

### Филтриране на рецепти

`GET /recipes/?title=cake&category_id=2&max_prep_time=30`

- `title` – част от заглавието (без значение главни/малки букви)
- `category_id` – категория
- `max_prep_time` – максимално време за приготвяне (включително)

Филтрите се комбинират с AND и се изпълняват като една заявка към базата данни.

## Бизнес правила

- Една съставка се добавя само веднъж към рецепта. Повторен опит връща `409 Conflict`, а количеството не се променя.
- Един автор не може да има две рецепти с еднакво заглавие.
- Имената и заглавията се сравняват без значение главни/малки букви, а интервалите в началото и края се премахват (работи и за кирилица).
- Различни автори могат да имат еднакви имена, но имейлите им трябва да са различни.
- При списък със свързани записи: несъществуващ основен ресурс → `404`, а липса на записи → `200` и `[]`.
- Максималният брой порции при преизчисляване е **81** (50 + последните две цифри на фак. № 2301262031). При по-голяма стойност се връща `422`.

## Правила при изтриване

Правилата са зададени чрез foreign key ограничения в базата (за SQLite се включва `PRAGMA foreign_keys=ON`):

| Действие | Резултат | Ограничение в базата |
|---|---|---|
| Изтриване на рецепта | връзките със съставките се премахват, съставките остават | `ON DELETE CASCADE` |
| Изтриване на категория | рецептите остават без категория | `ON DELETE SET NULL` |
| Изтриване на автор с рецепти | `409 Conflict` | `ON DELETE RESTRICT` |
| Изтриване на съставка, използвана в рецепта | `409 Conflict` | `ON DELETE RESTRICT` |

## Валидация и грешки

- Задължителните текстови полета не могат да са празни или само интервали → `422`
- Времето за приготвяне и порциите са положителни цели числа → `422`
- Невалиден имейл, количество ≤ 0 или мерна единица извън g / ml / pcs → `422`
- Несъществуващ ресурс → `404`, дублиране или нарушено ограничение → `409`
- Грешките от бизнес логиката се връщат като `{"error_message": "..."}`
