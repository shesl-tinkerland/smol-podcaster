from fastapi import APIRouter, HTTPException
from typing import Dict
import os
from app.core.config import settings

router = APIRouter()

@router.get("/{episode_name}")
async def get_transcript(episode_name: str) -> Dict[str, str]:
    transcript_path = os.path.join(settings.TRANSCRIPTS_DIR, f"{episode_name}.md")
    
    if not os.path.exists(transcript_path):
        raise HTTPException(status_code=404, detail="Transcript not found")
    
    with open(transcript_path, 'r') as f:
        content = f.read()
    
    return {
        "episode_name": episode_name,
        "transcript": content
    }

@router.get("/{episode_name}/raw")
async def get_raw_transcript(episode_name: str) -> Dict:
    raw_path = os.path.join(settings.RAW_TRANSCRIPTS_DIR, f"{episode_name}.json")
    
    if not os.path.exists(raw_path):
        raise HTTPException(status_code=404, detail="Raw transcript not found")
    
    import json
    with open(raw_path, 'r') as f:
        content = json.load(f)
    
    return {
        "episode_name": episode_name,
        "raw_transcript": content
    }