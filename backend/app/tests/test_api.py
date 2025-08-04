import pytest
from unittest.mock import patch, MagicMock
from app.models.episode import ProcessingStatus

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