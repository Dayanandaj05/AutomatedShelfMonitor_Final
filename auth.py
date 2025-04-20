# auth.py

def validate_login(username, password):
    """
    Validate the admin login credentials.
    You can later expand this to check against a database or use hashed passwords.
    """
    VALID_USERNAME = "admin"
    VALID_PASSWORD = "admin123"

    if not username or not password:
        return False, "Username and password cannot be empty."

    if username == VALID_USERNAME and password == VALID_PASSWORD:
        return True, "Login successful!"
    else:
        return False, "Invalid username or password."
