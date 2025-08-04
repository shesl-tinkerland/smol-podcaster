from celery import Task
from app.core.celery_app import celery_app
from app.services.transcription_service import TranscriptionService
from app.services.ai_service import AIService
from app.services.episode_service import EpisodeService
from app.services.chapter_sync_service import ChapterSyncService
from app.models.episode import ProcessingStatus
import os
import json
import asyncio

class CallbackTask(Task):
    def on_success(self, retval, task_id, args, kwargs):
        """Success handler."""
        info = {'current': 'Completed', 'progress': 100}
        self.update_state(state='SUCCESS', meta=info)
    
    def on_failure(self, exc, task_id, args, kwargs, einfo):
        """Error handler."""
        info = {'current': 'Failed', 'progress': 0, 'error': str(exc)}
        self.update_state(state='FAILURE', meta=info)

@celery_app.task(base=CallbackTask, bind=True)
def process_episode_task(self, episode_id: str, file_or_url: str, name: str, 
                        speakers_count: int, transcript_only: bool, generate_extra: bool):
    """Process a podcast episode"""
    
    # Initialize services
    transcription_service = TranscriptionService()
    ai_service = AIService()
    episode_service = EpisodeService()
    
    # Create async event loop for async services
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    
    try:
        # Update progress
        self.update_state(state='PROGRESS', meta={'current': 'Starting transcription', 'progress': 10, 'episode_id': episode_id})
        
        # Check if raw transcript already exists
        raw_transcript_path = f"./podcasts-raw-transcripts/{name}.json"
        if os.path.exists(raw_transcript_path):
            with open(raw_transcript_path, "r") as f:
                transcript = json.loads(f.read())['segments']
        else:
            # Upload file if needed and transcribe
            url = loop.run_until_complete(transcription_service.upload_file_and_use_url(file_or_url))
            if not url:
                raise Exception("Failed to process file or URL")
            
            transcript = loop.run_until_complete(
                transcription_service.transcribe_audio(url, name, speakers_count)
            )
        
        self.update_state(state='PROGRESS', meta={'current': 'Processing transcript', 'progress': 30, 'episode_id': episode_id})
        
        # Process YouTube subtitles
        loop.run_until_complete(transcription_service.process_youtube_transcript(transcript, name))
        
        # Process transcript
        clean_transcript_path = f"./podcasts-clean-transcripts/{name}.md"
        if os.path.exists(clean_transcript_path):
            with open(clean_transcript_path, "r") as f:
                clean_transcript = f.read()
        else:
            clean_transcript = loop.run_until_complete(
                transcription_service.process_transcript(transcript, name)
            )
        
        # Update episode with transcript path
        loop.run_until_complete(
            episode_service.update_episode_paths(episode_id, transcript_path=clean_transcript_path)
        )
        
        if transcript_only:
            loop.run_until_complete(
                episode_service.update_episode_status(episode_id, ProcessingStatus.COMPLETED)
            )
            return {"status": "completed", "episode_id": episode_id}
        
        # Generate AI content
        self.update_state(state='PROGRESS', meta={'current': 'Creating chapters', 'progress': 50, 'episode_id': episode_id})
        chapters = loop.run_until_complete(ai_service.create_chapters(clean_transcript))
        
        self.update_state(state='PROGRESS', meta={'current': 'Creating show notes', 'progress': 60, 'episode_id': episode_id})
        show_notes = loop.run_until_complete(ai_service.create_show_notes(clean_transcript))
        
        self.update_state(state='PROGRESS', meta={'current': 'Generating clips', 'progress': 70, 'episode_id': episode_id})
        loop.run_until_complete(ai_service.clips_picker(clean_transcript))
        
        self.update_state(state='PROGRESS', meta={'current': 'Creating writeup', 'progress': 80, 'episode_id': episode_id})
        writeup = loop.run_until_complete(ai_service.create_writeup(clean_transcript))
        
        title_suggestions = None
        tweet_suggestions = None
        
        if generate_extra:
            self.update_state(state='PROGRESS', meta={'current': 'Generating title suggestions', 'progress': 90, 'episode_id': episode_id})
            title_suggestions = loop.run_until_complete(ai_service.title_suggestions(writeup))
            tweet_suggestions = loop.run_until_complete(ai_service.tweet_suggestions(clean_transcript))
        
        # Save results
        self.update_state(state='PROGRESS', meta={'current': 'Saving results', 'progress': 95, 'episode_id': episode_id})
        results_path = loop.run_until_complete(
            episode_service.save_episode_results(
                name, chapters, writeup, show_notes,
                title_suggestions, tweet_suggestions, clean_transcript
            )
        )
        
        # Update episode status
        loop.run_until_complete(
            episode_service.update_episode_paths(episode_id, results_path=results_path)
        )
        loop.run_until_complete(
            episode_service.update_episode_status(episode_id, ProcessingStatus.COMPLETED)
        )
        
        return {"status": "completed", "episode_id": episode_id, "results_path": results_path}
        
    except Exception as e:
        loop.run_until_complete(
            episode_service.update_episode_status(episode_id, ProcessingStatus.FAILED, str(e))
        )
        raise
    finally:
        loop.close()

@celery_app.task(base=CallbackTask, bind=True)
def sync_chapters_task(self, chapters: str, audio_name: str, video_name: str):
    """Sync chapters between audio and video"""
    
    chapter_service = ChapterSyncService()
    
    # Create async event loop
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    
    try:
        self.update_state(state='PROGRESS', meta={'current': 'Syncing chapters', 'progress': 50})
        
        result = loop.run_until_complete(
            chapter_service.update_video_chapters(chapters, audio_name, video_name)
        )
        
        return {"status": "completed", "result": result}
        
    finally:
        loop.close()