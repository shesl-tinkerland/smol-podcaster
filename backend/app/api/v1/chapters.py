from fastapi import APIRouter, BackgroundTasks
from app.models.episode import ChapterSyncRequest
from app.services.chapter_sync_service import ChapterSyncService
from app.core.tasks import sync_chapters_task

router = APIRouter()
chapter_service = ChapterSyncService()

@router.post("/sync")
async def sync_chapters(
    request: ChapterSyncRequest,
    background_tasks: BackgroundTasks
) -> dict:
    # Queue the chapter sync task
    task = sync_chapters_task.delay(
        request.chapters,
        request.audio_name,
        request.video_name
    )
    
    return {
        "message": f"Syncing chapters for {request.video_name} and {request.audio_name}",
        "task_id": task.id
    }