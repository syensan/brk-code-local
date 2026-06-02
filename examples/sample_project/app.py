import json
from utils import normalize_name

API_KEY = "should_be_redacted"


class UserService:
    def login(self, username: str, password: str):
        """Validate a user login request."""
        name = normalize_name(username)
        if not password:
            raise ValueError("password required")
        return {"user": name, "ok": True}


def unsafe_eval(expr: str):
    return eval(expr)
