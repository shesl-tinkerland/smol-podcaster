---
name: Smol Podcaster
description: |
  Produce podcast post-production assets — diarized transcripts, chapters,
  show notes, title ideas, tweet drafts — from a single audio file using
  Whisper transcription and multi-LLM generation.
---

# Smol Podcaster

Help the user run [smol-podcaster](https://github.com/FanaHOVA/smol-podcaster),
an AI-powered podcast production CLI that automates post-production from a
single audio file: speaker-diarized transcripts with timestamps, chapter
lists, show notes with entity links, long-form writeups, title suggestions,
and social media drafts.

Provenance: this skill was shaped from the public repository
`https://github.com/FanaHOVA/smol-podcaster` (413 stars, MIT license,
Python CLI + Flask web UI). Originally built for the Latent Space podcast.

## When to use this skill

- The user has a podcast episode audio file and wants a complete
  post-production package (transcript, chapters, show notes, titles, tweets).
- The user needs a diarized transcript with speaker labels and timestamps
  from a multi-speaker recording.
- The user wants chapter markers with timestamps for a podcast episode.
- The user wants AI-generated title options, tweet drafts, or show notes
  with linked entity references.
- The user wants to set up the smol-podcaster CLI or web UI locally.

## Required inputs

- **Audio source**: a direct-download URL or local file path to the episode
  audio (MP3, WAV, etc.). Dropbox links are auto-converted; Google Drive
  links are not supported.
- **Guest name(s)**: speaker names for the transcript labels.
- **Speaker count**: number of distinct speakers in the episode (default 3).

## Workflow

### 1. Environment setup

1. Clone the repository:
   `git clone https://github.com/FanaHOVA/smol-podcaster.git`
2. Create and activate a virtual environment:
   `python -m venv venv && source venv/bin/activate`
3. Install dependencies: `pip install -r requirements.txt`
4. Copy `.env.sample` to `.env` and populate API keys (OpenAI, Anthropic).

### 2. Transcription

Run the CLI with the audio source:

```
python smol_podcaster.py <audio_url_or_path> "<guest_name>" <speaker_count>
```

Flags:
- `--transcript_only` — generate only the diarized transcript, skip AI
  content generation.
- `--generate_extra` — also produce title suggestions and tweet drafts.

The pipeline:
1. Uploads local files to tmpfiles.org if needed.
2. Sends audio to Replicate's Whisper Diarization model for
   speaker-labeled, timestamped transcription.
3. Saves raw JSON to `./podcasts-raw-transcripts/`.
4. Cleans and formats the transcript as Markdown with `[HH:MM:SS]`
   timestamps and speaker labels → `./podcasts-clean-transcripts/<name>.md`.

### 3. AI content generation

Unless `--transcript_only` is set, the pipeline generates:

| Asset | Method | Output |
|---|---|---|
| **Chapters** | Claude + GPT dual-generation | `[HH:MM:SS] Topic name` list |
| **Show notes** | Entity extraction with linked references | Companies, people, papers, projects |
| **Writeup** | Bullet points + 4–5 analytical paragraphs | Core episode concepts |
| **Clip suggestions** | 7–8 insightful/funny/controversial passages | YouTube Shorts candidates |
| **Title suggestions** | 8 options matching podcast style (with `--generate_extra`) | Episode title ideas |
| **Tweet drafts** | 8 posts in concise literary style (with `--generate_extra`) | Social announcements |

All generated content is saved to `./podcasts-results/<name>.md`.
A combined Substack-ready file is also produced at
`./podcasts-results/substack_<name>.md`.

### 4. Web UI (optional)

For a browser-based workflow with background processing:

1. Install RabbitMQ (required as Celery broker).
2. Start all services: `honcho start`
   Or manually: `celery -A tasks worker --loglevel=INFO` and
   `flask --app web.py --debug run`.
3. Access at `http://localhost:5000`.

### 5. Video chapter mapping

When a separate video transcript exists (e.g., from YouTube), the tool can
map audio chapter timestamps to video timestamps using Levenshtein distance
matching, compensating for timing differences between audio and video edits.

## Output

Provide the user with:
- Guidance on CLI arguments and flags for their specific episode.
- Troubleshooting for API key setup, file upload issues, or diarization
  quality.
- Advice on choosing between transcript-only and full generation modes.
- Tips for improving speaker diarization accuracy (correct speaker count,
  audio quality).
- Help interpreting and editing the generated chapters, show notes, and
  writeup.

## Key references

- Repository: <https://github.com/FanaHOVA/smol-podcaster>
- README: <https://github.com/FanaHOVA/smol-podcaster/blob/main/README.md>
- Main script: <https://github.com/FanaHOVA/smol-podcaster/blob/main/smol_podcaster.py>
- Web UI: <https://github.com/FanaHOVA/smol-podcaster/blob/main/web.py>
- Environment sample: <https://github.com/FanaHOVA/smol-podcaster/blob/main/.env.sample>
