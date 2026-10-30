import os
from google import genai
from moviepy.editor import TextClip, CompositeVideoClip, ColorClip, concatenate_videoclips
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

def upload_to_youtube(file_path, title, description):
    print("Authenticating with YouTube API...")
    # Authenticate silently using GitHub Action Secrets
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
            "categoryId": "22"  # People & Blogs category
        },
        "status": {
            "privacyStatus": "public"  # Change to "private" or "unlisted" if you want to review first
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

    # --- ADD YOUR GEMINI SCRIPT GENERATION & CONTENT LOGIC HERE ---
    # Example: response = client.models.generate_content(...)
    
    # 2. Render your video using MoviePy and save it locally as 'final_video.mp4'
    print("Starting video generation with MoviePy...")
    
    # --- EXAMPLE MOVIEPY CODE (Replace or keep your own rendering logic) ---
    # Make sure your script actually saves the file as 'final_video.mp4'
    txt_clip = TextClip("Christian Leadership", fontsize=50, color='white', size=(1280, 720))
    txt_clip = txt_clip.set_duration(5)
    video = CompositeVideoClip([txt_clip])
    video.write_videofile("final_video.mp4", fps=24, codec='libx264', audio=False)
    # ---------------------------------------------------------------------

    print("Video generated and saved successfully as final_video.mp4!")

    # 3. Upload the generated video to YouTube
    print("Starting YouTube upload process...")
    upload_to_youtube(
        file_path="final_video.mp4", 
        title="Christian Leadership Daily Inspiration", 
        description="An automated daily message of leadership and faith."
    )
    print("YouTube upload workflow completed entirely!")

if __name__ == "__main__":
    main()
