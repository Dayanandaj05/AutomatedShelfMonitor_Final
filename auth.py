# auth.py

# Import configuration
try:
    from config import ADMIN_USERNAME, ADMIN_PASSWORD
except ImportError:
    ADMIN_USERNAME = "admin"
    ADMIN_PASSWORD = "admin123"

def validate_login(username, password):
    """
    Validate the admin login credentials.
    """
    if not username or not password:
        return False, "Username and password cannot be empty."

    if username == ADMIN_USERNAME and password == ADMIN_PASSWORD:
        return True, "Login successful!"
    else:
        return False, "Invalid username or password."
