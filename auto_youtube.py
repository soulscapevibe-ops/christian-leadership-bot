import os
import random
import asyncio
import urllib.request
import moviepy.config as conf

# Force MoviePy to locate ImageMagick on the Linux GitHub runner
conf.IMAGEMAGICK_BINARY = "/usr/bin/convert"

from moviepy.editor import TextClip, CompositeVideoClip, VideoFileClip, AudioFileClip, CompositeAudioClip
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
import edge_tts

VOICE = "en-US-ChristopherNeural"

# Rotation pool of fresh, unique, high-impact Servant Leadership scripts for automated runs
SERVANT_LEADERSHIP_SCRIPTS = [
    (
        "The Quiet Elevation",
        "True leadership doesn't demand the spotlight. It builds the stage. "
        "It is a quiet strength—one that listens before it speaks, and measures success "
        "not by how high we climb, but by how many we lift along the way. "
        "Because when you lead with empathy, you don’t just direct the path. You clear it. "
        "To serve isn’t stepping down. It is the highest way to lead."
    ),
    (
        "Leading with a Servant's Heart",
        "Authority gives orders, but true influence earns trust. "
        "When you make your primary goal the growth and well-being of your team, everything changes. "
        "You stop managing tasks and start empowering people. "
        "A true leader removes obstacles so others can shine. "
        "Remember: greatness is found in the willingness to serve."
    ),
    (
        "The Strength of Empathy",
        "The most powerful leaders are those who are unafraid to be gentle. "
        "Leading through service means standing shoulder-to-shoulder with your people through every challenge. "
        "It means listening with patience, acting with integrity, and putting others first. "
        "When you elevate those around you, you rise together. "
        "True strength is measured by how well you serve."
    ),
    (
        "Building People, Not Just Projects",
        "Projects end, but people endure. "
        "A transactional leader focuses only on the output, but a servant leader invests in the person. "
        "By offering guidance, fostering encouragement, and offering a steady hand in difficult seasons, "
        "you create a legacy that outlasts any single achievement. "
        "Lead to serve, and watch your team flourish."
    ),
    (
        "The Art of Listening First",
        "Before a leader can guide a team forward, they must first understand where they stand. "
        "Servant leadership begins with deep, intentional listening. "
        "It values every voice, respects every perspective, and honors the unique strengths of every individual. "
        "When people know they are truly heard, they give their best. "
        "Lead with a heart of service today."
    )
]

# A pool of verified, high-definition, scenic natural landscape background video URLs
BACKGROUND_VIDEO_URLS = [
    "https://assets.mixkit.co/videos/preview/mixkit-sun-shining-through-the-trees-of-a-forest-4355-large.mp4",
    "https://assets.mixkit.co/videos/preview/mixkit-aerial-view-of-pine-forest-during-sunset-41650-large.mp4",
    "https://assets.mixkit.co/videos/preview/mixkit-forest-stream-in-the-sunlight-5296-large.mp4",
    "https://assets.mixkit.co/videos/preview/mixkit-waterfall-in-forest-surrounded-by-greenery-1215-large.mp4"
]

# Royalty-free soft ambient background music loop
BACKGROUND_MUSIC_URL = "https://actions.google.com/sounds/v1/ambiences/morning_birds.ogg" 

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

    # 1. Pick a fresh, unique script and background video for this automation run
    video_title, script_text = random.choice(SERVANT_LEADERSHIP_SCRIPTS)
    selected_bg_url = random.choice(BACKGROUND_VIDEO_URLS)

    print(f"Selected Video Title: {video_title}")
    print(f"Selected Script: {script_text[:60]}...")

    # 2. Create Voiceover Audio & Download Assets
    loop = asyncio.get_event_loop()
    loop.run_until_complete(generate_voiceover(script_text, "voiceover.mp3"))

    download_file(selected_bg_url, "background.mp4")
    download_file(BACKGROUND_MUSIC_URL, "bg_music.ogg")

    # 3. Render video with MoviePy (Crisp HD Text, Scenic Video Motion, and Audio Mixing)
    print("Starting video composition with MoviePy...")
    
    voiceover_audio = AudioFileClip("voiceover.mp3")
    total_duration = voiceover_audio.duration

    # Setup background video with a slow, cinematic zoom effect
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

        # HIGH RESOLUTION TEXT FIX: Using larger font size, high-contrast colors, and bold stroke for maximum clarity
        txt_clip = TextClip(
            sentence, 
            fontsize=64, 
            color='white', 
            font='Arial-Bold',
            size=(1150, 500),
            method='caption',
            align='center',
            stroke_color='black',
            stroke_width=3
        ).set_start(current_time).set_duration(chunk_duration).set_position('center')

        caption_clips.append(txt_clip)
        current_time += chunk_duration

    if caption_clips and current_time > total_duration:
        excess = current_time - total_duration
        caption_clips[-1] = caption_clips[-1].set_duration(max(1.0, caption_clips[-1].duration - excess))

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

    # 4. Upload to YouTube with fresh titles and tags
    print("Starting YouTube upload process...")
    upload_to_youtube(
        file_path="final_video.mp4", 
        title=f"{video_title} | Servant Leadership Inspiration 🌿", 
        description=f"{script_text}\n\n#ServantLeadership #Leadership #Inspiration #FaithAndLeadership"
    )
    print("YouTube automation workflow completed entirely!")

if __name__ == "__main__":
    main()
