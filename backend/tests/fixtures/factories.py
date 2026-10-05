import factory

from app.internal.entities import Resume, Role, User


class UserFactory(factory.Factory):
    class Meta:
        model = User

    id = factory.Sequence(lambda n: n + 1)
    username = factory.Sequence(lambda n: f"user{n}")
    email = factory.LazyAttribute(lambda o: f"{o.username}@example.com")
    password_hash = "hashed:Password123"
    role = Role.CANDIDATE
    is_active = True


class ResumeFactory(factory.Factory):
    class Meta:
        model = Resume

    id = factory.Sequence(lambda n: n + 1)
    user_id = 1
    storage_key = factory.Sequence(lambda n: f"{n}.pdf")
    file_name = "cv.pdf"
    file_size = 10
    mime_type = "application/pdf"


def register_payload(**overrides) -> dict:
    data = {
        "username": "alice",
        "email": "alice@example.com",
        "password": "Password123",
        "confirm_password": "Password123",
    }
    data.update(overrides)
    return data
