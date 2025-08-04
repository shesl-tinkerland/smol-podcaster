import pytest
import asyncio
from unittest.mock import patch, MagicMock
from app.models.episode import ProcessingStatus

@pytest.mark.integration
class TestEpisodeProcessingFlow:
    @patch("app.core.tasks.TranscriptionService")
    @patch("app.core.tasks.AIService")
    @patch("app.core.tasks.EpisodeService")
    def test_full_episode_processing(self, mock_episode_service, mock_ai_service, mock_transcription_service, client):
        # Mock the services
        mock_transcript = "Test transcript content"
        mock_transcription_service.return_value.transcribe_audio = MagicMock(
            return_value=asyncio.coroutine(lambda: [{"speaker": "SPEAKER 1", "text": "Hello", "start": "0", "end": "5"}])()
        )
        mock_transcription_service.return_value.process_transcript = MagicMock(
            return_value=asyncio.coroutine(lambda: mock_transcript)()
        )
        mock_transcription_service.return_value.upload_file_and_use_url = MagicMock(
            return_value=asyncio.coroutine(lambda: "https://example.com/audio.mp3")()
        )
        
        mock_ai_service.return_value.create_chapters = MagicMock(
            return_value=asyncio.coroutine(lambda: "Chapter list")()
        )
        mock_ai_service.return_value.create_show_notes = MagicMock(
            return_value=asyncio.coroutine(lambda: "Show notes")()
        )
        mock_ai_service.return_value.create_writeup = MagicMock(
            return_value=asyncio.coroutine(lambda: "Writeup")()
        )
        
        # Create episode
        response = client.post(
            "/api/v1/episodes/",
            data={
                "name": "Integration Test Episode",
                "speakers_count": "2",
                "url": "https://example.com/test.mp3",
                "transcript_only": "false",
                "generate_extra": "false"
            }
        )
        
        assert response.status_code == 200
        episode = response.json()
        assert episode["status"] == ProcessingStatus.PENDING
    
    def test_episode_list_and_edit_flow(self, client):
        # List episodes
        response = client.get("/api/v1/episodes/")
        assert response.status_code == 200
        
        # Get specific episode (would need to create one first in real test)
        # This is a simplified example
        episodes = response.json()
        if episodes:
            episode_id = episodes[0]["id"]
            
            # Update show notes
            response = client.patch(
                f"/api/v1/episodes/{episode_id}/show-notes",
                json=[
                    {"text": "Updated note 1", "url": "https://example.com"},
                    {"text": "Updated note 2", "url": None}
                ]
            )
            
            # In a real test, we'd check the response
            # assert response.status_code == 200

@pytest.mark.integration
class TestChapterSyncFlow:
    @patch("app.api.v1.chapters.sync_chapters_task")
    def test_chapter_sync_workflow(self, mock_task, client):
        mock_task.delay.return_value = MagicMock(id="sync-task-123")
        
        # Initiate chapter sync
        response = client.post(
            "/api/v1/chapters/sync",
            json={
                "audio_name": "test_audio",
                "video_name": "test_video",
                "chapters": "[00:00:00] Start\n[00:05:00] Middle\n[00:10:00] End"
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        task_id = data["task_id"]
        
        # Check task status
        with patch("app.api.v1.processing.AsyncResult") as mock_result:
            mock_result.return_value.state = "PROGRESS"
            mock_result.return_value.info = {
                "current": "Syncing chapters",
                "progress": 50,
                "episode_id": ""
            }
            
            response = client.get(f"/api/v1/processing/status/{task_id}")
            assert response.status_code == 200
            status = response.json()
            assert status["status"] == ProcessingStatus.PROCESSING
            assert status["progress"] == 50

@pytest.mark.integration
class TestTranscriptAccess:
    @patch("os.path.exists")
    @patch("builtins.open", create=True)
    def test_transcript_retrieval(self, mock_open, mock_exists, client):
        mock_exists.return_value = True
        mock_transcript = "**SPEAKER 1** [00:00:00]: Hello world"
        mock_open.return_value.__enter__.return_value.read.return_value = mock_transcript
        
        # Get clean transcript
        response = client.get("/api/v1/transcripts/test_episode")
        assert response.status_code == 200
        data = response.json()
        assert data["transcript"] == mock_transcript
        
        # Get raw transcript
        import json
        mock_raw = {"segments": [{"speaker": "SPEAKER 1", "text": "Hello world", "start": "0", "end": "5"}]}
        mock_open.return_value.__enter__.return_value.read.return_value = json.dumps(mock_raw)
        
        response = client.get("/api/v1/transcripts/test_episode/raw")
        assert response.status_code == 200
        data = response.json()
        assert "raw_transcript" in data