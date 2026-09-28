from datetime import datetime, timezone
from enum import Enum
from typing import Optional
from uuid import uuid4

from pydantic import BaseModel, Field, field_validator
from typing import Optional


class ContractStatus(str, Enum):
    UPLOADED = "uploaded"
    ANALYZING = "analyzing"
    ANALYZED = "analyzed"
    ERROR = "error"


class ContractBase(BaseModel):
    filename: str
    original_filename: str
    text_content: str = ""
    page_count: int = Field(default=1, ge=0)
    word_count: int = Field(default=0, ge=0)


class ContractCreate(ContractBase):
    pass


class Contract(ContractBase):
    id: str = Field(default_factory=lambda: str(uuid4()))
    upload_date: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    status: ContractStatus = ContractStatus.UPLOADED
    file_path: Optional[str] = None
    file_size_mb: float = Field(default=0.0, ge=0.0)

    @field_validator("word_count", mode="before")
    @classmethod
    def calculate_word_count(cls, v, info):
        # Auto-compute word count if default 0 is passed and text exists
        if not v and "text_content" in info.data:
            return len(info.data["text_content"].split())
        return v


class ContractResponse(BaseModel):
    id: str
    filename: str
    original_filename: str
    upload_date: datetime
    page_count: int
    word_count: int
    status: ContractStatus
    file_size_mb: float

    class Config:
        from_attributes = True
