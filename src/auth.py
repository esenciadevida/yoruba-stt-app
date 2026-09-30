import json
import hashlib
import os

USER_FILE = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "users.json")


def load_users():
    try:
        abs_path = os.path.abspath(USER_FILE)
        with open(abs_path, "r") as f:
            data = json.load(f)
            if "users" not in data:
                data["users"] = {}
            return data
    except Exception as e:
        print(f"[AUTH DEBUG] Error loading users: {e} from {os.path.abspath(USER_FILE)}")
        return {"users": {}}


def save_users(data):
    with open(USER_FILE, "w") as f:
        json.dump(data, f, indent=4)


def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()


def authenticate_user(username, password):
    users = load_users()
    if username not in users["users"]:
        return False, "Username not found"
    if users["users"][username] != hash_password(password):
        return False, "Incorrect password"
    return True, "Login successful"


def create_user(username, password):
    users = load_users()
    if username in users["users"]:
        return False, "Username already exists"
    users["users"][username] = hash_password(password)
    save_users(users)
    return True, "Account created successfully"
