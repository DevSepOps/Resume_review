import pytest
from app.tests.factories.user_factory import UserFactory

class TestUsersAPI:
    """Test users endpoints"""
    
    def test_register_user_success(self, client, sample_user_data):
        """Test successful user registration"""
        response = client.post("/users/register", json=sample_user_data)
        assert response.status_code == 201
        assert response.json()["detail"] == "User registered successfully"
    
    def test_register_user_duplicate(self, client, test_db):
        """Test duplicate user registration using UserFactory"""
        # Create user first using factory
        user = UserFactory.create(
            username="duplicateuser",
            email="duplicate@example.com",
            password="testpass123"
        )
        test_db.add(user)
        test_db.commit()
        
        # Try to register same username
        duplicate_data = {
            "username": "duplicateuser",
            "password": "anotherpass123",
            "confirm_password": "anotherpass123",
            "email": "different@example.com",
            "github": "https://github.com/duplicate"
        }
        response = client.post("/users/register", json=duplicate_data)
        
        assert response.status_code == 409
        assert "already exists" in response.json()["detail"]
    
    def test_login_success(self, client, test_db):
        """Test successful login using UserFactory"""
        user = UserFactory.create(
            username="loginuser",
            email="login@example.com",
            password="loginpass123"
        )
        test_db.add(user)
        test_db.commit()
        
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
        """Test login with wrong password using UserFactory"""
        user = UserFactory.create(
            username="loginuser2",
            email="login2@example.com",
            password="correctpass"
        )
        test_db.add(user)
        test_db.commit()
        
        login_data = {
            "username": "loginuser2",
            "password": "wrongpassword"
        }
        response = client.post("/users/login", json=login_data)
        
        assert response.status_code == 401
        assert "Invalid username or password" in response.json()["detail"]
    
    def test_refresh_token(self, client, test_db):
        """Test token refresh using UserFactory"""
        user = UserFactory.create(
            username="refreshuser",
            email="refresh@example.com",
            password="refreshpass123"
        )
        test_db.add(user)
        test_db.commit()
        
        login_data = {"username": "refreshuser", "password": "refreshpass123"}
        login_response = client.post("/users/login", json=login_data)
        refresh_token = login_response.json()["refresh_token"]
        
        refresh_data = {"token": refresh_token}
        response = client.post("/users/refresh_token", json=refresh_data)
        
        assert response.status_code == 200
        assert "access_token" in response.json()

# class TestProtectedEndpoints:
#     """Test protected endpoints"""
    
#     def test_access_protected_endpoint_without_token(self, client):
#         """Test accessing protected endpoint without token"""
#         response = client.get("/resumes/my-resumes")
#         assert response.status_code == 401  # Unauthorized
    
#     def test_access_protected_endpoint_with_valid_token(self, client, test_db):
#         """Test accessing protected endpoint with valid token using UserFactory"""
#         user = UserFactory.create(
#             username="protecteduser",
#             email="protected@example.com",
#             password="protected123"
#         )
#         test_db.add(user)
#         test_db.commit()
        
#         login_data = {"username": "protecteduser", "password": "protected123"}
#         login_response = client.post("/users/login", json=login_data)
#         access_token = login_response.json()["access_token"]
        
#         headers = {"Authorization": f"Bearer {access_token}"}
#         response = client.get("/resumes/my-resumes", headers=headers)
        
#         assert response.status_code in [200, 404]  # 200 if resumes exist, 404 if none
