from app import UserService


def test_login():
    service = UserService()
    result = service.login("Alice", "pass")
    assert result["ok"] is True
