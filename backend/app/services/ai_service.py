from typing import Optional, List, Dict
import os
from openai import OpenAI
from anthropic import Anthropic
from app.core.config import settings

class AIService:
    def __init__(self):
        self.openai_client = OpenAI(api_key=settings.OPENAI_API_KEY)
        self.anthropic_client = Anthropic(api_key=settings.ANTHROPIC_API_KEY)
        self.anthropic_model = settings.ANTHROPIC_MODEL
        self.gpt_model = settings.GPT_MODEL
    
    async def call_anthropic(self, prompt: str, temperature: float = 0.5) -> str:
        try:
            response = self.anthropic_client.messages.create(
                model=self.anthropic_model,
                max_tokens=3000,
                temperature=temperature,
                messages=[{"role": "user", "content": prompt}]
            )
            return response.content[0].text
        except Exception as e:
            return f"An error occurred with Claude: {e}"
    
    async def call_openai(self, prompt: str, temperature: float = 0.5) -> str:
        try:
            result = self.openai_client.chat.completions.create(
                model=self.gpt_model,
                temperature=temperature,
                messages=[{"role": "user", "content": prompt}]
            )
            return result.choices[0].message.content
        except Exception as e:
            error_msg = f"An error occurred with OpenAI: {e}"
            print(error_msg)
            return error_msg
    
    async def create_chapters(self, transcript: str) -> str:
        prompt = f"""I'm going to give you a podcast transcript with timestamps for each speaker section in this format: `SPEAKER: Some transcription [00:00:00]`. Generate a list of all major topics covered in the podcast, and the timestamp where the discussion starts. Make sure to use the timestamp BEFORE the the discussion starts. Make sure to cover topics from the whole episode. Use this format: `- [00:00:00] Topic name`. Here's the transcript: 

{transcript}"""
        
        claude_suggestions = await self.call_anthropic(prompt, 0.6)
        gpt_suggestions = await self.call_openai(prompt, 0.6)
        
        return "\n".join([claude_suggestions, gpt_suggestions])
    
    async def create_show_notes(self, transcript: str) -> str:
        prompt = f"""I'll give you a podcast transcript; help me create a list of every company, person, project, research paper, or any other named entity that you find in it. Return it as a markdown list. If it references a company or person that you know, add a link to their website or online profile. Here's the transcript: 

{transcript}"""
        
        claude_suggestions = await self.call_anthropic(prompt, 0.4)
        gpt_suggestions = await self.call_openai(prompt, 0.4)
        
        return "\n".join([claude_suggestions, gpt_suggestions])
    
    async def create_writeup(self, transcript: str) -> str:
        prompt = f"""You're the writing assistant of a podcast producer. For each episode, we do a write up to recap the core ideas of the episode and expand on them. Write a list of bullet points on topics we should expand on, and then 4-5 paragraphs about them. Here's the transcript: 

{transcript}"""
        
        claude_suggestions = await self.call_anthropic(prompt, 0.7)
        gpt_suggestions = await self.call_openai(prompt, 0.7)
        
        return "\n".join([claude_suggestions, gpt_suggestions])
    
    async def title_suggestions(self, writeup: str) -> str:
        prompt = f"""
These are some titles of previous podcast episodes we've published:

1. "From RLHF to RLHB: The Case for Learning from Human Behavior"
2. "Commoditizing the Petaflop"
3. "Llama 2: The New Open LLM SOTA"
4. "FlashAttention 2: making Transformers 800% faster w/o approximation"
5. "Mapping the future of *truly* Open Models and Training Dolly for $30"
6. "Beating GPT-4 with Open Source LLMs"
7. "Why AI Agents Don't Work (yet)"
8. "The End of Finetuning"

Here's a write up of the latest podcast episode; suggest 8 title options for it that will be just as successful in catching the readers' attention:

{writeup}
"""
        
        gpt_suggestions = await self.call_openai(prompt, 0.7)
        claude_suggestions = await self.call_anthropic(prompt, 0.7)
        
        return f"\n\nGPT-4 title suggestions:\n\n{gpt_suggestions}\n\nClaude's title suggestions:\n{claude_suggestions}\n\n"
    
    async def tweet_suggestions(self, transcript: str) -> str:
        prompt = f"""
Here's a transcript of our latest podcast episode; suggest 8 tweets to share it on social medias.
It should include a few bullet points of the most interesting topics. Our audience is technical.
Use a writing style between Hemingway's and Flash Fiction. 

{transcript}
"""
        
        gpt_suggestions = await self.call_openai(prompt, 0.7)
        claude_suggestions = await self.call_anthropic(prompt, 0.7)
        
        return f"GPT-4 tweet suggestions:\n{gpt_suggestions}\n\nClaude's tweet suggestions:\n{claude_suggestions}\n"
    
    async def clips_picker(self, transcript: str) -> str:
        prompt = f"""I'm about to release my new video podcast and I want to create four 60 second clips for YouTube Shorts. Can you suggest 7-8 passages that would make for good clips and their rough timestamps? They are usually very insightful, funny, or controversial parts of the discussion. Here's the transcript: 

{transcript}"""
        
        claude_suggestions = await self.call_anthropic(prompt, 0.5)
        gpt_suggestions = await self.call_openai(prompt, 0.5)
        
        return "\n".join([claude_suggestions, gpt_suggestions])