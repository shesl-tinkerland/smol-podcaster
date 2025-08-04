from typing import List, Optional
import Levenshtein
import os
from app.core.config import settings

class ChapterSyncService:
    async def update_video_chapters(self, audio_chapters: str, audio_file_name: str, video_file_name: str) -> str:
        video_transcript_path = os.path.join(settings.TRANSCRIPTS_DIR, f"{video_file_name}.md")
        audio_transcript_path = os.path.join(settings.TRANSCRIPTS_DIR, f"{audio_file_name}.md")
        
        with open(video_transcript_path, "r") as f:
            video_transcript = f.read()
        
        with open(audio_transcript_path, "r") as f:
            audio_transcript = f.read()
        
        updated_chapters = []
        
        for chapter in audio_chapters.split("\n"):
            if chapter.strip() == "":
                continue
            
            timestamp, topic = chapter.split("]", 1)
            timestamp = timestamp.strip("[]").strip()
            
            # Find the corresponding segment in the audio transcript
            audio_segment = None
            for segment in audio_transcript.split("\n"):
                if timestamp.strip() in segment.strip():
                    audio_segment = segment
                    break
            
            if audio_segment is not None:
                # Find the closest matching segment in the video transcript
                closest_segment = None
                min_distance = float("inf")
                for segment in video_transcript.split("\n"):
                    distance = Levenshtein.distance(segment, audio_segment)
                    
                    if distance < min_distance:
                        min_distance = distance
                        closest_segment = segment
                
                if closest_segment is not None:
                    video_seconds = closest_segment.split("]")[0]
                    updated_chapters.append(f"[{video_seconds.split('[')[1]}] {topic}")
                else:
                    updated_chapters.append(f"Couldn't find a match for {timestamp}")
            else:
                updated_chapters.append(f"Couldn't find a match for {timestamp}")
        
        spaced = "\n".join(updated_chapters)
        
        # Update the substack file with video chapters
        substack_file_path = os.path.join(settings.RESULTS_DIR, f"substack_{audio_file_name}.md")
        
        if os.path.exists(substack_file_path):
            with open(substack_file_path, "r") as f:
                existing_content = f.read()
            
            updated_content = "\n".join(updated_chapters) + "\n\n" + existing_content
            
            with open(substack_file_path, "w") as f:
                f.write(updated_content)
        
        return spaced