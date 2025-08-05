import pytest
from unittest.mock import patch, MagicMock, AsyncMock
from app.models.episode import ProcessingStatus, ShowNotesItem
import tempfile
import os
import json

def test_health_check(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "healthy"}

def test_root(client):
    response = client.get("/")
    assert response.status_code == 200
    assert response.json()["message"] == "Smol Podcaster API"

class TestEpisodesAPI:
    @patch("app.api.v1.episodes.process_episode_task")
    @patch("app.api.v1.episodes.episode_service")
    def test_create_episode_with_url(self, mock_service, mock_task, client):
        mock_episode = MagicMock()
        mock_episode.id = "test-123"
        mock_episode.name = "Test Episode"
        mock_episode.speakers_count = 2
        mock_episode.status = ProcessingStatus.PENDING
        mock_episode.created_at = "2024-01-01T00:00:00"
        mock_episode.updated_at = "2024-01-01T00:00:00"
        
        mock_service.create_episode.return_value = mock_episode
        mock_task.delay.return_value = None
        
        response = client.post(
            "/api/v1/episodes/",
            data={
                "name": "Test Episode",
                "speakers_count": "2",
                "url": "https://example.com/audio.mp3",
                "transcript_only": "false",
                "generate_extra": "false"
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Test Episode"
        assert data["speakers_count"] == 2
    
    @patch("app.api.v1.episodes.episode_service")
    def test_list_episodes(self, mock_service, client):
        mock_episodes = [
            MagicMock(
                id="1",
                name="Episode 1",
                speakers_count=2,
                status=ProcessingStatus.COMPLETED,
                created_at="2024-01-01T00:00:00",
                updated_at="2024-01-01T00:00:00"
            ),
            MagicMock(
                id="2",
                name="Episode 2",
                speakers_count=3,
                status=ProcessingStatus.PROCESSING,
                created_at="2024-01-02T00:00:00",
                updated_at="2024-01-02T00:00:00"
            )
        ]
        mock_service.list_episodes.return_value = mock_episodes
        
        response = client.get("/api/v1/episodes/")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2
        assert data[0]["name"] == "Episode 1"
        assert data[1]["name"] == "Episode 2"

class TestTranscriptsAPI:
    @patch("os.path.exists")
    def test_get_transcript_not_found(self, mock_exists, client):
        mock_exists.return_value = False
        
        response = client.get("/api/v1/transcripts/nonexistent")
        assert response.status_code == 404
        assert response.json()["detail"] == "Transcript not found"
    
    @patch("builtins.open", create=True)
    @patch("os.path.exists")
    def test_get_transcript_success(self, mock_exists, mock_open, client):
        mock_exists.return_value = True
        mock_open.return_value.__enter__.return_value.read.return_value = "Test transcript content"
        
        response = client.get("/api/v1/transcripts/test_episode")
        assert response.status_code == 200
        data = response.json()
        assert data["episode_name"] == "test_episode"
        assert data["transcript"] == "Test transcript content"

class TestProcessingAPI:
    @patch("app.api.v1.processing.AsyncResult")
    def test_get_processing_status_pending(self, mock_async_result, client):
        mock_result = MagicMock()
        mock_result.state = "PENDING"
        mock_result.info = {"episode_id": "test-123"}
        mock_async_result.return_value = mock_result
        
        response = client.get("/api/v1/processing/status/task-123")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == ProcessingStatus.PENDING
        assert data["progress"] == 0
    
    @patch("app.api.v1.processing.AsyncResult")
    def test_get_processing_status_success(self, mock_async_result, client):
        mock_result = MagicMock()
        mock_result.state = "SUCCESS"
        mock_result.info = {"episode_id": "test-123"}
        mock_async_result.return_value = mock_result
        
        response = client.get("/api/v1/processing/status/task-123")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == ProcessingStatus.COMPLETED
        assert data["progress"] == 100

class TestChaptersAPI:
    @patch("app.api.v1.chapters.sync_chapters_task")
    def test_sync_chapters(self, mock_task, client):
        mock_task.delay.return_value = MagicMock(id="task-456")
        
        response = client.post(
            "/api/v1/chapters/sync",
            json={
                "audio_name": "audio_episode",
                "video_name": "video_episode",
                "chapters": "[00:00:00] Introduction\n[00:05:00] Main Topic"
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "Syncing chapters" in data["message"]
        assert data["task_id"] == "task-456"


class TestEpisodesAPIExtended:
    @patch("app.api.v1.episodes.process_episode_task")
    @patch("app.api.v1.episodes.episode_service")
    async def test_create_episode_with_file(self, mock_service, mock_task, client):
        mock_episode = MagicMock()
        mock_episode.id = "test-123"
        mock_episode.name = "Test Episode"
        mock_episode.speakers_count = 2
        mock_episode.status = ProcessingStatus.PENDING
        mock_episode.created_at = "2024-01-01T00:00:00"
        mock_episode.updated_at = "2024-01-01T00:00:00"
        
        mock_service.create_episode = AsyncMock(return_value=mock_episode)
        mock_task.delay.return_value = None
        
        # Create a temporary file to upload
        with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as tmp_file:
            tmp_file.write(b"fake audio content")
            tmp_file_path = tmp_file.name
        
        try:
            with open(tmp_file_path, "rb") as f:
                response = client.post(
                    "/api/v1/episodes/",
                    data={
                        "name": "Test Episode",
                        "speakers_count": "2",
                        "transcript_only": "false",
                        "generate_extra": "true"
                    },
                    files={"file": ("test.mp3", f, "audio/mpeg")}
                )
            
            assert response.status_code == 200
            data = response.json()
            assert data["name"] == "Test Episode"
            mock_task.delay.assert_called_once()
        finally:
            os.unlink(tmp_file_path)
    
    def test_create_episode_missing_file_and_url(self, client):
        response = client.post(
            "/api/v1/episodes/",
            data={
                "name": "Test Episode",
                "speakers_count": "2",
                "transcript_only": "false",
                "generate_extra": "false"
            }
        )
        
        assert response.status_code == 400
        assert "Either file or URL must be provided" in response.json()["detail"]
    
    @patch("app.api.v1.episodes.episode_service")
    async def test_get_episode_not_found(self, mock_service, client):
        mock_service.get_episode = AsyncMock(return_value=None)
        
        response = client.get("/api/v1/episodes/nonexistent-id")
        assert response.status_code == 404
        assert response.json()["detail"] == "Episode not found"
    
    @patch("app.api.v1.episodes.episode_service")
    async def test_get_episode_success(self, mock_service, client):
        mock_episode = MagicMock()
        mock_episode.id = "test-123"
        mock_episode.name = "Test Episode"
        mock_episode.speakers_count = 2
        mock_episode.status = ProcessingStatus.COMPLETED
        mock_episode.created_at = "2024-01-01T00:00:00"
        mock_episode.updated_at = "2024-01-01T00:00:00"
        mock_episode.show_notes = [{"text": "Note 1", "url": "https://example.com"}]
        
        mock_service.get_episode = AsyncMock(return_value=mock_episode)
        
        response = client.get("/api/v1/episodes/test-123")
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == "test-123"
        assert data["name"] == "Test Episode"
        assert len(data["show_notes"]) == 1
    
    @patch("builtins.open", create=True)
    @patch("os.path.exists")
    @patch("app.api.v1.episodes.episode_service")
    async def test_update_show_notes(self, mock_service, mock_exists, mock_open, client):
        mock_episode = MagicMock()
        mock_episode.id = "test-123"
        mock_episode.name = "Test Episode"
        mock_episode.show_notes = []
        
        mock_service.get_episode = AsyncMock(return_value=mock_episode)
        mock_exists.return_value = True
        
        # Mock file read/write
        file_content = "### Show Notes\n- Old Note\n\n### Timestamps\n[00:00:00] Start"
        mock_file = MagicMock()
        mock_file.__enter__.return_value.read.return_value = file_content
        mock_file.__enter__.return_value.write = MagicMock()
        mock_open.return_value = mock_file
        
        response = client.patch(
            "/api/v1/episodes/test-123/show-notes",
            json=[
                {"text": "New Note 1", "url": "https://example1.com"},
                {"text": "New Note 2", "url": None}
            ]
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == "test-123"
        
        # Verify file was written with updated content
        write_calls = mock_file.__enter__.return_value.write.call_args_list
        assert len(write_calls) > 0
        written_content = write_calls[0][0][0]
        assert "New Note 1" in written_content
        assert "New Note 2" in written_content


class TestTranscriptsAPIExtended:
    @patch("json.load")
    @patch("builtins.open", create=True)
    @patch("os.path.exists")
    def test_get_raw_transcript_success(self, mock_exists, mock_open, mock_json_load, client):
        mock_exists.return_value = True
        mock_raw_data = {
            "segments": [
                {"speaker": "SPEAKER 1", "text": "Hello", "start": "0", "end": "5"}
            ]
        }
        mock_json_load.return_value = mock_raw_data
        
        response = client.get("/api/v1/transcripts/test_episode/raw")
        assert response.status_code == 200
        data = response.json()
        assert data["episode_name"] == "test_episode"
        assert data["raw_transcript"]["segments"][0]["text"] == "Hello"
    
    @patch("os.path.exists")
    def test_get_raw_transcript_not_found(self, mock_exists, client):
        mock_exists.return_value = False
        
        response = client.get("/api/v1/transcripts/nonexistent/raw")
        assert response.status_code == 404
        assert response.json()["detail"] == "Raw transcript not found"


class TestProcessingAPIExtended:
    @patch("app.api.v1.processing.AsyncResult")
    def test_get_processing_status_in_progress(self, mock_async_result, client):
        mock_result = MagicMock()
        mock_result.state = "PROGRESS"
        mock_result.info = {
            "episode_id": "test-123",
            "current": "Processing transcript",
            "progress": 50
        }
        mock_async_result.return_value = mock_result
        
        response = client.get("/api/v1/processing/status/task-123")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == ProcessingStatus.PROCESSING
        assert data["progress"] == 50
        assert data["current_step"] == "Processing transcript"
    
    @patch("app.api.v1.processing.AsyncResult")
    def test_get_processing_status_failed(self, mock_async_result, client):
        mock_result = MagicMock()
        mock_result.state = "FAILURE"
        mock_result.info = "Error: API key invalid"
        mock_async_result.return_value = mock_result
        
        response = client.get("/api/v1/processing/status/task-123")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == ProcessingStatus.FAILED
        assert data["error_message"] == "Error: API key invalid"
    
    @patch("app.api.v1.processing.AsyncResult")
    def test_retry_processing_not_failed(self, mock_async_result, client):
        mock_result = MagicMock()
        mock_result.state = "SUCCESS"
        mock_async_result.return_value = mock_result
        
        response = client.post("/api/v1/processing/retry/task-123")
        assert response.status_code == 400
        assert response.json()["detail"] == "Task has not failed"
    
    @patch("app.api.v1.processing.AsyncResult")
    def test_retry_processing_success(self, mock_async_result, client):
        mock_result = MagicMock()
        mock_result.state = "FAILURE"
        mock_result.retry = MagicMock()
        mock_async_result.return_value = mock_result
        
        response = client.post("/api/v1/processing/retry/task-123")
        assert response.status_code == 200
        data = response.json()
        assert data["message"] == "Task retry initiated"
        assert data["task_id"] == "task-123"
        mock_result.retry.assert_called_once()


class TestChaptersAPIExtended:
    def test_sync_chapters_invalid_request(self, client):
        response = client.post(
            "/api/v1/chapters/sync",
            json={
                "audio_name": "",
                "video_name": "video_episode",
                "chapters": "[00:00:00] Introduction"
            }
        )
        
        assert response.status_code == 422  # Validation error
    
    @patch("app.api.v1.chapters.sync_chapters_task")
    def test_sync_chapters_with_empty_chapters(self, mock_task, client):
        mock_task.delay.return_value = MagicMock(id="task-789")
        
        response = client.post(
            "/api/v1/chapters/sync",
            json={
                "audio_name": "audio_episode",
                "video_name": "video_episode", 
                "chapters": ""
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["task_id"] == "task-789"