import pytest
from datetime import datetime, timedelta
from app.tests.factories.user_factory import UserFactory
from app.auth.jwt_auth import (
    generate_access_token, 
    generate_refresh_token,
    get_authenticated_user,
    add_token_to_blacklist
)

class TestJWTAuth:
    """Test JWT Authentication"""
    
    def test_generate_access_token(self, test_db):
        """Test generating access token using UserFactory"""
        user = UserFactory.create(id=1)
        test_db.add(user)
        test_db.commit()
        
        token = generate_access_token(user.id)
        assert isinstance(token, str)
        assert len(token) > 0
    
    def test_generate_refresh_token(self, test_db):
        """Test generating refresh token using UserFactory"""
        user = UserFactory.create(id=1)
        test_db.add(user)
        test_db.commit()
        
        token = generate_refresh_token(user.id)
        assert isinstance(token, str)
        assert len(token) > 0
    
    def test_token_blacklist(self, test_db):
        """Test token blacklist functionality using UserFactory"""
        user = UserFactory.create(id=1)
        test_db.add(user)
        test_db.commit()
        
        token = generate_access_token(user.id)
        
        # Add token to blacklist
        add_token_to_blacklist(token, user.id, test_db)
        
        # Check if token is in blacklist
        from app.auth.token_blacklist import BlacklistedToken
        blacklisted = test_db.query(BlacklistedToken).filter_by(token=token).first()
        assert blacklisted is not None
        assert blacklisted.user_id == user.id
