from typing import List, Dict, Optional
import re
import json
import os
import replicate
import tempfile
import requests
from app.models.episode import TranscriptSegment
from app.core.config import settings

class TranscriptionService:
    def __init__(self):
        self.fix_recording_mapping = {
            "noose": "Nous",
            "Dali": "DALL·E",
            "Swyggs": "Swyx",
            " lama ": " Llama "
        }
    
    async def transcribe_audio(self, file_url: str, episode_name: str, speakers_count: int) -> List[Dict]:
        # Check if the URL is from Dropbox and replace the domain
        file_url = re.sub(r"https?:\/\/(www\.)?dropbox\.com", "https://dl.dropboxusercontent.com", file_url)
        
        print(f"Running transcription on {file_url}")
        
        output = replicate.run(
            "thomasmol/whisper-diarization:7e5dafea13d80265ea436e51a310ae5103b9f16e2039f54de4eede3060a61617",
            input={
                "file_url": file_url,
                "num_speakers": speakers_count,
                "prompt": "Audio of Latent Space, a technical podcast about artificial intelligence and machine learning hosted by Swyx and Alessio."
            }
        )
        
        # Save raw transcript
        os.makedirs(settings.RAW_TRANSCRIPTS_DIR, exist_ok=True)
        with open(os.path.join(settings.RAW_TRANSCRIPTS_DIR, f"{episode_name}.json"), "w") as f:
            json.dump(output, f)
        
        return output['segments']
    
    async def process_transcript(self, transcript: List[Dict], episode_name: str) -> str:
        transcript_strings = []
        
        for entry in transcript:
            speaker = entry["speaker"]
            text = entry["text"]
            
            # Replace each word in fix_recording_mapping with the correct word
            for key, value in self.fix_recording_mapping.items():
                text = text.replace(key, value)
            
            # Convert "start" value to seconds and convert to hours, minutes and seconds
            seconds = int(float(entry["start"]))
            minutes, seconds = divmod(seconds, 60)
            hours, minutes = divmod(minutes, 60)
            
            timestamp = "[{:02d}:{:02d}:{:02d}]".format(hours, minutes, seconds)
            
            transcript_strings.append(f"**{speaker}** {timestamp}: {text}")
        
        clean_transcript = "\n\n".join(transcript_strings)
        
        # Save clean transcript
        os.makedirs(settings.TRANSCRIPTS_DIR, exist_ok=True)
        with open(os.path.join(settings.TRANSCRIPTS_DIR, f"{episode_name}.md"), "w") as f:
            f.write(clean_transcript)
        
        return clean_transcript
    
    async def process_youtube_transcript(self, parts: List[Dict], episode_name: str) -> None:
        formatted_transcriptions = []
        
        for part in parts:
            formatted_transcriptions.append(part['text'].strip())
        
        os.makedirs(settings.RESULTS_DIR, exist_ok=True)
        with open(os.path.join(settings.RESULTS_DIR, f"{episode_name}-yt-subtitles.txt"), "w") as file:
            file.writelines("\n".join(formatted_transcriptions))
    
    async def upload_to_tmpfiles(self, file_path: str) -> Optional[str]:
        """Uploads a file to tmpfiles.org and returns the downloadable URL."""
        print("Uploading file to tmpfiles.org")
        upload_url = 'https://tmpfiles.org/api/v1/upload'
        
        with open(file_path, 'rb') as file:
            files = {'file': (os.path.basename(file_path), file)}
            response = requests.post(upload_url, files=files)
            
            if response.status_code == 200:
                file_url = response.json()
                print(f"File uploaded successfully. URL: {file_url}")
                return file_url['data']['url'].replace("https://tmpfiles.org/", "https://tmpfiles.org/dl/")
            else:
                print("Failed to upload the file. Please check the error and try again.")
                return None
    
    async def upload_file_and_use_url(self, file_or_url: str) -> Optional[str]:
        """Handles file path or URL input and returns a URL for processing."""
        if os.path.exists(file_or_url):
            # It's a local file path
            return await self.upload_to_tmpfiles(file_or_url)
        else:
            # It's already a URL
            print("Using file at remote URL.")
            return file_or_url