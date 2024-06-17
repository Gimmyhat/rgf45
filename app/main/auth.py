import os

from dotenv import load_dotenv
from flask import g
from flask_httpauth import HTTPBasicAuth
from werkzeug.security import generate_password_hash, check_password_hash

auth = HTTPBasicAuth()

load_dotenv()

users = {
    "admin": {
        "password": generate_password_hash(os.environ.get("ADMIN_PASSWORD")),
        "can_view_logs": True,
        "can_view_delete": False
    },
    "user": {
        "password": generate_password_hash(os.environ.get("USER_PASSWORD")),
        "can_view_logs": False,
        "can_view_delete": False
    }
}


@auth.verify_password
def verify_pwd(username, password):
    if username in users and check_password_hash(users[username]['password'], password):
        g.can_view_logs = users[username]['can_view_logs']
        return username
