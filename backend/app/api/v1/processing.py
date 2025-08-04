from fastapi import APIRouter, HTTPException
from typing import Dict
from app.models.episode import ProcessingTask, ProcessingStatus
from app.core.celery_app import celery_app
from celery.result import AsyncResult

router = APIRouter()

@router.get("/status/{task_id}", response_model=ProcessingTask)
async def get_processing_status(task_id: str):
    result = AsyncResult(task_id, app=celery_app)
    
    if result.state == 'PENDING':
        status = ProcessingStatus.PENDING
        current_step = "Waiting to start"
        progress = 0
    elif result.state == 'PROGRESS':
        status = ProcessingStatus.PROCESSING
        current_step = result.info.get('current', '')
        progress = result.info.get('progress', 0)
    elif result.state == 'SUCCESS':
        status = ProcessingStatus.COMPLETED
        current_step = "Completed"
        progress = 100
    else:  # FAILURE
        status = ProcessingStatus.FAILED
        current_step = "Failed"
        progress = 0
    
    return ProcessingTask(
        task_id=task_id,
        episode_id=result.info.get('episode_id', '') if hasattr(result.info, 'get') else '',
        status=status,
        progress=progress,
        current_step=current_step,
        error_message=str(result.info) if result.state == 'FAILURE' else None
    )

@router.post("/retry/{task_id}")
async def retry_processing(task_id: str) -> Dict[str, str]:
    result = AsyncResult(task_id, app=celery_app)
    
    if result.state != 'FAILURE':
        raise HTTPException(status_code=400, detail="Task has not failed")
    
    # Retry the task
    result.retry()
    
    return {"message": "Task retry initiated", "task_id": task_id}