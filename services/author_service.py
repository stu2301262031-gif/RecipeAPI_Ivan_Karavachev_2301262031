from exceptions import NotFound, DuplicationError, ConflictError
from sqlalchemy.orm import Session
from sqlalchemy import select, func
from db.models import Author, Recipe

class AuthorService:
    def _get(self, id: int, db_session: Session) -> Author:
        author = db_session.get(Author, id)
        # if no author found in database throw exception
        if author is None:
            raise NotFound(f"Author with id {id} not found")
        return author

    #different authors can have the same name, but the email must be unique
    def _check_email(self, email: str, db_session: Session, id: int | None = None):
        stmt = select(Author).where(func.lower(Author.email) == email.lower())
        if id is not None:
            stmt = stmt.where(Author.id != id)
        if db_session.scalars(stmt).first() is not None:
            raise DuplicationError(f"Author with email {email} already exists")

    def get_authors(self, db_session: Session) -> list[Author]:
        return db_session.scalars(select(Author).order_by(Author.id)).all()

    def get_author(self, id: int, db_session: Session) -> Author:
        return self._get(id, db_session)

    def create_author(self, data: dict, db_session: Session) -> Author:
        self._check_email(data["email"], db_session)
        author = Author(name=data["name"], email=data["email"])
        db_session.add(author)
        db_session.commit()
        db_session.refresh(author)
        return author

    def update_author(self, id: int, data: dict, db_session: Session) -> Author:
        author = self._get(id, db_session)
        self._check_email(data["email"], db_session, id)
        author.name = data["name"]
        author.email = data["email"]
        db_session.commit()
        db_session.refresh(author)
        return author

    def delete_author(self, id: int, db_session: Session):
        author = self._get(id, db_session)
        recipes_count = db_session.scalar(
            select(func.count()).select_from(Recipe).where(Recipe.author_id == id))
        if recipes_count > 0:
            raise ConflictError(
                f"Author with id {id} has {recipes_count} recipe(s) and can not be deleted")
        db_session.delete(author)
        db_session.commit()

def get_author_service() -> AuthorService:
    return AuthorService()
