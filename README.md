# smol-podcaster

![Screenshot](screenshots/main.png)

We use smol-podcaster to take care of most of [Latent Space](https://latent.space) transcription work. What it will do for you:

- Generate a clean, diarized transcript of the podcast with speaker labels and timestamps
- Generate a list of chapters with timestamps for the episode
- Give you title ideas based on previous ones (modify the prompt to give examples of your own, it comes with Latent Space ones)
- Give you ideas for tweets to announce the podcast

### Environment Setup

Activate virtualenv with

`source venv/bin/activate`

Install dependencies with

`pip install -r requirements.txt`

Make a copy of the `.env.sample` and replace it with your keys:

`mv .env.sample .env`

### Run with web UI + background runs

The app now uses a FastAPI backend and a Next.js frontend, with Celery for background processing. You will need a Celery broker ([RabbitMQ](https://docs.celeryq.dev/en/stable/getting-started/backends-and-brokers/rabbitmq.html)) reachable at the URL in `celeryconfig.py`.

- Option A: start backend API + worker via Procfile (honcho)

```
cd smol-podcaster
honcho start
```

This starts:
- API: `uvicorn api.main:app` on `${PORT:-8000}`
- Worker: `celery -A tasks worker ...`

- Option B: start them manually

```
# Terminal 1 – Celery worker
cd smol-podcaster
celery -A tasks worker --loglevel=INFO -E -n smol_podcaster@%h

# Terminal 2 – FastAPI
cd smol-podcaster
uvicorn api.main:app --host 0.0.0.0 --port 8000
```

Frontend (Next.js):

```
cd frontend
npm install
export NEXT_PUBLIC_API_BASE_URL=http://localhost:8000
npm run dev
```

Open http://localhost:3000 and use the UI. Generated files are saved under `./podcasts-results` and `./podcasts-clean-transcripts`.

### Run from CLI

To run:

`python smol_podcaster.py AUDIO_FILE_URL GUEST_NAME NUMBER_OF_SPEAKERS`

The URL needs to be a direct download link, it can't be a GDrive. For files <100MB you can use [tmpfiles.org](https://tmpfiles.org/) (e.g. `https://tmpfiles.org/dl/4338258/audio.mp3`), otherwise Dropbox. For example: 

`python smol_podcaster.py "https://dl.dropboxusercontent.com/XXXX" "Tianqi" 3`  

Or, if you want to use a local file (with absolute or relative paths), use the following:
```
python smol_podcaster.py audio_sample.mp3 "test" 1
```
Or, use `~/Downloads/audio_sample.mp3` for file.

The script will automatically switch https://www.dropbox.com to https://dl.dropboxusercontent.com in the link.

Optional flags:

- `--transcript_only` will generate only the transcript without any of the show notes
- `--generate_extra` will also create tweets and title ideas

### Audio / Video Sync

If you use smol-podcaster to transcribe both your audio and video files, you can create chapters based on your audio ones, put them in the form, and create a new list that matches the video transcript for YouTube. Usually audio and video have different lengths because less pauses are edited, so re-using the audio timestamps in the video doesn't work.

For example:

Timestamp:
`[00:10:00] Talking about Latent Space`

Audio Transcript:
`[00:10:00] We love talking about Latent Space`

Video Transcript:
`[00:12:05] We love talking about Latent Space`

Will return you new chapters where the timestamp would be
`[00:12:05] Talking about Latent Space`

This is based on string similarity, not hard-matching so don't worry about Whisper's mistakes.


### Edit Show Notes

Each run generates a set of show notes from both OAI and Claude. The easiest way to consolidate them is the "Edit Show Notes" feature. Simply click "Edit Episode" to see a list of them, and then make the edits you need.

![Screenshot](screenshots/edit.png)

![Screenshot](screenshots/edit-full.png)

After you're done editing, press "Save Changes" and it will rewrite the Markdown in your file to show the new cleaned and merged list.

# API quick start

Basic endpoints (served by FastAPI):

- `POST /process` (multipart): fields `file_input` (file) or `url` (string), `speakers` (int), `name` (str), optional `transcript_only` (bool), `generate_extra` (bool). Returns `{ task_id }`.
- `POST /sync_chapters` (json): `{ video_name, audio_name, chapters }`. Returns `{ task_id }`.
- `GET /episodes`: lists available episodes.
- `GET /episodes/{name}/show_notes` and `PUT /episodes/{name}/show_notes` to fetch/update show notes.
- `GET /tasks/{task_id}`: Celery task status/result.

Example (curl):

```
curl -F url=https://example.com/audio.mp3 \
     -F speakers=2 \
     -F name=episode1 \
     http://localhost:8000/process
```

### Testing

Backend tests live under `smol-podcaster/tests`.

```
cd smol-podcaster
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements-dev.txt
pytest -q
```

Note: for full production dependencies (`requirements.txt`) prefer Python 3.11/3.12 to avoid heavy wheel builds on some platforms.

# License

MIT License
