import os
import json
import shutil
import sys
from pathlib import Path

# Ensure module import from project root
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import smol_podcaster as core


def test_process_transcript_formats_and_writes(tmp_path: Path):
    # Arrange
    os.chdir(tmp_path)
    (tmp_path / "podcasts-clean-transcripts").mkdir(parents=True, exist_ok=True)

    transcript = [
        {"end": "10", "text": " Hello world.", "start": "0", "speaker": "SPEAKER 1"},
        {"end": "20", "text": " Second line.", "start": "12", "speaker": "SPEAKER 2"},
    ]

    # Act
    out = core.process_transcript(transcript, "episode1")

    # Assert
    assert "**SPEAKER 1** [00:00:00]:  Hello world." in out
    assert "**SPEAKER 2** [00:00:12]:  Second line." in out

    file_path = tmp_path / "podcasts-clean-transcripts/episode1.md"
    assert file_path.exists()
    assert file_path.read_text() == out


def test_update_video_chapters_inserts_above_substack(tmp_path: Path):
    os.chdir(tmp_path)
    (tmp_path / "podcasts-clean-transcripts").mkdir(parents=True, exist_ok=True)
    (tmp_path / "podcasts-results").mkdir(parents=True, exist_ok=True)

    (tmp_path / "podcasts-clean-transcripts/audio.md").write_text("**S** [00:00:01]: a\n**S** [00:01:00]: b")
    (tmp_path / "podcasts-clean-transcripts/video.md").write_text("**S** [00:00:00]: x\n**S** [00:01:01]: y")
    (tmp_path / "podcasts-results/substack_audio.md").write_text("### Show Notes\n- a\n\n### Timestamps\n- [00:00:00] t\n\n### Transcript\n...")

    updated = core.update_video_chapters("[00:01:00] Topic 1\n", "audio", "video")
    assert "[00:01:01] Topic 1" in updated
    # Ensure file got updated at the top
    content = (tmp_path / "podcasts-results/substack_audio.md").read_text()
    assert content.startswith("[00:01:01] Topic 1\n\n### Show Notes")
