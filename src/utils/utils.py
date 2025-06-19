import os

def validate_password(password, db_password):
    return password == db_password

def init_dirs():
    if not os.path.exists("./static/employees"):
        os.makedirs("./static/employees")
    if not os.path.exists("./static/accessLogs"):
        os.makedirs("./static/accessLogs")