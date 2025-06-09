from pydantic import BaseModel

class User(BaseModel):
    login: str
    password: str

class UserLoginResponse(BaseModel):
    login: str
    accessLayerId: int
    resultCode: int

class LogResponse(BaseModel):
    id: int
    name: str
    access: bool
    time: str

class AccessLogsResponse(BaseModel):
    logs: list[LogResponse]
    count: int
    resultCode: int = 0

class UserResponse(BaseModel):
    id: int
    login: str
    accessLayer: int

class UsersResponse(BaseModel):
    users: list[UserResponse]
    count: int
    resultCode: int = 0


class GoodResponse(BaseModel):

    """
    Хорошие ответы сервера
    1000 - authorization success
    """

    resultCode: int = 0

    def __init__(self, code, **data):
        super().__init__(**data)
        self.resultCode = code


class BadResponse(BaseModel):

    """
    Плохие ответы сервера
    1 - object not exist in database
    2 - invalid password
    3 - access and refresh tokens expired
    4 - access denied
    """

    resultCode: int = 1

    def __init__(self, code, **data):
        super().__init__(**data)
        self.resultCode = code
