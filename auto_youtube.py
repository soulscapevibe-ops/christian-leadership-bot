import os
import time
import asyncio
import urllib.request
import moviepy.config as conf

# Force MoviePy to locate ImageMagick on the Linux GitHub runner
conf.IMAGEMAGICK_BINARY = "/usr/bin/convert"

from google import genai
from google.genai.errors import ServerError
from moviepy.editor import TextClip, CompositeVideoClip, VideoFileClip, AudioFileClip
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
import edge_tts

VOICE = "en-US-ChristopherNeural"

# Direct copyright-free background video URL (A soothing nature/landscape loop)
BACKGROUND_VIDEO_URL = "https://assets.mixkit.co/videos/preview/mixkit-aerial-view-of-pine-forest-during-sunset-41650-large.mp4"

async def generate_voiceover(text, output_filename="voiceover.mp3"):
    print("Generating AI voiceover...")
    communicate = edge_tts.Communicate(text, VOICE)
    await communicate.save(output_filename)
    print("Voiceover generated successfully!")

def download_background_video(url, output_filename="background.mp4"):
    print("Downloading background landscape video...")
    try:
        urllib.request.urlretrieve(url, output_filename)
        print("Background video downloaded successfully!")
        return True
    except Exception as e:
        print(f"Failed to download background video: {e}")
        return False

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

    # Strict prompt to ensure Gemini outputs ONLY the pure voiceover text with zero fluff
    prompt = (
        "Write a short, powerful, elegant 30-second script about Servant Leadership "
        "focusing on empathy, lifting others up, and leading with a quiet strength. "
        "CRITICAL REQUIREMENT: Return ONLY the raw paragraph text to be spoken aloud. "
        "Do not include titles, labels like VOICEOVER, scene directions, brackets, or meta notes."
    )
    
    # 2. Generate content with automatic retries and fallback
    script_text = None
    max_retries = 3
    for attempt in range(1, max_retries + 1):
        try:
            print(f"Attempting to generate script (Attempt {attempt}/{max_retries})...")
            response = client.models.generate_content(
                model='gemini-3.8-flash',
                contents=prompt,
            )
            script_text = response.text.strip().replace("VOICEOVER:", "").strip()
            break
        except ServerError:
            if attempt < max_retries:
                print(f"Model busy (503). Retrying in 10 seconds...")
                time.sleep(10)
            else:
                print("Gemini servers busy. Using clean fallback script.")
                script_text = (
                    "True leadership doesn't demand the spotlight. It builds the stage. "
                    "It is a quiet strength—one that listens before it speaks, and measures success "
                    "not by how high we climb, but by how many we lift along the way. "
                    "Because when you lead with empathy, you don’t just direct the path. You clear it. "
                    "To serve isn’t stepping down. It is the highest way to lead."
                )

    print(f"Clean Script Text: {script_text}")

    # 3. Create the Voiceover Audio asynchronously
    loop = asyncio.get_event_loop()
    loop.run_until_complete(generate_voiceover(script_text, "voiceover.mp3"))

    # 4. Download background video loop
    download_success = download_background_video(BACKGROUND_VIDEO_URL, "background.mp4")

    # 5. Render video with MoviePy (Combining background video, voiceover, and matched text captions)
    print("Starting video composition with MoviePy...")
    
    audio_clip = AudioFileClip("voiceover.mp3")
    duration = audio_clip.duration

    if download_success and os.path.exists("background.mp4"):
        # Load background video, loop it if it's shorter than the audio, and trim to exact audio length
        bg_video = VideoFileClip("background.mp4")
        if bg_video.duration < duration:
            # Loop video to match audio length if necessary
            loops_needed = int(duration // bg_video.duration) + 1
            bg_video = bg_video.loop(n=loops_needed)
        bg_clip = bg_video.subclip(0, duration).resize(height=720) # ensure clean fit
    else:
        # Fallback safety if download ever hiccups
        from moviepy.editor import ColorClip
        bg_clip = ColorClip(size=(1280, 720), color=(15, 23, 42), duration=duration)

    # Create the clean on-screen caption matching the exact clean voiceover words
    txt_clip = TextClip(
        script_text, 
        fontsize=36, 
        color='white', 
        font='Arial-Bold',
        size=(1100, 560),
        method='caption'
    ).set_duration(duration).set_position('center')

    # Composite background video and text overlay, then add the voiceover audio
    video = CompositeVideoClip([bg_clip, txt_clip])
    video = video.set_audio(audio_clip)

    video.write_videofile(
        "final_video.mp4", 
        fps=24, 
        codec='libx264', 
        audio_codec='aac',
        bitrate="3000k"
    )
    print("Video generated and saved successfully as final_video.mp4!")

    # 6. Upload the polished video package to YouTube
    print("Starting YouTube upload process...")
    upload_to_youtube(
        file_path="final_video.mp4", 
        title="The Quiet Elevation: The True Power of Servant Leadership 🌿", 
        description=f"{script_text}\n\n#ServantLeadership #Leadership #Inspiration #FaithAndLeadership"
    )
    print("YouTube automation workflow completed entirely!")

if __name__ == "__main__":
    main()
