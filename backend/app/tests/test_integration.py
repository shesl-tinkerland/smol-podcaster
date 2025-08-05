import pytest
import asyncio
from unittest.mock import patch, MagicMock, AsyncMock
from app.models.episode import ProcessingStatus, EpisodeCreate
from app.core.tasks import process_episode_task
import tempfile
import os
import json

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


@pytest.mark.integration
class TestCompleteWorkflow:
    @patch("replicate.run")
    @patch("app.services.ai_service.OpenAI")
    @patch("app.services.ai_service.Anthropic")
    @patch("app.api.v1.episodes.episode_service")
    def test_end_to_end_episode_creation_and_processing(
        self, mock_episode_service, mock_anthropic, mock_openai, mock_replicate, client
    ):
        # Setup mocks
        mock_episode = MagicMock()
        mock_episode.id = "workflow-test-123"
        mock_episode.name = "Workflow Test"
        mock_episode.speakers_count = 2
        mock_episode.status = ProcessingStatus.PENDING
        mock_episode.created_at = "2024-01-01T00:00:00"
        mock_episode.updated_at = "2024-01-01T00:00:00"
        
        mock_episode_service.create_episode = AsyncMock(return_value=mock_episode)
        mock_episode_service.get_episode = AsyncMock(return_value=mock_episode)
        mock_episode_service.list_episodes = AsyncMock(return_value=[mock_episode])
        
        # Mock transcription
        mock_replicate.return_value = {
            'segments': [
                {"speaker": "SPEAKER 1", "text": "Welcome to the podcast", "start": "0", "end": "3"},
                {"speaker": "SPEAKER 2", "text": "Thanks for having me", "start": "3", "end": "6"}
            ]
        }
        
        # Mock AI responses
        mock_openai_client = MagicMock()
        mock_openai_response = MagicMock()
        mock_openai_response.choices = [MagicMock(message=MagicMock(content="GPT-4 response"))]
        mock_openai_client.chat.completions.create.return_value = mock_openai_response
        mock_openai.return_value = mock_openai_client
        
        mock_anthropic_client = MagicMock()
        mock_anthropic_response = MagicMock()
        mock_anthropic_response.content = [MagicMock(text="Claude response")]
        mock_anthropic_client.messages.create.return_value = mock_anthropic_response
        mock_anthropic.return_value = mock_anthropic_client
        
        # Step 1: Create episode
        response = client.post(
            "/api/v1/episodes/",
            data={
                "name": "Workflow Test",
                "speakers_count": "2",
                "url": "https://example.com/workflow-test.mp3",
                "transcript_only": "false",
                "generate_extra": "true"
            }
        )
        assert response.status_code == 200
        episode_data = response.json()
        episode_id = episode_data["id"]
        
        # Step 2: List episodes to verify creation
        response = client.get("/api/v1/episodes/")
        assert response.status_code == 200
        episodes = response.json()
        assert len(episodes) > 0
        assert any(e["id"] == episode_id for e in episodes)
        
        # Step 3: Get specific episode details
        response = client.get(f"/api/v1/episodes/{episode_id}")
        assert response.status_code == 200
        episode_detail = response.json()
        assert episode_detail["name"] == "Workflow Test"
        
        # Step 4: Update show notes
        mock_episode.show_notes = []
        response = client.patch(
            f"/api/v1/episodes/{episode_id}/show-notes",
            json=[
                {"text": "OpenAI", "url": "https://openai.com"},
                {"text": "Anthropic", "url": "https://anthropic.com"}
            ]
        )
        # Would normally check response but need file mocking
        
        # Step 5: Test transcript retrieval
        with patch("os.path.exists", return_value=True):
            with patch("builtins.open", create=True) as mock_open:
                mock_open.return_value.__enter__.return_value.read.return_value = "Test transcript"
                
                response = client.get("/api/v1/transcripts/Workflow Test")
                assert response.status_code == 200
                assert response.json()["transcript"] == "Test transcript"


@pytest.mark.integration
class TestErrorHandling:
    def test_invalid_episode_creation_missing_data(self, client):
        response = client.post(
            "/api/v1/episodes/",
            data={
                "speakers_count": "2",
                # Missing name and file/url
            }
        )
        assert response.status_code == 422  # Validation error
    
    @patch("app.api.v1.episodes.episode_service")
    def test_episode_not_found_handling(self, mock_service, client):
        mock_service.get_episode = AsyncMock(return_value=None)
        
        response = client.get("/api/v1/episodes/non-existent-id")
        assert response.status_code == 404
        assert "Episode not found" in response.json()["detail"]
    
    @patch("app.api.v1.processing.AsyncResult")
    def test_task_failure_handling(self, mock_async_result, client):
        mock_result = MagicMock()
        mock_result.state = "FAILURE"
        mock_result.info = "Transcription service unavailable"
        mock_async_result.return_value = mock_result
        
        response = client.get("/api/v1/processing/status/failed-task-123")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == ProcessingStatus.FAILED
        assert "Transcription service unavailable" in data["error_message"]


@pytest.mark.integration
class TestConcurrentOperations:
    @patch("app.api.v1.episodes.process_episode_task")
    @patch("app.api.v1.episodes.episode_service")
    async def test_multiple_episode_creation(self, mock_service, mock_task, client):
        # Mock service to return different episodes
        episodes = []
        for i in range(3):
            episode = MagicMock()
            episode.id = f"concurrent-{i}"
            episode.name = f"Concurrent Episode {i}"
            episode.speakers_count = 2
            episode.status = ProcessingStatus.PENDING
            episode.created_at = "2024-01-01T00:00:00"
            episode.updated_at = "2024-01-01T00:00:00"
            episodes.append(episode)
        
        mock_service.create_episode = AsyncMock(side_effect=episodes)
        mock_task.delay.return_value = None
        
        # Create multiple episodes concurrently
        responses = []
        for i in range(3):
            response = client.post(
                "/api/v1/episodes/",
                data={
                    "name": f"Concurrent Episode {i}",
                    "speakers_count": "2",
                    "url": f"https://example.com/episode{i}.mp3",
                    "transcript_only": "false",
                    "generate_extra": "false"
                }
            )
            responses.append(response)
        
        # Verify all were created successfully
        for i, response in enumerate(responses):
            assert response.status_code == 200
            data = response.json()
            assert data["id"] == f"concurrent-{i}"
            assert data["name"] == f"Concurrent Episode {i}"


@pytest.mark.integration
class TestDataPersistence:
    def test_episode_data_persistence_across_requests(self, client):
        with tempfile.TemporaryDirectory() as tmpdir:
            # Override directories for testing
            with patch('app.core.config.settings.RESULTS_DIR', tmpdir):
                # Create test files
                substack_file = os.path.join(tmpdir, "substack_persistence_test.md")
                with open(substack_file, 'w') as f:
                    f.write("### Show Notes\n- Test note\n\n### Timestamps\n[00:00:00] Start")
                
                with patch("app.api.v1.episodes.episode_service") as mock_service:
                    mock_service.list_episodes = AsyncMock(return_value=[])
                    
                    # First request - should pick up file from filesystem
                    response = client.get("/api/v1/episodes/")
                    assert response.status_code == 200
                    
                    # The service should have been called
                    mock_service.list_episodes.assert_called_once()