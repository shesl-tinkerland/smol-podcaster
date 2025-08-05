import pytest
from unittest.mock import MagicMock, patch, AsyncMock
from app.services.ai_service import AIService
from app.services.transcription_service import TranscriptionService
from app.services.episode_service import EpisodeService
from app.services.chapter_sync_service import ChapterSyncService
from app.models.episode import EpisodeCreate, ProcessingStatus
import os
import tempfile

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
    
    async def test_save_episode_results(self):
        service = EpisodeService()
        
        with tempfile.TemporaryDirectory() as tmpdir:
            with patch('app.core.config.settings.RESULTS_DIR', tmpdir):
                results_path = await service.save_episode_results(
                    "test_episode",
                    "Chapter 1\nChapter 2",
                    "Test writeup",
                    "- Note 1\n- Note 2",
                    "Title suggestions",
                    "Tweet suggestions",
                    "Test transcript"
                )
                
                assert os.path.exists(results_path)
                assert os.path.exists(os.path.join(tmpdir, "substack_test_episode.md"))
                
                with open(results_path, 'r') as f:
                    content = f.read()
                    assert "Chapter 1" in content
                    assert "Test writeup" in content
                    assert "Note 1" in content


@pytest.mark.asyncio
class TestChapterSyncService:
    async def test_update_video_chapters(self):
        service = ChapterSyncService()
        
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create mock transcript files
            audio_transcript = "**SPEAKER 1** [00:00:00]: Hello\n**SPEAKER 2** [00:00:05]: World"
            video_transcript = "**SPEAKER 1** [00:00:01]: Hello\n**SPEAKER 2** [00:00:06]: World"
            
            os.makedirs(os.path.join(tmpdir, "podcasts-clean-transcripts"))
            os.makedirs(os.path.join(tmpdir, "podcasts-results"))
            
            with open(os.path.join(tmpdir, "podcasts-clean-transcripts", "audio.md"), 'w') as f:
                f.write(audio_transcript)
            
            with open(os.path.join(tmpdir, "podcasts-clean-transcripts", "video.md"), 'w') as f:
                f.write(video_transcript)
            
            # Create substack file
            with open(os.path.join(tmpdir, "podcasts-results", "substack_audio.md"), 'w') as f:
                f.write("Existing content")
            
            with patch('app.core.config.settings.TRANSCRIPTS_DIR', os.path.join(tmpdir, "podcasts-clean-transcripts")):
                with patch('app.core.config.settings.RESULTS_DIR', os.path.join(tmpdir, "podcasts-results")):
                    chapters = "[00:00:00] Introduction\n[00:00:05] Main Topic"
                    result = await service.update_video_chapters(chapters, "audio", "video")
                    
                    assert "[00:00:01]  Introduction" in result
                    assert "[00:00:06]  Main Topic" in result


@pytest.mark.asyncio
class TestAIServiceExtended:
    async def test_create_show_notes(self):
        service = AIService()
        service.call_anthropic = AsyncMock(return_value="- Company A\n- Person B")
        service.call_openai = AsyncMock(return_value="- Project C\n- Research D")
        
        result = await service.create_show_notes("Test transcript")
        assert "Company A" in result
        assert "Project C" in result
    
    async def test_create_writeup(self):
        service = AIService()
        service.call_anthropic = AsyncMock(return_value="Claude writeup")
        service.call_openai = AsyncMock(return_value="GPT writeup")
        
        result = await service.create_writeup("Test transcript")
        assert "Claude writeup" in result
        assert "GPT writeup" in result
    
    async def test_title_suggestions(self):
        service = AIService()
        service.call_anthropic = AsyncMock(return_value="Claude titles")
        service.call_openai = AsyncMock(return_value="GPT titles")
        
        result = await service.title_suggestions("Test writeup")
        assert "Claude titles" in result
        assert "GPT titles" in result
    
    async def test_tweet_suggestions(self):
        service = AIService()
        service.call_anthropic = AsyncMock(return_value="Claude tweets")
        service.call_openai = AsyncMock(return_value="GPT tweets")
        
        result = await service.tweet_suggestions("Test transcript")
        assert "Claude tweets" in result
        assert "GPT tweets" in result
    
    async def test_clips_picker(self):
        service = AIService()
        service.call_anthropic = AsyncMock(return_value="Claude clips")
        service.call_openai = AsyncMock(return_value="GPT clips")
        
        result = await service.clips_picker("Test transcript")
        assert "Claude clips" in result
        assert "GPT clips" in result
    
    async def test_ai_service_error_handling(self):
        service = AIService()
        service.anthropic_client = MagicMock()
        service.anthropic_client.messages.create.side_effect = Exception("API Error")
        
        result = await service.call_anthropic("Test prompt")
        assert "An error occurred with Claude" in result
        
        service.openai_client = MagicMock()
        service.openai_client.chat.completions.create.side_effect = Exception("API Error")
        
        result = await service.call_openai("Test prompt")
        assert "An error occurred with OpenAI" in result


@pytest.mark.asyncio
class TestTranscriptionServiceExtended:
    async def test_transcribe_audio_with_dropbox_url(self):
        service = TranscriptionService()
        
        with patch('replicate.run') as mock_replicate:
            mock_replicate.return_value = {
                'segments': [
                    {"speaker": "SPEAKER 1", "text": "Test", "start": "0", "end": "5"}
                ]
            }
            
            with patch('builtins.open', create=True):
                with patch('os.makedirs'):
                    result = await service.transcribe_audio(
                        "https://www.dropbox.com/test.mp3",
                        "test_episode",
                        2
                    )
                    
                    # Check Dropbox URL was converted
                    call_args = mock_replicate.call_args[1]['input']
                    assert call_args['file_url'] == "https://dl.dropboxusercontent.com/test.mp3"
    
    async def test_process_youtube_transcript(self):
        service = TranscriptionService()
        parts = [
            {"text": "First subtitle"},
            {"text": "Second subtitle"}
        ]
        
        with tempfile.TemporaryDirectory() as tmpdir:
            with patch('app.core.config.settings.RESULTS_DIR', tmpdir):
                await service.process_youtube_transcript(parts, "test_episode")
                
                yt_file = os.path.join(tmpdir, "test_episode-yt-subtitles.txt")
                assert os.path.exists(yt_file)
                
                with open(yt_file, 'r') as f:
                    content = f.read()
                    assert "First subtitle" in content
                    assert "Second subtitle" in content
    
    async def test_fix_recording_mapping(self):
        service = TranscriptionService()
        transcript = [
            {"speaker": "SPEAKER 1", "text": "noose is great", "start": "0", "end": "5"},
            {"speaker": "SPEAKER 2", "text": "I love Dali", "start": "5", "end": "10"}
        ]
        
        with patch('builtins.open', create=True):
            with patch('os.makedirs'):
                result = await service.process_transcript(transcript, "test_episode")
                
                assert "Nous is great" in result
                assert "I love DALL·E" in result
                assert "noose" not in result
                assert "Dali" not in result