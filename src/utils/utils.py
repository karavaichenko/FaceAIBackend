import os
from passlib.hash import bcrypt

def hash_password(password: str):
    return bcrypt.hash(password)

def validate_password(password, db_password):
    return bcrypt.verify(password, db_password)

def init_dirs():
    if not os.path.exists("./static/employees"):
        os.makedirs("./static/employees")
    if not os.path.exists("./static/accessLogs"):
        os.makedirs("./static/accessLogs")