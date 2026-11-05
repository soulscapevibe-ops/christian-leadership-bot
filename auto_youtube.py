import os
import time
import asyncio
import urllib.request
import moviepy.config as conf

# Force MoviePy to locate ImageMagick on the Linux GitHub runner
conf.IMAGEMAGICK_BINARY = "/usr/bin/convert"

from google import genai
from google.genai.errors import ServerError
from moviepy.editor import TextClip, CompositeVideoClip, VideoFileClip, AudioFileClip, CompositeAudioClip
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
import edge_tts

VOICE = "en-US-ChristopherNeural"

# High-quality vibrant background video URL (Warm sunset/nature landscape)
BACKGROUND_VIDEO_URL = "https://assets.mixkit.co/videos/preview/mixkit-sun-shining-through-the-trees-of-a-forest-4355-large.mp4"

# Royalty-free soft ambient background music loop (Gentle, calm instrumental)
BACKGROUND_MUSIC_URL = "https://actions.google.com/sounds/v1/ambiences/morning_birds.ogg" 
# Alternative smooth ambient loop if needed: https://cdn.pixabay.com/download/audio/2022/05/27/audio_1808fbf756.mp3

async def generate_voiceover(text, output_filename="voiceover.mp3"):
    print("Generating AI voiceover...")
    communicate = edge_tts.Communicate(text, VOICE)
    await communicate.save(output_filename)
    print("Voiceover generated successfully!")

def download_file(url, output_filename):
    print(f"Downloading asset from {url}...")
    try:
        urllib.request.urlretrieve(url, output_filename)
        print(f"Successfully downloaded {output_filename}")
        return True
    except Exception as e:
        print(f"Failed to download {output_filename}: {e}")
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

    # 3. Create Voiceover Audio & Download Assets
    loop = asyncio.get_event_loop()
    loop.run_until_complete(generate_voiceover(script_text, "voiceover.mp3"))

    download_file(BACKGROUND_VIDEO_URL, "background.mp4")
    download_file(BACKGROUND_MUSIC_URL, "bg_music.ogg")

    # 4. Render video with MoviePy (HD Text, Motion Background, and Audio Mixing)
    print("Starting video composition with MoviePy...")
    
    voiceover_audio = AudioFileClip("voiceover.mp3")
    total_duration = voiceover_audio.duration

    # Set up background video with a slow zoom/motion effect
    if os.path.exists("background.mp4"):
        bg_video = VideoFileClip("background.mp4")
        if bg_video.duration < total_duration:
            loops_needed = int(total_duration // bg_video.duration) + 1
            bg_video = bg_video.loop(n=loops_needed)
        
        bg_clip = bg_video.subclip(0, total_duration).resize(lambda t: 1.0 + 0.04 * (t / total_duration))
        bg_clip = bg_clip.set_fps(24).crop(x_center=bg_clip.w/2, y_center=bg_clip.h/2, width=1280, height=720)
    else:
        from moviepy.editor import ColorClip
        bg_clip = ColorClip(size=(1280, 720), color=(15, 23, 42), duration=total_duration)

    # Mix Voiceover with Soft Background Music
    audio_tracks = [voiceover_audio.volumex(1.0)]
    if os.path.exists("bg_music.ogg"):
        try:
            bg_music = AudioFileClip("bg_music.ogg")
            if bg_music.duration < total_duration:
                bg_music = bg_music.loop(duration=total_duration)
            else:
                bg_music = bg_music.subclip(0, total_duration)
            # Lower music volume so it sits quietly in the background (15% volume)
            audio_tracks.append(bg_music.volumex(0.15))
        except Exception as e:
            print(f"Could not process background music: {e}")

    final_audio = CompositeAudioClip(audio_tracks)

    # Break script into sentence chunks for sequential high-definition captions
    raw_sentences = [s.strip() for s in script_text.replace("—", ", ").split('.') if s.strip()]
    total_words = sum(len(s.split()) for s in raw_sentences)
    if total_words == 0:
        total_words = 1

    caption_clips = []
    current_time = 0.0

    for sentence in raw_sentences:
        sentence_words = len(sentence.split())
        chunk_duration = (sentence_words / total_words) * total_duration
        if chunk_duration < 1.5:
            chunk_duration = 1.5

        # High-definition text rendering (using a semi-transparent dark backdrop box or high contrast styling for clarity)
        txt_clip = TextClip(
            sentence, 
            fontsize=46, 
            color='white', 
            font='Arial-Bold',
            size=(1100, 400),
            method='caption',
            align='center',
            stroke_color='black',
            stroke_width=2  # Adds a crisp clean outline for high legibility
        ).set_start(current_time).set_duration(chunk_duration).set_position('center')

        caption_clips.append(txt_clip)
        current_time += chunk_duration

    if caption_clips and current_time > total_duration:
        excess = current_time - total_duration
        caption_clips[-1] = caption_clips[-1].set_duration(max(1.0, caption_clips[-1].duration - excess))

    # Composite final video
    video = CompositeVideoClip([bg_clip] + caption_clips)
    video = video.set_audio(final_audio)

    video.write_videofile(
        "final_video.mp4", 
        fps=24, 
        codec='libx264', 
        audio_codec='aac',
        bitrate="4000k"
    )
    print("Video generated and saved successfully as final_video.mp4!")

    # 5. Upload to YouTube
    print("Starting YouTube upload process...")
    upload_to_youtube(
        file_path="final_video.mp4", 
        title="The Quiet Elevation: The True Power of Servant Leadership 🌿", 
        description=f"{script_text}\n\n#ServantLeadership #Leadership #Inspiration #FaithAndLeadership"
    )
    print("YouTube automation workflow completed entirely!")

if __name__ == "__main__":
    main()
