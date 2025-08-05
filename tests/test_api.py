import os
import shutil
from pathlib import Path

from fastapi.testclient import TestClient

from backend.app import app

client = TestClient(app)

BASE_DIR = Path(__file__).resolve().parents[1]
RESULTS_DIR = BASE_DIR / 'podcasts-results'


def setup_module(module):
    RESULTS_DIR.mkdir(exist_ok=True)


def teardown_module(module):
    # leave artifacts for manual inspection if needed
    pass


def test_health():
    resp = client.get('/health')
    assert resp.status_code == 200
    assert resp.json()['status'] == 'ok'


def test_list_episodes_and_show_notes_roundtrip(tmp_path):
    name = 'episode_test'
    file_path = RESULTS_DIR / f'substack_{name}.md'
    content = (
        "### Show Notes\n"
        "- Item A\n"
        "- [Item B](https://example.com)\n\n"
        "### Timestamps\n"
        "- [00:00:00] Start\n"
    )
    file_path.write_text(content)

    # list episodes
    resp = client.get('/episodes')
    assert resp.status_code == 200
    episodes = resp.json()
    assert any(e['name'] == name for e in episodes)

    # get show notes
    resp = client.get(f'/episodes/{name}/show-notes')
    assert resp.status_code == 200
    items = resp.json()['items']
    assert {'text': 'Item A', 'url': None} in items
    assert {'text': 'Item B', 'url': 'https://example.com'} in items

    # update show notes
    new_items = {
        'items': [
            {'text': 'New A', 'url': None},
            {'text': 'New B', 'url': 'https://b.example'},
        ]
    }
    resp = client.put(f'/episodes/{name}/show-notes', json=new_items)
    assert resp.status_code == 204

    updated = file_path.read_text()
    assert '### Show Notes' in updated
    assert '- New A' in updated
    assert '- [New B](https://b.example)' in updated


def test_process_triggers_celery(monkeypatch):
    calls = {}

    class DummyResult:
        def __init__(self, id):
            self.id = id

    def fake_send_task(task_name, args):
        calls['task_name'] = task_name
        calls['args'] = args
        return DummyResult('123')

    from backend import app as backend_app
    monkeypatch.setattr(backend_app, 'celery_app', type('X', (), {'send_task': staticmethod(fake_send_task)}))

    body = {
        'url': 'https://example.com/file.mp3',
        'name': 'job1',
        'speakers': 2,
        'transcript_only': True,
        'generate_extra': False,
    }
    resp = client.post('/process', json=body)
    assert resp.status_code == 200
    assert resp.json()['task_id'] == '123'
    assert calls['task_name'] == 'tasks.run_smol_podcaster'
    assert calls['args'][0] == 'https://example.com/file.mp3'
