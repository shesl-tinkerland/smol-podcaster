import os
import re
import tempfile
from datetime import datetime
from typing import List, Optional

from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from celery.result import AsyncResult

# Import Celery app and tasks
from tasks import app as celery_app
from tasks import run_smol_podcaster, run_video_chapters

app = FastAPI(title="Smol Podcaster API", version="1.0.0")

# CORS
frontend_origin = os.environ.get("FRONTEND_ORIGIN", "http://localhost:3000")
app.add_middleware(
    CORSMiddleware,
    allow_origins=[frontend_origin, "*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def root():
    return {
        "status": "ok",
        "name": "Smol Podcaster API",
        "version": "1.0.0",
        "docs": "/docs",
        "openapi": "/openapi.json",
    }


class ProcessResponse(BaseModel):
    task_id: str


class SyncChaptersRequest(BaseModel):
    video_name: str
    audio_name: str
    chapters: str


class Episode(BaseModel):
    name: str
    created_at: float
    created_at_formatted: str


class ShowNoteItem(BaseModel):
    label: str
    url: Optional[str] = None


class UpdateShowNotesRequest(BaseModel):
    items: List[ShowNoteItem]


@app.post("/process", response_model=ProcessResponse)
async def process(
    file_input: Optional[UploadFile] = File(None),
    url: Optional[str] = Form(None),
    speakers: int = Form(...),
    name: str = Form(...),
    transcript_only: bool = Form(False),
    generate_extra: bool = Form(False),
):
    if not file_input and not url:
        raise HTTPException(status_code=400, detail="Either file_input or url must be provided")

    file_or_url = url
    if file_input is not None:
        # Save the uploaded file to a temporary location
        _, file_extension = os.path.splitext(file_input.filename)
        temp_dir = tempfile.gettempdir()
        temp_file_path = os.path.join(temp_dir, f"upload_{name}{file_extension}")
        with open(temp_file_path, "wb") as f:
            f.write(await file_input.read())
        file_or_url = temp_file_path

    task = run_smol_podcaster.delay(file_or_url, name, int(speakers), bool(transcript_only), bool(generate_extra))
    return ProcessResponse(task_id=task.id)


@app.post("/sync_chapters", response_model=ProcessResponse)
async def sync_chapters(payload: SyncChaptersRequest):
    task = run_video_chapters.delay(payload.chapters, payload.audio_name, payload.video_name)
    return ProcessResponse(task_id=task.id)


@app.get("/tasks/{task_id}")
async def get_task_status(task_id: str):
    result = AsyncResult(task_id, app=celery_app)
    return JSONResponse({
        "task_id": task_id,
        "state": result.state,
        "result": result.result if result.ready() else None,
    })


@app.get("/episodes", response_model=List[Episode])
async def list_episodes():
    podcast_results_dir = './podcasts-results'
    episodes: List[Episode] = []

    if os.path.exists(podcast_results_dir):
        for filename in os.listdir(podcast_results_dir):
            if filename.startswith('substack_') and filename.endswith('.md'):
                file_path = os.path.join(podcast_results_dir, filename)
                episode_name = filename[len('substack_'):-3]
                creation_time = os.path.getctime(file_path)
                episodes.append(Episode(
                    name=episode_name,
                    created_at=creation_time,
                    created_at_formatted=datetime.fromtimestamp(creation_time).strftime("%b %-d"),
                ))

    # Sort by creation time desc
    episodes.sort(key=lambda x: x.created_at, reverse=True)
    return episodes


@app.get("/episodes/{episode_name}/content")
async def get_episode_content(episode_name: str):
    file_path = os.path.join('./podcasts-results', f'substack_{episode_name}.md')
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="Episode not found")

    with open(file_path, 'r') as f:
        content = f.read()
    return JSONResponse({"content": content})


@app.get("/episodes/{episode_name}/show_notes", response_model=List[ShowNoteItem])
async def get_show_notes(episode_name: str):
    file_path = os.path.join('./podcasts-results', f'substack_{episode_name}.md')
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="Episode not found")

    with open(file_path, 'r') as f:
        content = f.read()

    show_notes_pattern = r'### Show Notes(.*?)(?=### Timestamps)'
    match = re.search(show_notes_pattern, content, re.DOTALL)
    items: List[ShowNoteItem] = []
    if match:
        section = match.group(1).strip()
        for m in re.finditer(r'^-\s*(?:\[([^\]]+)\]\(([^)]+)\)|(.+))$', section, re.MULTILINE):
            label = m.group(1) or m.group(3)
            url = m.group(2) or None
            if label:
                items.append(ShowNoteItem(label=label, url=url))

    return items


@app.put("/episodes/{episode_name}/show_notes")
async def update_show_notes(episode_name: str, payload: UpdateShowNotesRequest):
    file_path = os.path.join('./podcasts-results', f'substack_{episode_name}.md')
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="Episode not found")

    with open(file_path, 'r') as f:
        content = f.read()

    show_notes_pattern = r'### Show Notes.*?(?=### Timestamps)'
    updated_show_notes_lines = []
    updated_show_notes_lines.append("### Show Notes")
    for item in payload.items:
        if item.url:
            updated_show_notes_lines.append(f"- [{item.label}]({item.url})")
        else:
            updated_show_notes_lines.append(f"- {item.label}")
    updated_show_notes = "\n".join(updated_show_notes_lines)

    updated_content = re.sub(show_notes_pattern, updated_show_notes, content, flags=re.DOTALL)

    with open(file_path, 'w') as f:
        f.write(updated_content)

    return JSONResponse({"ok": True})
