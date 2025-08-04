from typing import List, Optional, Dict
import os
import json
import uuid
from datetime import datetime
from app.models.episode import Episode, EpisodeCreate, ProcessingStatus
from app.core.config import settings

class EpisodeService:
    def __init__(self):
        # In production, this would use a proper database
        self.episodes_db: Dict[str, Episode] = {}
    
    async def create_episode(self, episode_data: EpisodeCreate) -> Episode:
        episode_id = str(uuid.uuid4())
        episode = Episode(
            id=episode_id,
            name=episode_data.name,
            speakers_count=episode_data.speakers_count,
            status=ProcessingStatus.PENDING,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        self.episodes_db[episode_id] = episode
        return episode
    
    async def get_episode(self, episode_id: str) -> Optional[Episode]:
        return self.episodes_db.get(episode_id)
    
    async def list_episodes(self) -> List[Episode]:
        episodes = []
        
        # Load episodes from file system
        if os.path.exists(settings.RESULTS_DIR):
            for filename in os.listdir(settings.RESULTS_DIR):
                if filename.startswith('substack_') and filename.endswith('.md'):
                    file_path = os.path.join(settings.RESULTS_DIR, filename)
                    episode_name = filename[len('substack_'):-3]
                    creation_time = datetime.fromtimestamp(os.path.getctime(file_path))
                    
                    # Check if episode exists in our db
                    existing = None
                    for ep in self.episodes_db.values():
                        if ep.name == episode_name:
                            existing = ep
                            break
                    
                    if existing:
                        episodes.append(existing)
                    else:
                        # Create episode entry from file
                        episode = Episode(
                            id=str(uuid.uuid4()),
                            name=episode_name,
                            speakers_count=2,  # Default
                            status=ProcessingStatus.COMPLETED,
                            created_at=creation_time,
                            updated_at=creation_time,
                            results_path=file_path
                        )
                        episodes.append(episode)
        
        # Add any pending episodes from memory
        for episode in self.episodes_db.values():
            if episode.status in [ProcessingStatus.PENDING, ProcessingStatus.PROCESSING]:
                episodes.append(episode)
        
        # Sort by creation time, most recent first
        episodes.sort(key=lambda x: x.created_at, reverse=True)
        return episodes
    
    async def update_episode_status(self, episode_id: str, status: ProcessingStatus, error_message: Optional[str] = None) -> Optional[Episode]:
        episode = self.episodes_db.get(episode_id)
        if episode:
            episode.status = status
            episode.updated_at = datetime.utcnow()
            if error_message:
                episode.error_message = error_message
            return episode
        return None
    
    async def update_episode_paths(self, episode_id: str, transcript_path: Optional[str] = None, results_path: Optional[str] = None) -> Optional[Episode]:
        episode = self.episodes_db.get(episode_id)
        if episode:
            if transcript_path:
                episode.transcript_path = transcript_path
            if results_path:
                episode.results_path = results_path
            episode.updated_at = datetime.utcnow()
            return episode
        return None
    
    async def save_episode_results(self, episode_name: str, chapters: str, writeup: str, show_notes: str, 
                                   title_suggestions: Optional[str] = None, tweet_suggestions: Optional[str] = None,
                                   transcript: Optional[str] = None) -> str:
        # Save main results file
        results_path = os.path.join(settings.RESULTS_DIR, f"{episode_name}.md")
        os.makedirs(settings.RESULTS_DIR, exist_ok=True)
        
        with open(results_path, "w") as f:
            f.write("Chapters:\n")
            f.write(chapters)
            f.write("\n\n")
            f.write("Writeup:\n")
            f.write(writeup)
            f.write("\n\n")
            f.write("Show Notes:\n")
            f.write(show_notes)
            f.write("\n\n")
            
            if title_suggestions:
                f.write("Title Suggestions:\n")
                f.write(title_suggestions)
                f.write("\n\n")
            
            if tweet_suggestions:
                f.write("Tweet Suggestions:\n")
                f.write(tweet_suggestions)
                f.write("\n")
        
        # Save Substack-formatted file
        substack_path = os.path.join(settings.RESULTS_DIR, f"substack_{episode_name}.md")
        with open(substack_path, "w") as f:
            f.write("### Show Notes\n")
            f.write(show_notes)
            f.write("\n\n")
            f.write("### Timestamps\n")
            f.write(chapters)
            f.write("\n\n")
            
            if transcript:
                f.write("### Transcript\n")
                # Add standard intro if Alessio is mentioned
                if "Alessio" in transcript:
                    f.write("**Alessio** [00:00:00]: Hey everyone, welcome to the Latent Space podcast. This is Alessio, partner and CTO-in-Residence at [Decibel Partners](https://decibel.vc), and I'm joined by my co-host Swyx, founder of [Smol AI](https://smol.ai).")
                f.write(transcript)
        
        return results_path