from users.models import UsersModel, UserRole
import factory

class UserFactory(factory.Factory):
    """Factory for creating users"""
    
    class Meta:
        model = UsersModel
    
    username = factory.Sequence(lambda n: f"testuser{n}")
    email = factory.Sequence(lambda n: f"test{n}@example.com")
    github = "https://github.com/testuser"
    role = UserRole.CANDIDATE
    is_active = True
    
    @classmethod
    def _create(cls, model_class, *args, **kwargs):
        """Creating user with hashed password"""
        password = kwargs.pop('password', 'testpass123')
        user = model_class(*args, **kwargs)
        user.set_password(password)
        return user
    
    @classmethod
    def create_admin(cls, **kwargs):
        """Creating Admin user"""
        return cls.create(role=UserRole.ADMIN, **kwargs)
    
    @classmethod
    def create_expert(cls, **kwargs):
        """Creating Expert user"""
        return cls.create(role=UserRole.EXPERT, **kwargs)
