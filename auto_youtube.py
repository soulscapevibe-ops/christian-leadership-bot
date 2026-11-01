import os
import asyncio
import moviepy.config as conf

# Force MoviePy to locate ImageMagick on the Linux GitHub runner
conf.IMAGEMAGICK_BINARY = "/usr/bin/convert"

from google import genai
from moviepy.editor import TextClip, CompositeVideoClip, ColorClip, AudioFileClip, concatenate_videoclips
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
import edge_tts

# Configuration for the video style
VOICE = "en-US-ChristopherNeural"  # Professional, calm, elegant male voice (or try en-US-AriaNeural for female)

async def generate_voiceover(text, output_filename="voiceover.mp3"):
    print("Generating AI voiceover...")
    communicate = edge_tts.Communicate(text, VOICE)
    await communicate.save(output_filename)
    print("Voiceover generated successfully!")

def upload_to_youtube(file_path, title, description):
    print("Authenticating with YouTube API...")
    credentials = Credentials(
        token=None,
        refresh_token=os.environ.get("YOUTUBE_REFRESH_TOKEN"),
        token_uri="https://oauth2.googleapis.com/token",
        client_id=os.environ.get("YOUTUBE_CLIENT_ID"),
        client_secret=os.environ.get("YOUTUBE_CLIENT_SECRET"),
        scopes=["https://www.googleapis.com/auth/youtube.upload"]
    )
    
    youtube = build("youtube", "v3", credentials=credentials)

    body = {
        "snippet": {
            "title": title,
            "description": description,
            "categoryId": "22"
        },
        "status": {
            "privacyStatus": "public" 
        }
    }

    print(f"Preparing upload for file: {file_path}")
    media = MediaFileUpload(file_path, chunksize=-1, resumable=True)
    request = youtube.videos().insert(part="snippet,status", body=body, media_body=media)
    
    response = None
    while response is None:
        status, response = request.next_chunk()
        if status:
            print(f"Uploaded {int(status.progress() * 100)}%.")
            
    print(f"Video successfully uploaded! YouTube Video ID: {response.get('id')}")

def main():
    print("Starting YouTube automation script...")

    # 1. Initialize Gemini Client
    client = genai.Client()
    print("Gemini client initialized successfully!")

    # Generate a script about Servant Leadership using Gemini
    prompt = (
        "Write a short, powerful, elegant 30-second script about Servant Leadership "
        "focusing on empathy, lifting others up, and leading with a quiet strength. "
        "Keep it concise, inspiring, and professional."
    )
    
    response = client.models.generate_content(
        model='gemini-2.5-flash',
        contents=prompt,
    )
    script_text = response.text.strip()
    print(f"Generated Script: {script_text[:60]}...")

    # 2. Create the Voiceover Audio asynchronously
    loop = asyncio.get_event_loop()
    loop.run_until_complete(generate_voiceover(script_text, "voiceover.mp3"))

    # 3. Render video with MoviePy (Clean, elegant look)
    print("Starting video composition with MoviePy...")
    
    # Load the generated voiceover audio to match video duration
    audio_clip = AudioFileClip("voiceover.mp3")
    duration = audio_clip.duration

    # Create an elegant dark navy/slate background (clean modern look)
    # 1280x720 landscape, or use (1080, 1920) if you want YouTube Shorts
    bg_clip = ColorClip(size=(1280, 720), color=(15, 23, 42), duration=duration)

    # Create a clean text caption overlay for the core message
    # Splitting the script into a punchy title/quote card overlay
    txt_clip = TextClip(
        "Servant Leadership:\nTrue strength is found in lifting others.", 
        fontsize=42, 
        color='white', 
        font='Arial-Bold',
        size=(1100, 500),
        method='caption'
    ).set_duration(duration).set_position('center')

    # Composite background and text, then add voiceover audio
    video = CompositeVideoClip([bg_clip, txt_clip])
    video = video.set_audio(audio_clip)

    # Write final video file
    video.write_videofile(
        "final_video.mp4", 
        fps=24, 
        codec='libx264', 
        audio_codec='aac',
        bitrate="3000k"
    )
    print("Video generated and saved successfully as final_video.mp4!")

    # 4. Upload to YouTube
    print("Starting YouTube upload process...")
    upload_to_youtube(
        file_path="final_video.mp4", 
        title="The True Power of Servant Leadership 🌿", 
        description=f"{script_text}\n\n#ServantLeadership #Leadership #Inspiration #FaithAndLeadership"
    )
    print("YouTube automation workflow completed entirely!")

if __name__ == "__main__":
    main()
