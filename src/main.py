from http.client import responses
from pydantic import BaseModel
from fastapi import FastAPI
from fastapi.params import Depends
from pydantic.v1 import ValidationError
from starlette.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from src.database.database import Database
import uvicorn
from src.schemas.schemas import User, BadResponse, GoodResponse, UserLoginResponse, AccessLogsResponse, LogResponse, \
    UsersResponse
from src.utils import utils, auth
from dotenv import load_dotenv
import os

load_dotenv()
app = FastAPI()

path = 'localhost'
if 'MY_PATH' in os.environ:
    path = os.environ["MY_PATH"]

URL = os.getenv('DB_URL')
database = Database(URL)
user_auth = auth.UserAuth("./src/certs/private_key.pem", "./src/certs/public_key.pem")

@app.post("/auth/login")
def login(user: User):
    user_db = database.get_user(user.login)
    if user_db is not None:
        if utils.validate_password(user.password, user_db.password):
            access, refresh = user_auth.create_tokens(user_db.id, user_db.login, user_db.access_layer_id)
            content = {
                "login": user_db.login,
                "accessLayerId": user_db.access_layer_id,
                "resultCode": 1000,
            }
            response = add_cookie(content, refresh, access)
            return response
        else:
            return BadResponse(2)
    else:
        return BadResponse(1)


@app.get("/auth")
def auth(access_token: dict = Depends(user_auth.check_access_jwt),
         refresh_token: dict = Depends(user_auth.check_refresh_jwt)):
    if access_token is not None:
        user_db = database.get_user(access_token["login"])
        if user_db is None:
            return BadResponse(1)
        return UserLoginResponse(login=user_db.login, accessLayerId=user_db.access_layer_id, resultCode=1000)
    elif refresh_token is not None:
        user_db = database.get_user(refresh_token["login"])
        if user_db is None:
            return BadResponse(1)
        new_access_token = user_auth.create_jwt(user_db.id, user_db.login, user_db.access_layer_id)
        new_refresh_token = user_auth.create_jwt(user_db.id, user_db.login, user_db.access_layer_id, 14*24*60)
        response = UserLoginResponse(login=user_db.login, accessLayerId=user_db.access_layer_id, resultCode=1000)
        return add_cookie(response, new_refresh_token, new_access_token)
    else:
        return BadResponse(3)

@app.delete('/auth/logout')
def logout():
    response = add_cookie({"resultCode": 0}, "", "")
    return response

@app.get("/accessLogs")
def access_logs(page: int, page_size: int = 10, access_token: dict = Depends(user_auth.check_access_jwt)):
    if check_access(access_token) is not None:
        logs = database.get_access_logs(page)
        logs = map(lambda x: x.to_schema(), logs)
        count = database.get_access_log_size()
        return AccessLogsResponse(logs=list(logs), count=count)
    else:
        return BadResponse(3)

@app.get("/users")
def users(page: int, page_size: int = 10, access_token: dict = Depends(user_auth.check_access_jwt)):
    user_access_layer = check_access(access_token)
    if user_access_layer is not None:
        if user_access_layer == 0:
            users_db = database.get_users(page, page_size)
            users_db = list(map(lambda x: x.to_schema(), users_db))
            count = database.get_users_size()
            return UsersResponse(users=users_db, count=count)
        else:
            return BadResponse(4)
    else:
        return BadResponse(3)

def check_access(access_token: dict):
    if access_token is not None:
        user_db = database.get_user(access_token["login"])
        if user_db is None:
            return None
        return user_db.access_layer_id
    else:
        return None

def add_cookie(content, refresh, access):
    if isinstance(content, BaseModel):
        content = dict(content)
    response = JSONResponse(content=content)
    response.set_cookie(key="access_token", value=access)
    response.set_cookie(key="refresh_token", value=refresh)
    return response

origins = [
    "http://localhost",
    "http://localhost:5173"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

if __name__ == "__main__":
    uvicorn.run("main:app")