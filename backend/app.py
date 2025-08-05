import os
import re
from datetime import datetime
from typing import List, Optional

from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from .celery_app import celery_app

PODCAST_RESULTS_DIR = './podcasts-results'

app = FastAPI(title="Smol Podcaster API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class Episode(BaseModel):
    name: str
    created_at: datetime
    created_at_formatted: str


class ProcessRequest(BaseModel):
    url: Optional[str] = None
    name: str
    speakers: int
    transcript_only: bool = False
    generate_extra: bool = False


class EditItem(BaseModel):
    text: str
    url: Optional[str] = None


class EditShowNotesRequest(BaseModel):
    items: List[EditItem]


class TranscriptBody(BaseModel):
    transcript: str


class WriteupBody(BaseModel):
    writeup: str


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/episodes", response_model=List[Episode])
def list_episodes():
    episodes: List[Episode] = []

    if os.path.exists(PODCAST_RESULTS_DIR):
        for filename in os.listdir(PODCAST_RESULTS_DIR):
            if filename.startswith('substack_') and filename.endswith('.md'):
                file_path = os.path.join(PODCAST_RESULTS_DIR, filename)
                episode_name = filename[len('substack_'):-3]
                creation_time = datetime.fromtimestamp(os.path.getctime(file_path))
                episodes.append(Episode(
                    name=episode_name,
                    created_at=creation_time,
                    created_at_formatted=creation_time.strftime("%b %-d"),
                ))

    episodes.sort(key=lambda x: x.created_at, reverse=True)
    return episodes


@app.post("/process")
def process_job(body: ProcessRequest):
    file_or_url = body.url
    if not file_or_url:
        raise HTTPException(status_code=400, detail="url is required if no file upload is provided")

    task = celery_app.send_task(
        'tasks.run_smol_podcaster',
        args=[file_or_url, body.name, body.speakers, body.transcript_only, body.generate_extra]
    )
    return {"task_id": task.id}


@app.post("/process/upload")
async def process_job_upload(
    file: UploadFile = File(...),
    name: str = Form(...),
    speakers: int = Form(...),
    transcript_only: bool = Form(False),
    generate_extra: bool = Form(False),
):
    # Save uploaded file to a temp location, then reuse existing upload handler
    import tempfile
    from werkzeug.utils import secure_filename

    _, file_extension = os.path.splitext(file.filename)
    temp_dir = tempfile.gettempdir()
    temp_file_path = os.path.join(temp_dir, secure_filename(f"upload_{name}{file_extension}"))

    with open(temp_file_path, 'wb') as out:
        content = await file.read()
        out.write(content)

    file_or_url = temp_file_path

    task = celery_app.send_task(
        'tasks.run_smol_podcaster',
        args=[file_or_url, name, speakers, transcript_only, generate_extra]
    )
    return {"task_id": task.id}


@app.post("/sync_chapters")
def sync_chapters(video_name: str, audio_name: str, chapters: str):
    task = celery_app.send_task(
        'tasks.run_video_chapters',
        args=[chapters, audio_name, video_name]
    )
    return {"task_id": task.id}


@app.get("/episodes/{episode_name}/show-notes")
def get_show_notes(episode_name: str):
    file_path = os.path.join(PODCAST_RESULTS_DIR, f'substack_{episode_name}.md')
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="Episode not found")

    with open(file_path, 'r') as f:
        content = f.read()

    show_notes_pattern = r'### Show Notes(.*?)(?=### Timestamps)'
    show_notes_match = re.search(show_notes_pattern, content, re.DOTALL)
    items: List[EditItem] = []

    if show_notes_match:
        show_notes = show_notes_match.group(1).strip()
        parsed = re.findall(r'^-\s*(?:\[([^\]]+)\]\(([^)]+)\)|(.+))$', show_notes, re.MULTILINE)
        for p in parsed:
            text = p[0] or p[2]
            url = p[1] or None
            items.append(EditItem(text=text, url=url))

    return {"items": [i.dict() for i in items]}


@app.put("/episodes/{episode_name}/show-notes")
def update_show_notes(episode_name: str, body: EditShowNotesRequest):
    file_path = os.path.join(PODCAST_RESULTS_DIR, f'substack_{episode_name}.md')
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="Episode not found")

    with open(file_path, 'r') as f:
        content = f.read()

    show_notes_pattern = r'### Show Notes.*?(?=### Timestamps)'
    lines = [f"- {i.text}" if not i.url else f"- [{i.text}]({i.url})" for i in body.items]
    updated_show_notes = "### Show Notes\n" + "\n".join(lines)
    updated_content = re.sub(show_notes_pattern, updated_show_notes, content, flags=re.DOTALL)

    with open(file_path, 'w') as f:
        f.write(updated_content)

    return JSONResponse(status_code=204, content=None)


# Modular pipeline endpoints


@app.post("/pipeline/chapters")
def pipeline_chapters(body: TranscriptBody):
    # lazy import to avoid heavy deps at import time
    import smol_podcaster as sp
    return {"chapters": sp.create_chapters(body.transcript)}


@app.post("/pipeline/show-notes")
def pipeline_show_notes(body: TranscriptBody):
    import smol_podcaster as sp
    return {"show_notes": sp.create_show_notes(body.transcript)}


@app.post("/pipeline/writeup")
def pipeline_writeup(body: TranscriptBody):
    import smol_podcaster as sp
    return {"writeup": sp.create_writeup(body.transcript)}


@app.post("/pipeline/title-suggestions")
def pipeline_titles(body: WriteupBody):
    import smol_podcaster as sp
    return {"titles": sp.title_suggestions(body.writeup)}


@app.post("/pipeline/tweet-suggestions")
def pipeline_tweets(body: TranscriptBody):
    import smol_podcaster as sp
    return {"tweets": sp.tweet_suggestions(body.transcript)}
