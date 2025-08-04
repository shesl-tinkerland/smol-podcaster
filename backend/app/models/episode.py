from pydantic import BaseModel, Field, HttpUrl
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum

class ProcessingStatus(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"

class TranscriptSegment(BaseModel):
    speaker: str
    text: str
    start: float
    end: float

class EpisodeBase(BaseModel):
    name: str = Field(..., description="Episode name")
    speakers_count: int = Field(..., ge=1, description="Number of speakers")
    
class EpisodeCreate(EpisodeBase):
    file_url: Optional[HttpUrl] = None
    transcript_only: bool = False
    generate_extra: bool = False

class EpisodeUpdate(BaseModel):
    show_notes: Optional[List[Dict[str, str]]] = None
    chapters: Optional[str] = None
    writeup: Optional[str] = None
    title_suggestions: Optional[str] = None
    tweet_suggestions: Optional[str] = None

class Episode(EpisodeBase):
    id: str
    status: ProcessingStatus
    created_at: datetime
    updated_at: datetime
    file_path: Optional[str] = None
    transcript_path: Optional[str] = None
    results_path: Optional[str] = None
    show_notes: Optional[List[Dict[str, str]]] = None
    chapters: Optional[str] = None
    writeup: Optional[str] = None
    error_message: Optional[str] = None

    class Config:
        from_attributes = True

class ProcessingTask(BaseModel):
    task_id: str
    episode_id: str
    status: ProcessingStatus
    progress: Optional[int] = Field(None, ge=0, le=100)
    current_step: Optional[str] = None
    error_message: Optional[str] = None

class ChapterSyncRequest(BaseModel):
    audio_name: str
    video_name: str
    chapters: str

class ShowNotesItem(BaseModel):
    text: str
    url: Optional[str] = None