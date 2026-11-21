from fastapi import FastAPI, status, Request
from fastapi.responses import JSONResponse
from sqlalchemy.exc import IntegrityError
from routers import authors_router, categories_router, ingredients_router, recipes_router
from exceptions import AppError, NotFound, DuplicationError, ConflictError
import uvicorn

#the database schema is created and updated only with Alembic migrations:
#alembic upgrade head
app = FastAPI(title="Recipe Catalog API")

app.include_router(authors_router.router)
app.include_router(categories_router.router)
app.include_router(ingredients_router.router)
app.include_router(recipes_router.router)

@app.exception_handler(AppError)
def handle_errors(request: Request, exc: AppError):
    if type(exc) is NotFound:
        status_code = status.HTTP_404_NOT_FOUND
    elif type(exc) in (DuplicationError, ConflictError):
        status_code = status.HTTP_409_CONFLICT
    else:
        status_code = status.HTTP_400_BAD_REQUEST
    return JSONResponse(status_code=status_code,
                        content={"error_message": exc.message})

#last line of defence - if a database constraint (UNIQUE, FOREIGN KEY, CHECK) is violated
#the request is answered with 409 Conflict instead of 500 Internal Server Error
@app.exception_handler(IntegrityError)
def handle_integrity_errors(request: Request, exc: IntegrityError):
    return JSONResponse(status_code=status.HTTP_409_CONFLICT,
                        content={"error_message": "The operation violates a database constraint"})

@app.get("/health")
def health_check():
    return {"health": "running"}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
