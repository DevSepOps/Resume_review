import pytest
import io
from app.tests.factories.user_factory import UserFactory


class TestFullUserFlow:
    """Test complete user flow"""

    def test_complete_user_journey(self, client, test_db):
        """Test complete user journey from signup to resume upload using UserFactory"""
        # 1. Create user using factory
        user = UserFactory.create(
            username="journeyuser",
            email="journey@example.com",
            password="journeypass123",
        )
        test_db.add(user)
        test_db.commit()

        # 2. Login
        login_data = {"username": "journeyuser", "password": "journeypass123"}
        login_response = client.post("/users/login", json=login_data)
        assert login_response.status_code == 202

        tokens = login_response.json()
        access_token = tokens["access_token"]
        headers = {"Authorization": f"Bearer {access_token}"}

        # 3. Get empty resumes list
        resumes_response = client.get("/resumes/my-resumes", headers=headers)
        assert resumes_response.status_code == 200
        assert resumes_response.json() == []

        # 4. Upload resume
        pdf_content = b"%PDF-1.4 fake pdf content for journey"
        files = {
            "resume": ("journey_resume.pdf", io.BytesIO(pdf_content), "application/pdf")
        }
        upload_response = client.post("/resumes/upload", files=files, headers=headers)
        assert upload_response.status_code == 200

        # 5. Get uploaded resumes
        resumes_after_upload = client.get("/resumes/my-resumes", headers=headers)
        assert resumes_after_upload.status_code == 200
        resumes_data = resumes_after_upload.json()
        assert len(resumes_data) == 1
        assert resumes_data[0]["file_name"] == "journey_resume.pdf"

        # 6. Logout
        logout_response = client.post("/users/logout", headers=headers)
        assert logout_response.status_code == 200

        # 7. Try to access after logout
        protected_response = client.get("/resumes/my-resumes", headers=headers)
        assert protected_response.status_code == 401  # Unauthorized
