import pytest
from sqlalchemy.exc import IntegrityError
from users.models import UsersModel, UserRole
from factories.user_factory import UserFactory

class TestUserModel:
    """Test User model"""
    
    def test_create_user(self, test_db):
        """Test user creation"""
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
        """Test check unique username and email"""
        user1 = UserFactory.create(username="duplicate", email="duplicate@example.com")
        test_db.add(user1)
        test_db.commit()
        
        # Has to has un-unique error
        user2 = UserFactory.create(username="duplicate", email="different@example.com")
        test_db.add(user2)
        
        with pytest.raises(IntegrityError):
            test_db.commit()
        
        test_db.rollback()
    
    def test_user_password_hashing(self):
        """Password hash test"""
        user = UserFactory.build()
        plain_password = "my_password"
        user.set_password(plain_password)
        
        assert user.verify_password(plain_password) == True
        assert user.verify_password("wrong_password") == False
        assert user.password != plain_password
    
    def test_user_role_enum(self):
        """Test user roles"""
        user = UserFactory.build(role=UserRole.ADMIN)
        assert user.role.value == "admin"
        
        user.role = UserRole.EXPERT
        assert user.role.value == "expert"

class TestTokenBlacklistModel:
    """Test blacklist tokens"""
    
    def test_create_blacklisted_token(self, test_db):
        """Test blacklist token creation"""
        from auth.token_blacklist import BlacklistedToken
        from datetime import datetime, timedelta
        
        token = BlacklistedToken(
            token="test_token_123",
            user_id=1,
            expires_at=datetime.utcnow() + timedelta(hours=1)
        )
        
        test_db.add(token)
        test_db.commit()
        
        assert token.id is not None
        assert token.token == "test_token_123"
        assert token.user_id == 1
