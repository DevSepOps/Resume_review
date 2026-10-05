from __future__ import annotations

from dataclasses import dataclass
from shared.lib.api_client import ApiError
from typing import Any, Dict, List, Optional


@dataclass(frozen=True)
class Resume:
    id: int
    file_name: str
    file_size: int
    created_date: Optional[str]
    username: Optional[str] = None
    email: Optional[str] = None
    github: Optional[str] = None

    @classmethod
    def from_api(cls, data: Dict[str, Any]) -> "Resume":
        return cls(
            id=int(data["id"]),
            file_name=str(data.get("file_name") or "resume.pdf"),
            file_size=int(data.get("file_size") or 0),
            created_date=data.get("created_date"),
            username=data.get("username"),
            email=data.get("email"),
            github=data.get("github"),
        )


def parse_resume_list(data: Any) -> List[Resume]:
    """Parse a list payload; malformed data becomes a friendly ApiError."""
    if not isinstance(data, list):
        raise ApiError("Unexpected response from the server.")
    try:
        return [Resume.from_api(item) for item in data]
    except (KeyError, TypeError, ValueError, AttributeError) as exc:
        raise ApiError("Unexpected response from the server.") from exc
