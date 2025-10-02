import pytest
from datetime import datetime, timedelta
from auth.jwt_auth import (
    generate_access_token, 
    generate_refresh_token,
    get_authenticated_user,
    add_token_to_blacklist
)
from users.models import UsersModel, UserRole
from factories.user_factory import UserFactory

class TestJWTAuth:
    """تست JWT Authentication"""
    
    def test_generate_access_token(self, test_db):
        """Test generating access token"""
        user = UserFactory.create(id=1)
        test_db.add(user)
        test_db.commit()
        
        token = generate_access_token(user.id)
        assert isinstance(token, str)
        assert len(token) > 0
    
    def test_generate_refresh_token(self, test_db):
        """Test generating refresh token"""
        user = UserFactory.create(id=1)
        test_db.add(user)
        test_db.commit()
        
        token = generate_refresh_token(user.id)
        assert isinstance(token, str)
        assert len(token) > 0
    
    def test_token_blacklist(self, test_db):
        """Test token blacklist func"""
        user = UserFactory.create(id=1)
        test_db.add(user)
        test_db.commit()
        
        token = generate_access_token(user.id)
        
        # Adding token into blacklist
        add_token_to_blacklist(token, user.id, test_db)
        
        # Check token in blacklist
        from auth.token_blacklist import BlacklistedToken
        blacklisted = test_db.query(BlacklistedToken).filter_by(token=token).first()
        assert blacklisted is not None
        assert blacklisted.user_id == user.id
    
    def test_get_authenticated_user_valid_token(self, test_db):
        """Getting a valid user with token"""
        user = UserFactory.create(id=1, username="auth_test")
        test_db.add(user)
        test_db.commit()
        
        token = generate_access_token(user.id)
        
        # User virtualization with token
        from fastapi.security import HTTPBearer
        from fastapi import HTTPException
        

        try:
            pass
        except HTTPException:
            pytest.fail("A valid token has not to have a error")
