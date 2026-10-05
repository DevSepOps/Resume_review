from __future__ import annotations

from typing import List, Tuple

from features.resumes.models import Resume, parse_resume_list
from shared.lib.api_client import ApiClient, ApiError
from shared.utils.formatting import safe_filename


class ResumeService:
    def __init__(self, api: ApiClient) -> None:
        self._api = api

    def list_mine(self) -> List[Resume]:
        return parse_resume_list(self._api.request_json("GET", "/resumes/my-resumes"))

    def upload(self, file_name: str, content: bytes) -> Resume:
        data = self._api.request_json(
            "POST", "/resumes/upload",
            files={"resume": (safe_filename(file_name), content, "application/pdf")},
        )
        try:
            return Resume.from_api(data["resume"])
        except (KeyError, TypeError, ValueError) as exc:
            raise ApiError("Unexpected response from the server.") from exc

    def delete(self, resume_id: int) -> None:
        self._api.request_json("DELETE", f"/resumes/{int(resume_id)}")

    def download(self, resume_id: int, fallback_name: str = "resume.pdf") -> Tuple[str, bytes]:
        response = self._api.request("GET", f"/resumes/download/{int(resume_id)}")
        return safe_filename(fallback_name), response.content
