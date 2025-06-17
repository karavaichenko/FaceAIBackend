from pydantic import BaseModel
from starlette.responses import FileResponse


# Auth models
class User(BaseModel):
    login: str
    password: str

class UserLoginResponse(BaseModel):
    login: str
    accessLayerId: int
    resultCode: int

# Logs Models
class LogResponse(BaseModel):
    id: int
    name: str
    access: bool
    time: str

class AccessLogsResponse(BaseModel):
    logs: list[LogResponse]
    count: int
    resultCode: int = 0

# Users Models
class UserResponse(BaseModel):
    id: int
    login: str
    accessLayer: int

class UsersResponse(BaseModel):
    users: list[UserResponse]
    count: int
    resultCode: int = 0

class AddUserRequest(BaseModel):
    login: str
    password: str
    accessLayerId: int

class GetUserResponse(BaseModel):
    id: int
    login: str
    accessLayer: int
    resultCode: int = 0

class SetUserPasswordRequest(BaseModel):
    id: int
    password: str

class SetUserAccessLayerRequest(BaseModel):
    id: int
    accessLayerId: int

# Employees models
class Employee(BaseModel):
    id: int
    name: str
    info: str
    isAccess: bool

class EmployeeResponse(BaseModel):
    id: int
    name: str
    info: str
    isAccess: bool
    resultCode: int = 0

class EmployeesResponse(BaseModel):
    employees: list[Employee]
    count: int
    resultCode: int = 0

class EmployeePostRequest(BaseModel):
    name: str
    info: str = '-'
    isAccess: bool

class EmployeePostResponse(BaseModel):
    id: int
    resultCode: int = 100


# Results models
class GoodResponse(BaseModel):

    """
    Хорошие ответы сервера
    1000 - authorization success
    100 - object added
    101 - object deleted
    102 - object changed
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
    5 - invalid request
    """

    resultCode: int = 1

    def __init__(self, code, **data):
        super().__init__(**data)
        self.resultCode = code
