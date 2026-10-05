from features.auth import validators as v


def test_login_requires_both_fields():
    assert set(v.validate_login("", "")) == {"username", "password"}
    assert v.validate_login("bob", "x") == {}


def test_username_rules():
    assert v.validate_username("ab")
    assert v.validate_username("a" * 51)
    assert v.validate_username("bad name!")
    assert v.validate_username("good.name-1_x") == ""


def test_email_rules():
    assert v.validate_email("nope")
    assert v.validate_email("a@b") != ""
    assert v.validate_email("a@b.io") == ""


def test_password_is_measured_in_bytes():
    assert v.validate_password("short")
    assert v.validate_password("12345678") == ""
    assert v.validate_password("a" * 72) == ""
    assert v.validate_password("a" * 73)
    assert v.validate_password("\u00e9" * 37)  # 74 bytes, 37 chars


def test_github_optional_but_prefixed():
    assert v.validate_github("") == ""
    assert v.validate_github("https://github.com/user") == ""
    assert v.validate_github("http://github.com/user")
    assert v.validate_github("https://github.com/")


def test_registration_collects_errors_and_checks_confirmation():
    errors = v.validate_registration("a", "bad", "short", "other", "x")
    assert set(errors) == {"username", "email", "password", "github"}
    assert v.validate_registration("alice", "a@b.io", "password1", "password2") == {"confirm_password": "Passwords do not match."}
    assert v.validate_registration("alice", "a@b.io", "password1", "password1", "https://github.com/a") == {}
