import pytest
import io

class TestFullUserFlow:
    """Full user tests"""
    
    def test_complete_user_journey(self, client, test_db):
        """Test user migration from sign up to upload CV"""
        # 1. Sign up
        user_data = {
            "username": "journeyuser",
            "password": "journeypass123",
            "confirm_password": "journeypass123",
            "email": "journey@example.com",
            "github": "https://github.com/journeyuser"
        }
        register_response = client.post("/users/register", json=user_data)
        assert register_response.status_code == 201
        
        # 2. Login
        login_data = {"username": "journeyuser", "password": "journeypass123"}
        login_response = client.post("/users/login", json=login_data)
        assert login_response.status_code == 202
        
        tokens = login_response.json()
        access_token = tokens["access_token"]
        headers = {"Authorization": f"Bearer {access_token}"}
        
        # 3. Getting empty CV's
        resumes_response = client.get("/resumes/my-resumes", headers=headers)
        assert resumes_response.status_code == 200
        assert resumes_response.json() == []
        
        # 4. Uploading CV's
        pdf_content = b"%PDF-1.4 fake pdf content for journey"
        files = {
            "resume": ("journey_resume.pdf", io.BytesIO(pdf_content), "application/pdf")
        }
        upload_response = client.post("/resumes/upload", files=files, headers=headers)
        assert upload_response.status_code == 200
        
        # 5. Getting uploaded CV's
        resumes_after_upload = client.get("/resumes/my-resumes", headers=headers)
        assert resumes_after_upload.status_code == 200
        resumes_data = resumes_after_upload.json()
        assert len(resumes_data) == 1
        assert resumes_data[0]["file_name"] == "journey_resume.pdf"
        
        # 6. Logout
        logout_response = client.post("/users/logout", headers=headers)
        assert logout_response.status_code == 200
        
        # 7. Access attempt after logout
        protected_response = client.get("/resumes/my-resumes", headers=headers)
        assert protected_response.status_code == 401  # Unauthorized
