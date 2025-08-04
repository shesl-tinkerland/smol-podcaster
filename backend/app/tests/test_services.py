import pytest
from unittest.mock import MagicMock, patch, AsyncMock
from app.services.ai_service import AIService
from app.services.transcription_service import TranscriptionService
from app.services.episode_service import EpisodeService
from app.models.episode import EpisodeCreate, ProcessingStatus

@pytest.mark.asyncio
class TestAIService:
    async def test_call_anthropic(self):
        service = AIService()
        service.anthropic_client = MagicMock()
        mock_response = MagicMock()
        mock_response.content = [MagicMock(text="Test response")]
        service.anthropic_client.messages.create.return_value = mock_response
        
        result = await service.call_anthropic("Test prompt")
        assert result == "Test response"
        service.anthropic_client.messages.create.assert_called_once()
    
    async def test_call_openai(self):
        service = AIService()
        service.openai_client = MagicMock()
        mock_response = MagicMock()
        mock_response.choices = [MagicMock(message=MagicMock(content="Test response"))]
        service.openai_client.chat.completions.create.return_value = mock_response
        
        result = await service.call_openai("Test prompt")
        assert result == "Test response"
    
    async def test_create_chapters(self):
        service = AIService()
        service.call_anthropic = AsyncMock(return_value="Claude chapters")
        service.call_openai = AsyncMock(return_value="GPT chapters")
        
        result = await service.create_chapters("Test transcript")
        assert "Claude chapters" in result
        assert "GPT chapters" in result

@pytest.mark.asyncio
class TestTranscriptionService:
    async def test_process_transcript(self):
        service = TranscriptionService()
        transcript = [
            {"speaker": "SPEAKER 1", "text": "Hello", "start": "0", "end": "5"},
            {"speaker": "SPEAKER 2", "text": "World", "start": "5", "end": "10"}
        ]
        
        with patch("builtins.open", create=True) as mock_open:
            result = await service.process_transcript(transcript, "test_episode")
            
            assert "**SPEAKER 1** [00:00:00]: Hello" in result
            assert "**SPEAKER 2** [00:00:05]: World" in result
    
    async def test_upload_file_and_use_url_with_url(self):
        service = TranscriptionService()
        url = "https://example.com/audio.mp3"
        
        result = await service.upload_file_and_use_url(url)
        assert result == url
    
    @patch("os.path.exists")
    async def test_upload_file_and_use_url_with_file(self, mock_exists):
        service = TranscriptionService()
        service.upload_to_tmpfiles = AsyncMock(return_value="https://tmpfiles.org/test.mp3")
        mock_exists.return_value = True
        
        result = await service.upload_file_and_use_url("/path/to/file.mp3")
        assert result == "https://tmpfiles.org/test.mp3"

@pytest.mark.asyncio
class TestEpisodeService:
    async def test_create_episode(self):
        service = EpisodeService()
        episode_data = EpisodeCreate(
            name="Test Episode",
            speakers_count=2,
            transcript_only=False,
            generate_extra=False
        )
        
        episode = await service.create_episode(episode_data)
        
        assert episode.name == "Test Episode"
        assert episode.speakers_count == 2
        assert episode.status == ProcessingStatus.PENDING
        assert episode.id in service.episodes_db
    
    async def test_get_episode(self):
        service = EpisodeService()
        episode_data = EpisodeCreate(
            name="Test Episode",
            speakers_count=2,
            transcript_only=False,
            generate_extra=False
        )
        created_episode = await service.create_episode(episode_data)
        
        retrieved_episode = await service.get_episode(created_episode.id)
        assert retrieved_episode is not None
        assert retrieved_episode.id == created_episode.id
    
    async def test_update_episode_status(self):
        service = EpisodeService()
        episode_data = EpisodeCreate(
            name="Test Episode",
            speakers_count=2,
            transcript_only=False,
            generate_extra=False
        )
        episode = await service.create_episode(episode_data)
        
        updated = await service.update_episode_status(
            episode.id, 
            ProcessingStatus.COMPLETED
        )
        
        assert updated is not None
        assert updated.status == ProcessingStatus.COMPLETED