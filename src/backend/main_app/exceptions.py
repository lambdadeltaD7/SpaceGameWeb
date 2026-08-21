from fastapi import HTTPException, status



class OnlyForAdminsException(HTTPException):
    def __init__(self):
        super().__init__(
            status_code = status.HTTP_401_UNAUTHORIZED,
            detail = "only for admins"
        )


class NotOwnerException(HTTPException):
    def __init__(self):
        super().__init__(
            status_code = status.HTTP_401_UNAUTHORIZED,
            detail = "you must be an owner or admin to do this"
        )

