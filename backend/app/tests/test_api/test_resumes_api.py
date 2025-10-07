import pytest
import io
from app.tests.factories.user_factory import UserFactory


class TestResumesAPI:
    """Test resume endpoints"""

    def test_upload_resume_success(self, client, test_db):
        """Test successful resume upload using UserFactory"""
        # Create user using factory
        user = UserFactory.create(
            username="resumeuser", email="resume@example.com", password="resumepass123"
        )
        test_db.add(user)
        test_db.commit()

        # Login to get token
        login_data = {"username": "resumeuser", "password": "resumepass123"}
        login_response = client.post("/users/login", json=login_data)
        access_token = login_response.json()["access_token"]

        headers = {"Authorization": f"Bearer {access_token}"}

        # Upload PDF file
        pdf_content = b"%PDF-1.4 fake pdf content"
        files = {
            "resume": ("test_resume.pdf", io.BytesIO(pdf_content), "application/pdf")
        }

        response = client.post("/resumes/upload", files=files, headers=headers)

        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "resume" in data
        assert data["resume"]["file_name"] == "test_resume.pdf"

    def test_upload_non_pdf_file(self, client, test_db):
        """Test uploading non-PDF file using UserFactory"""
        user = UserFactory.create(
            username="resumeuser2",
            email="resume2@example.com",
            password="resumepass123",
        )
        test_db.add(user)
        test_db.commit()

        login_data = {"username": "resumeuser2", "password": "resumepass123"}
        login_response = client.post("/users/login", json=login_data)
        access_token = login_response.json()["access_token"]

        headers = {"Authorization": f"Bearer {access_token}"}

        # Upload text file (should fail)
        text_content = b"This is a text file, not PDF"
        files = {"resume": ("test.txt", io.BytesIO(text_content), "text/plain")}

        response = client.post("/resumes/upload", files=files, headers=headers)

        assert response.status_code == 400
        assert "Only PDF files are allowed" in response.json()["detail"]

    def test_get_user_resumes(self, client, test_db):
        """Test getting user's resumes using UserFactory"""
        user = UserFactory.create(
            username="resumeuser3",
            email="resume3@example.com",
            password="resumepass123",
        )
        test_db.add(user)
        test_db.commit()

        login_data = {"username": "resumeuser3", "password": "resumepass123"}
        login_response = client.post("/users/login", json=login_data)
        access_token = login_response.json()["access_token"]

        headers = {"Authorization": f"Bearer {access_token}"}
        response = client.get("/resumes/my-resumes", headers=headers)

        assert response.status_code == 200
        assert isinstance(response.json(), list)
