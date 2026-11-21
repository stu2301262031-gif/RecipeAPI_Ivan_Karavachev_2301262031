class AppError(Exception):
    def __init__(self, message):
        super().__init__(message)
        self.message = message

# raised when a requested resource does not exist -> 404 Not Found
class NotFound(AppError):
    pass

# raised when a unique value (email, name, title) is already taken -> 409 Conflict
class DuplicationError(AppError):
    pass

# raised when an operation is not allowed because of existing relations -> 409 Conflict
class ConflictError(AppError):
    pass
