from fastapi import APIRouter, HTTPException, UploadFile, File, Form, BackgroundTasks
from typing import List, Optional
from app.models.episode import Episode, EpisodeCreate, EpisodeUpdate, ShowNotesItem
from app.services.episode_service import EpisodeService
from app.core.tasks import process_episode_task
import os
import tempfile
import re

router = APIRouter()
episode_service = EpisodeService()

@router.post("/", response_model=Episode)
async def create_episode(
    background_tasks: BackgroundTasks,
    name: str = Form(...),
    speakers_count: int = Form(...),
    file: Optional[UploadFile] = File(None),
    url: Optional[str] = Form(None),
    transcript_only: bool = Form(False),
    generate_extra: bool = Form(False)
):
    if not file and not url:
        raise HTTPException(status_code=400, detail="Either file or URL must be provided")
    
    file_or_url = url
    if file:
        # Save uploaded file to temporary location
        _, file_extension = os.path.splitext(file.filename)
        temp_dir = tempfile.gettempdir()
        # Sanitize filename
        safe_name = re.sub(r'[^\w\s-]', '', name).strip()
        safe_name = re.sub(r'[-\s]+', '-', safe_name)
        temp_file_path = os.path.join(temp_dir, f"upload_{safe_name}{file_extension}")
        
        with open(temp_file_path, "wb") as buffer:
            content = await file.read()
            buffer.write(content)
        
        file_or_url = temp_file_path
    
    # Create episode in database
    episode_data = EpisodeCreate(
        name=name,
        speakers_count=speakers_count,
        transcript_only=transcript_only,
        generate_extra=generate_extra
    )
    episode = await episode_service.create_episode(episode_data)
    
    # Queue processing task
    process_episode_task.delay(
        episode.id,
        file_or_url,
        name,
        speakers_count,
        transcript_only,
        generate_extra
    )
    
    return episode

@router.get("/", response_model=List[Episode])
async def list_episodes():
    return await episode_service.list_episodes()

@router.get("/{episode_id}", response_model=Episode)
async def get_episode(episode_id: str):
    episode = await episode_service.get_episode(episode_id)
    if not episode:
        raise HTTPException(status_code=404, detail="Episode not found")
    return episode

@router.patch("/{episode_id}/show-notes", response_model=Episode)
async def update_show_notes(episode_id: str, items: List[ShowNotesItem]):
    episode = await episode_service.get_episode(episode_id)
    if not episode:
        raise HTTPException(status_code=404, detail="Episode not found")
    
    # Read current file
    file_path = os.path.join('./podcasts-results', f'substack_{episode.name}.md')
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="Episode file not found")
    
    with open(file_path, 'r') as file:
        content = file.read()
    
    # Update show notes section
    import re
    show_notes_pattern = r'### Show Notes.*?(?=### Timestamps)'
    updated_show_notes = "### Show Notes\n" + "\n".join([
        f"- [{item.text}]({item.url})" if item.url else f"- {item.text}"
        for item in items
    ])
    updated_content = re.sub(show_notes_pattern, updated_show_notes, content, flags=re.DOTALL)
    
    # Write updated content back to file
    with open(file_path, 'w') as file:
        file.write(updated_content)
    
    # Update episode in database
    episode.show_notes = [{"text": item.text, "url": item.url} for item in items]
    
    return episode