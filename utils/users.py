import os
from dotenv import load_dotenv

load_dotenv()

REGISTERED_USERS_FILE = "registered_users.txt"

def save_registered_user(user_id):
    registered_users = get_registered_users()
    if user_id not in registered_users:
        with open(REGISTERED_USERS_FILE, "a") as file:
            file.write(f"{user_id}\n")
        return True
    else:
        return False

def get_registered_users():
    if os.path.exists(REGISTERED_USERS_FILE):
        with open(REGISTERED_USERS_FILE, "r") as file:
            return [user.strip() for user in file.readlines()]
    return []

def remove_registered_user(user_id):
    registered_users = get_registered_users()
    if user_id in registered_users:
        registered_users.remove(user_id)
        with open(REGISTERED_USERS_FILE, "w") as file:
            for user in registered_users:
                file.write(f"{user}\n")
        print(f"User {user_id} has been removed from the registered list.")
    else:
        print(f"User {user_id} not found in the registered list.")
