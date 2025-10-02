import pytest
from factories.user_factory import UserFactory

class TestUsersAPI:
    """Test users endpoints"""
    
    def test_register_user_success(self, client, sample_user_data):
        """Test successful signup"""
        response = client.post("/users/register", json=sample_user_data)
        
        assert response.status_code == 201
        assert response.json()["detail"] == "User registered successfully"
    
    def test_register_user_duplicate(self, client, test_db, sample_user_data):
        """Test creating excisting user"""
        client.post("/users/register", json=sample_user_data)
        
        response = client.post("/users/register", json=sample_user_data)
        
        assert response.status_code == 409
        assert "already exists" in response.json()["detail"]
    
    def test_login_success(self, client, test_db):
        """Test login status"""
        user_data = {
            "username": "loginuser",
            "password": "loginpass123",
            "confirm_password": "loginpass123",
            "email": "login@example.com",
            "github": "https://github.com/loginuser"
        }
        client.post("/users/register", json=user_data)
        
        login_data = {
            "username": "loginuser",
            "password": "loginpass123"
        }
        response = client.post("/users/login", json=login_data)
        
        assert response.status_code == 202
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data
        assert data["detail"] == "logged in successfully"
    
    def test_login_wrong_password(self, client, test_db):
        """Test wrong password login"""
        user_data = {
            "username": "loginuser2",
            "password": "loginpass123",
            "confirm_password": "loginpass123",
            "email": "login2@example.com",
            "github": "https://github.com/loginuser2"
        }
        client.post("/users/register", json=user_data)
        
        login_data = {
            "username": "loginuser2",
            "password": "wrongpassword"
        }
        response = client.post("/users/login", json=login_data)
        
        assert response.status_code == 401
        assert "Invalid username or password" in response.json()["detail"]
    
    def test_refresh_token(self, client, test_db):
        """Test refresh token"""
        user_data = {
            "username": "refreshuser",
            "password": "refreshpass123",
            "confirm_password": "refreshpass123",
            "email": "refresh@example.com",
            "github": "https://github.com/refreshuser"
        }
        client.post("/users/register", json=user_data)
        
        login_data = {"username": "refreshuser", "password": "refreshpass123"}
        login_response = client.post("/users/login", json=login_data)
        refresh_token = login_response.json()["refresh_token"]
        
        refresh_data = {"token": refresh_token}
        response = client.post("/users/refresh_token", json=refresh_data)
        
        assert response.status_code == 200
        assert "access_token" in response.json()

class TestProtectedEndpoints:
    """Test secure endpoint"""
    
    def test_access_protected_endpoint_without_token(self, client):
        """Test access without token"""
        response = client.get("/resumes/my-resumes")
        assert response.status_code == 401  # Unauthorized
    
    def test_access_protected_endpoint_with_valid_token(self, client, test_db):
        """Test access with token"""
  
        user_data = {
            "username": "protecteduser",
            "password": "protected123",
            "confirm_password": "protected123",
            "email": "protected@example.com",
            "github": "https://github.com/protecteduser"
        }
        client.post("/users/register", json=user_data)
        
        login_data = {"username": "protecteduser", "password": "protected123"}
        login_response = client.post("/users/login", json=login_data)
        access_token = login_response.json()["access_token"]
        
        headers = {"Authorization": f"Bearer {access_token}"}
        response = client.get("/resumes/my-resumes", headers=headers)
        
        assert response.status_code in [200, 404]