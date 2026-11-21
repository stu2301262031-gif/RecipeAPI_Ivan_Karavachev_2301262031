from exceptions import NotFound, DuplicationError
from sqlalchemy.orm import Session
from sqlalchemy import select, func
from db.models import Category

class CategoryService:
    def _get(self, id: int, db_session: Session) -> Category:
        category = db_session.get(Category, id)
        if category is None:
            raise NotFound(f"Category with id {id} not found")
        return category

    #names are compared case-insensitive, the spaces are already removed by the pydantic model
    def _check_name(self, name: str, db_session: Session, id: int | None = None):
        stmt = select(Category).where(func.lower(Category.name) == name.lower())
        if id is not None:
            stmt = stmt.where(Category.id != id)
        if db_session.scalars(stmt).first() is not None:
            raise DuplicationError(f"Category with name {name} already exists")

    def get_categories(self, db_session: Session) -> list[Category]:
        return db_session.scalars(select(Category).order_by(Category.id)).all()

    def get_category(self, id: int, db_session: Session) -> Category:
        return self._get(id, db_session)

    def create_category(self, data: dict, db_session: Session) -> Category:
        self._check_name(data["name"], db_session)
        category = Category(name=data["name"])
        db_session.add(category)
        db_session.commit()
        db_session.refresh(category)
        return category

    def update_category(self, id: int, data: dict, db_session: Session) -> Category:
        category = self._get(id, db_session)
        self._check_name(data["name"], db_session, id)
        category.name = data["name"]
        db_session.commit()
        db_session.refresh(category)
        return category

    #the recipes of the category are not deleted,
    #the database sets their category_id to NULL (ON DELETE SET NULL)
    def delete_category(self, id: int, db_session: Session):
        category = self._get(id, db_session)
        db_session.delete(category)
        db_session.commit()

def get_category_service() -> CategoryService:
    return CategoryService()
