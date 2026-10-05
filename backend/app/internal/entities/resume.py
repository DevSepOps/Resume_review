from dataclasses import dataclass
from datetime import datetime
from typing import Optional

PDF_MIME_TYPE = "application/pdf"


@dataclass
class Resume:
    user_id: int
    storage_key: str
    file_name: str
    file_size: int
    mime_type: str = PDF_MIME_TYPE
    id: Optional[int] = None
    created_date: Optional[datetime] = None
    updated_date: Optional[datetime] = None
