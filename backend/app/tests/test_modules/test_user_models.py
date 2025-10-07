import pytest
from sqlalchemy.exc import IntegrityError
from app.tests.factories.user_factory import UserFactory
from app.users.models import UsersModel, UserRole

class TestUserModel:
    """Test User model"""
    
    def test_create_user(self, test_db):
        """Test user creation using UserFactory"""
        user = UserFactory.create(
            username="testuser",
            email="test@example.com"
        )
        test_db.add(user)
        test_db.commit()
        
        assert user.id is not None
        assert user.username == "testuser"
        assert user.role == UserRole.CANDIDATE
        assert user.is_active == True
        assert user.verify_password("testpass123") == True
    
    def test_user_unique_constraint(self, test_db):
        """Test unique username and email constraint using UserFactory"""
        user1 = UserFactory.create(username="duplicate", email="duplicate@example.com")
        test_db.add(user1)
        test_db.commit()
        
        # Should raise integrity error for duplicate username
        user2 = UserFactory.create(username="duplicate", email="different@example.com")
        test_db.add(user2)
        
        with pytest.raises(IntegrityError):
            test_db.commit()
        
        test_db.rollback()
    
    def test_user_password_hashing(self):
        """Test password hashing using UserFactory"""
        user = UserFactory.build()
        plain_password = "my_password"
        user.set_password(plain_password)
        
        assert user.verify_password(plain_password) == True
        assert user.verify_password("wrong_password") == False
        assert user.password != plain_password
    
    def test_user_role_enum(self):
        """Test user role enum using UserFactory"""
        user = UserFactory.build(role=UserRole.ADMIN)
        assert user.role.value == "admin"
        
        user.role = UserRole.EXPERT
        assert user.role.value == "expert"
