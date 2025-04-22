import os
from dotenv import load_dotenv

load_dotenv()

REGISTERED_USERS_FILE = "registered_users.txt"

def save_registered_user(user_id):
    if os.path.exists(REGISTERED_USERS_FILE):
        with open(REGISTERED_USERS_FILE, "a") as file:
            file.write(f"{user_id}\n")
    else:
        with open(REGISTERED_USERS_FILE, "w") as file:
            file.write(f"{user_id}\n")

def get_registered_users():
    if os.path.exists(REGISTERED_USERS_FILE):
        with open(REGISTERED_USERS_FILE, "r") as file:
            return file.readlines()
    return []
