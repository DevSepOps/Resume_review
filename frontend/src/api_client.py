import requests
import json
from typing import Optional, Dict, Any


class ResumeAPI:
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.access_token = None
        self.refresh_token = None

    def login(self, username: str, password: str) -> Dict[str, Any]:
        """Login user and store tokens"""
        try:
            response = requests.post(
                f"{self.base_url}/users/login",
                json={"username": username, "password": password},
            )

            if response.status_code == 202:
                data = response.json()
                self.access_token = data["access_token"]
                self.refresh_token = data["refresh_token"]
                return {"success": True, "data": data}
            else:
                return {
                    "success": False,
                    "error": response.json().get("detail", "Login failed"),
                }

        except Exception as e:
            return {"success": False, "error": f"Network error: {str(e)}"}

    def register(
        self, username: str, password: str, email: str, github: str = ""
    ) -> Dict[str, Any]:
        """Register new user"""
        try:
            response = requests.post(
                f"{self.base_url}/users/register",
                json={
                    "username": username,
                    "password": password,
                    "confirm_password": password,
                    "email": email,
                    "github": github,
                },
            )

            if response.status_code == 201:
                return {"success": True, "data": response.json()}
            else:
                return {
                    "success": False,
                    "error": response.json().get("detail", "Registration failed"),
                }

        except Exception as e:
            return {"success": False, "error": f"Network error: {str(e)}"}

    def upload_resume(self, file_path: str) -> Dict[str, Any]:
        """Upload resume file"""
        if not self.access_token:
            return {"success": False, "error": "Not authenticated"}

        try:
            with open(file_path, "rb") as file:
                files = {"resume": (file_path.split("/")[-1], file, "application/pdf")}
                headers = {"Authorization": f"Bearer {self.access_token}"}

                response = requests.post(
                    f"{self.base_url}/resumes/upload", files=files, headers=headers
                )

            if response.status_code == 200:
                return {"success": True, "data": response.json()}
            else:
                return {
                    "success": False,
                    "error": response.json().get("detail", "Upload failed"),
                }

        except Exception as e:
            return {"success": False, "error": f"Upload error: {str(e)}"}

    def get_my_resumes(self) -> Dict[str, Any]:
        """Get user's resumes"""
        if not self.access_token:
            return {"success": False, "error": "Not authenticated"}

        try:
            headers = {"Authorization": f"Bearer {self.access_token}"}
            response = requests.get(
                f"{self.base_url}/resumes/my-resumes", headers=headers
            )

            if response.status_code == 200:
                return {"success": True, "data": response.json()}
            else:
                return {
                    "success": False,
                    "error": response.json().get("detail", "Failed to get resumes"),
                }

        except Exception as e:
            return {"success": False, "error": f"Network error: {str(e)}"}

    def logout(self) -> Dict[str, Any]:
        """Logout user"""
        if not self.access_token:
            return {"success": False, "error": "Not authenticated"}

        try:
            headers = {"Authorization": f"Bearer {self.access_token}"}
            response = requests.post(f"{self.base_url}/users/logout", headers=headers)

            self.access_token = None
            self.refresh_token = None

            return {"success": True, "data": response.json()}

        except Exception as e:
            return {"success": False, "error": f"Logout error: {str(e)}"}
