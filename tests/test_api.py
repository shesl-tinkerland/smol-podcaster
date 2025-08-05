import os
import sys
from pathlib import Path
from fastapi.testclient import TestClient

# Ensure imports resolve when running from this folder
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from api.main import app
import tasks


client = TestClient(app)


def setup_module():
    # Run Celery in eager mode for tests so we don't need a broker
    tasks.app.conf.task_always_eager = True


def test_list_episodes_empty(tmp_path: Path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    (tmp_path / "podcasts-results").mkdir()
    resp = client.get("/episodes")
    assert resp.status_code == 200
    assert resp.json() == []


def test_process_starts_task(monkeypatch, tmp_path: Path):
    monkeypatch.chdir(tmp_path)

    # Monkeypatch the Celery task to avoid external calls
    called = {}

    def fake_main(url, name, speakers, transcript_only, generate_extra):
        called.update({
            "url": url,
            "name": name,
            "speakers": speakers,
            "transcript_only": transcript_only,
            "generate_extra": generate_extra,
        })
        return str(tmp_path / f"podcasts-results/{name}.md")

    monkeypatch.setattr(tasks.smol_podcaster, "main", fake_main)

    resp = client.post(
        "/process",
        data={
            "url": "https://example.com/audio.mp3",
            "speakers": 2,
            "name": "ep1",
            "transcript_only": False,
            "generate_extra": False,
        },
    )
    assert resp.status_code == 200
    data = resp.json()
    assert "task_id" in data
    # And our fake got called
    assert called["name"] == "ep1"


def test_update_and_get_show_notes(monkeypatch, tmp_path: Path):
    monkeypatch.chdir(tmp_path)
    (tmp_path / "podcasts-results").mkdir()
    file_path = tmp_path / "podcasts-results/substack_ep1.md"
    file_path.write_text("### Show Notes\n- a\n\n### Timestamps\n- [00:00:00] t\n\n### Transcript\n...")

    # Update
    resp = client.put("/episodes/ep1/show_notes", json={
        "items": [
            {"label": "Item 1", "url": "https://x"},
            {"label": "Item 2"},
        ]
    })
    assert resp.status_code == 200

    # Fetch
    resp = client.get("/episodes/ep1/show_notes")
    assert resp.status_code == 200
    items = resp.json()
    assert items == [
        {"label": "Item 1", "url": "https://x"},
        {"label": "Item 2", "url": None},
    ]
