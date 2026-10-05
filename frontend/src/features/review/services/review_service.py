from __future__ import annotations

from typing import List, Tuple

from features.resumes.models import Resume, parse_resume_list
from shared.lib.api_client import ApiClient
from shared.utils.formatting import safe_filename

PAGE_SIZE = 50


class ReviewService:
    def __init__(self, api: ApiClient) -> None:
        self._api = api

    def list_all(self, skip: int = 0, limit: int = PAGE_SIZE) -> List[Resume]:
        limit = max(1, min(int(limit), 200))
        data = self._api.request_json(
            "GET", "/resumes/expert/all", params={"skip": max(0, int(skip)), "limit": limit}
        )
        return parse_resume_list(data)

    def download(self, resume_id: int, fallback_name: str = "resume.pdf") -> Tuple[str, bytes]:
        response = self._api.request("GET", f"/resumes/download/{int(resume_id)}")
        return safe_filename(fallback_name), response.content
