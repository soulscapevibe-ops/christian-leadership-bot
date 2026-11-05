import os
import random
import asyncio
import urllib.request
import moviepy.config as conf

# Force MoviePy to locate ImageMagick on the Linux GitHub runner
conf.IMAGEMAGICK_BINARY = "/usr/bin/convert"

from moviepy.editor import TextClip, CompositeVideoClip, VideoFileClip, AudioFileClip, CompositeAudioClip, ColorClip
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
import edge_tts
from PIL import Image, ImageDraw, ImageFont, ImageEnhance

VOICE = "en-US-ChristopherNeural"

# Rotation pool with custom thumbnail text and matching high-res scenic image URLs
SERVANT_LEADERSHIP_LIBRARY = [
    {
        "title": "The Quiet Elevation | The Power of Servant Leadership 🌿",
        "script": (
            "True leadership doesn't demand the spotlight. It builds the stage. "
            "It is a quiet strength—one that listens before it speaks, and measures success "
            "not by how high we climb, but by how many we lift along the way. "
            "Because when you lead with empathy, you don’t just direct the path. You clear it. "
            "To serve isn’t stepping down. It is the highest way to lead."
        ),
        "keywords": "servant leadership, quiet strength, leadership inspiration, empathetic leadership, Christian leadership, lead to serve",
        "hashtags": "#ServantLeadership #LeadershipInspiration #QuietStrength #EmpathyInLeadership #FaithAndLeadership",
        "thumb_text": "LIFT OTHERS",
        "thumb_bg_image": "https://images.unsplash.com/photo-1506744038136-46273834b3fb?w=1280&q=80" # Scenic mountain landscape
    },
    {
        "title": "Leading with a Servant's Heart | Empower Your Team 🌟",
        "script": (
            "Authority gives orders, but true influence earns trust. "
            "When you make your primary goal the growth and well-being of your team, everything changes. "
            "You stop managing tasks and start empowering people. "
            "A true leader removes obstacles so others can shine. "
            "Remember: greatness is found in the willingness to serve."
        ),
        "keywords": "servant heart, empowering people, leadership trust, team growth, servant leadership principles, inspiring leaders",
        "hashtags": "#ServantHeart #EmpowerOthers #LeadershipMindset #ServantLeadership #TeamBuilding",
        "thumb_text": "THE HIGHEST\nWAY",
        "thumb_bg_image": "https://images.unsplash.com/photo-1499750310107-5fef28a66643?w=1280&q=80" # Warm study/desk aesthetic
    },
    {
        "title": "The Strength of Empathy in Leadership 🌱",
        "script": (
            "The most powerful leaders are those who are unafraid to be gentle. "
            "Leading through service means standing shoulder-to-shoulder with your people through every challenge. "
            "It means listening with patience, acting with integrity, and putting others first. "
            "When you elevate those around you, you rise together. "
            "True strength is measured by how well you serve."
        ),
        "keywords": "empathy in leadership, gentle strength, leading with integrity, supportive leadership, servant leadership motivation",
        "hashtags": "#Empathy #LeadershipMotivation #ServantLeadership #LeadingWithGrace #InspirationalQuotes",
        "thumb_text": "QUIET STRENGTH",
        "thumb_bg_image": "https://images.unsplash.com/photo-1448375240586-882707db888b?w=1280&q=80" # Sunlit forest pathway
    }
]

BACKGROUND_VIDEO_URLS = [
    "https://commondatastorage.googleapis.com/gtv-videos-bucket/sample/ForBiggerBlazes.mp4",
    "https://commondatastorage.googleapis.com/gtv-videos-bucket/sample/ForBiggerEscapes.mp4"
]

BACKGROUND_MUSIC_URL = "https://actions.google.com/sounds/v1/ambiences/morning_birds.ogg" 

async def generate_voiceover(text, output_filename="voiceover.mp3"):
    print("Generating AI voiceover...")
    communicate = edge_tts.Communicate(text, VOICE)
    await communicate.save(output_filename)
    print("Voiceover generated successfully!")

def generate_photographic_thumbnail(image_url, thumb_text, output_filename="thumbnail.jpg"):
    print("Generating custom photographic SEO thumbnail...")
    raw_img_path = "raw_thumb_bg.jpg"
    
    # 1. Download the scenic background image for the thumbnail
    success = download_file(image_url, raw_img_path)
    
    width, height = 1280, 720
    if success and os.path.exists(raw_img_path):
        image = Image.open(raw_img_path).convert("RGB")
        image = image.resize((width, height), Image.Resampling.LANCZOS)
        
        # Apply a subtle dark gradient/dimmer overlay so the white text pops clearly
        enhancer = ImageEnhance.Brightness(image)
        image = enhancer.enhance(0.65) # Darken slightly for readability
    else:
        # Fallback solid background if image download fails
        image = Image.new("RGB", (width, height), color=(15, 23, 42))

    draw = ImageDraw.Draw(image)

    # Try loading a bold font, fallback to default if unavailable
    try:
        font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 85)
    except IOError:
        font = ImageFont.load_default()

    # Center text calculation
    try:
        bbox = draw.multiline_textbbox((0, 0), thumb_text, font=font, spacing=15, align="center")
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]
    except AttributeError:
        text_width, text_height = 500, 150

    x = (width - text_width) / 2
    y = (height - text_height) / 2

    # Draw soft shadow for professional depth matching your uploaded style
    draw.multiline_text((x + 3, y + 3), thumb_text, font=font, fill=(0, 0, 0), spacing=15, align="center")
    # Draw crisp white text
    draw.multiline_text((x, y), thumb_text, font=font, fill=(255, 255, 255), spacing=15, align="center")

    image.save(output_filename, "JPEG", quality=95)
    print("Photographic SEO thumbnail created successfully!")

def download_file(url, output_filename):
    print(f"Downloading asset from {url}...")
    try:
        req = urllib.request.Request(
            url, 
            headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
        )
        with urllib.request.urlopen(req) as response, open(output_filename, 'wb') as out_file:
            out_file.write(response.read())
        
        if os.path.exists(output_filename) and os.path.getsize(output_filename) > 10000:
            return True
        return False
    except Exception as e:
        print(f"Failed to download {output_filename}: {e}")
        return False

def upload_to_youtube(video_path, thumb_path, title, description, tags):
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
            "tags": [tag.strip() for tag in tags.split(',')],
            "categoryId": "22"
        },
        "status": {
            "privacyStatus": "public"
        }
    }

    print(f"Preparing video upload for: {video_path}")
    media = MediaFileUpload(video_path, chunksize=-1, resumable=True)
    request = youtube.videos().insert(part="snippet,status", body=body, media_body=media)
    
    response = None
    while response is None:
        status, response = request.next_chunk()
        if status:
            print(f"Uploaded {int(status.progress() * 100)}%.")
            
    video_id = response.get('id')
    print(f"Video successfully uploaded! YouTube Video ID: {video_id}")

    if os.path.exists(thumb_path):
        print("Uploading custom photographic thumbnail...")
        try:
            youtube.thumbnails().set(
                videoId=video_id,
                media_body=MediaFileUpload(thumb_path)
            ).execute()
            print("Custom thumbnail assigned successfully via YouTube API!")
        except Exception as e:
            print(f"Failed to upload thumbnail: {e}")

def main():
    print("Starting YouTube automation script...")

    content_item = random.choice(SERVANT_LEADERSHIP_LIBRARY)
    video_title = content_item["title"]
    script_text = content_item["script"]
    video_keywords = content_item["keywords"]
    video_hashtags = content_item["hashtags"]
    thumb_text = content_item["thumb_text"]
    thumb_bg_image = content_item["thumb_bg_image"]

    selected_bg_url = random.choice(BACKGROUND_VIDEO_URLS)

    print(f"Selected Title: {video_title}")

    loop = asyncio.get_event_loop()
    loop.run_until_complete(generate_voiceover(script_text, "voiceover.mp3"))

    generate_photographic_thumbnail(thumb_bg_image, thumb_text, "thumbnail.jpg")
    video_downloaded = download_file(selected_bg_url, "background.mp4")
    download_file(BACKGROUND_MUSIC_URL, "bg_music.ogg")

    print("Starting video composition with MoviePy...")
    
    voiceover_audio = AudioFileClip("voiceover.mp3")
    total_duration = voiceover_audio.duration

    bg_clip = None
    if video_downloaded:
        try:
            bg_video = VideoFileClip("background.mp4")
            if bg_video.duration < total_duration:
                loops_needed = int(total_duration // bg_video.duration) + 1
                bg_video = bg_video.loop(n=loops_needed)
            
            bg_clip = bg_video.subclip(0, total_duration).resize(lambda t: 1.0 + 0.04 * (t / total_duration))
            bg_clip = bg_clip.set_fps(24).crop(x_center=bg_clip.w/2, y_center=bg_clip.h/2, width=1280, height=720)
        except Exception as e:
            print(f"Error processing background video: {e}")

    if bg_clip is None:
        bg_clip = ColorClip(size=(1280, 720), color=(20, 35, 50), duration=total_duration)

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
    print("Video generated successfully!")

    print("Starting YouTube upload and thumbnail assignment...")
    full_description = f"{script_text}\n\n{video_hashtags}"
    
    upload_to_youtube(
        video_path="final_video.mp4",
        thumb_path="thumbnail.jpg",
        title=video_title, 
        description=full_description,
        tags=video_keywords
    )
    print("YouTube automation workflow completed entirely!")

if __name__ == "__main__":
    main()
