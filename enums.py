from enum import Enum

#enums are shared by the ORM models (db/models.py) and the Pydantic models (models/models.py)
class Unit(str, Enum):
    g = "g"
    ml = "ml"
    pcs = "pcs"

class Difficulty(str, Enum):
    easy = "easy"
    medium = "medium"
    hard = "hard"
