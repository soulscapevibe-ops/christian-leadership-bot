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
from PIL import Image, ImageDraw, ImageFont

VOICE = "en-US-ChristopherNeural"

# Rotation pool of fresh Servant Leadership scripts paired with custom SEO metadata and thumbnail themes
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
        "thumb_text": "THE QUIET\nELEVATION",
        "thumb_bg": (15, 23, 42)     # Deep Navy
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
        "thumb_text": "SERVANT'S\nHEART",
        "thumb_bg": (20, 40, 30)     # Deep Forest Green
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
        "thumb_text": "STRENGTH OF\nEMPATHY",
        "thumb_bg": (30, 25, 45)     # Deep Slate Purple
    },
    {
        "title": "Building People, Not Just Projects | Leadership Focus 💡",
        "script": (
            "Projects end, but people endure. "
            "A transactional leader focuses only on the output, but a servant leader invests in the person. "
            "By offering guidance, fostering encouragement, and offering a steady hand in difficult seasons, "
            "you create a legacy that outlasts any single achievement. "
            "Lead to serve, and watch your team flourish."
        ),
        "keywords": "building people, legacy leadership, people over projects, investing in teams, servant leadership coaching",
        "hashtags": "#PeopleFirst #LeadershipLegacy #ServantLeadership #TeamSuccess #InspirationalLeadership",
        "thumb_text": "BUILDING\nPEOPLE",
        "thumb_bg": (40, 25, 20)     # Deep Bronze
    },
    {
        "title": "The Art of Listening First | Core Leadership Skill 🎧",
        "script": (
            "Before a leader can guide a team forward, they must first understand where they stand. "
            "Servant leadership begins with deep, intentional listening. "
            "It values every voice, respects every perspective, and honors the unique strengths of every individual. "
            "When people know they are truly heard, they give their best. "
            "Lead with a heart of service today."
        ),
        "keywords": "listening first, intentional listening, respectful leadership, valuing every voice, servant leadership fundamentals",
        "hashtags": "#ActiveListening #LeadershipSkills #ServantLeadership #ValuePeople #GrowthMindset",
        "thumb_text": "THE ART OF\nLISTENING",
        "thumb_bg": (20, 35, 50)     # Deep Ocean Blue
    }
]

BACKGROUND_VIDEO_URLS = [
    "https://commondatastorage.googleapis.com/gtv-videos-bucket/sample/ForBiggerBlazes.mp4",
    "https://commondatastorage.googleapis.com/gtv-videos-bucket/sample/ForBiggerEscapes.mp4",
    "https://commondatastorage.googleapis.com/gtv-videos-bucket/sample/ForBiggerFun.mp4"
]

BACKGROUND_MUSIC_URL = "https://actions.google.com/sounds/v1/ambiences/morning_birds.ogg" 

async def generate_voiceover(text, output_filename="voiceover.mp3"):
    print("Generating AI voiceover...")
    communicate = edge_tts.Communicate(text, VOICE)
    await communicate.save(output_filename)
    print("Voiceover generated successfully!")

def generate_thumbnail(thumb_text, bg_color, output_filename="thumbnail.jpg"):
    print("Generating SEO thumbnail...")
    # YouTube recommended dimensions: 1280x720
    width, height = 1280, 720
    image = Image.new("RGB", (width, height), color=bg_color)
    draw = ImageDraw.Draw(image)

    # Add a subtle glowing border/frame for professional contrast
    draw.rectangle([20, 20, width - 20, height - 20], outline=(255, 255, 255), width=4)

    # Load a standard system font or fallback gracefully
    try:
        # Linux runner font path check
        font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 90)
    except IOError:
        font = ImageFont.load_default()

    # Center text dynamically
    # Use textbbox for modern Pillow versions
    try:
        bbox = draw.multiline_textbbox((0, 0), thumb_text, font=font, spacing=20, align="center")
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]
    except AttributeError:
        text_width, text_height = 600, 200

    x = (width - text_width) / 2
    y = (height - text_height) / 2

    # Draw subtle drop shadow for high readability
    draw.multiline_text((x + 4, y + 4), thumb_text, font=font, fill=(0, 0, 0), spacing=20, align="center")
    # Draw main crisp white text
    draw.multiline_text((x, y), thumb_text, font=font, fill=(255, 255, 255), spacing=20, align="center")

    image.save(output_filename, "JPEG", quality=95)
    print("SEO thumbnail generated successfully as thumbnail.jpg!")

def download_file(url, output_filename):
    print(f"Downloading asset from {url}...")
    try:
        req = urllib.request.Request(
            url, 
            headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
        )
        with urllib.request.urlopen(req) as response, open(output_filename, 'wb') as out_file:
            out_file.write(response.read())
        
        if os.path.exists(output_filename) and os.path.getsize(output_filename) > 50000:
            print(f"Successfully downloaded {output_filename}")
            return True
        else:
            print(f"Downloaded file {output_filename} is invalid.")
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

    # 1. Upload Video
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

    # 2. Upload Custom Thumbnail
    if os.path.exists(thumb_path):
        print("Uploading custom SEO thumbnail...")
        try:
            youtube.thumbnails().set(
                videoId=video_id,
                media_body=MediaFileUpload(thumb_path)
            ).execute()
            print("Custom SEO thumbnail uploaded successfully!")
        except Exception as e:
            print(f"Failed to upload thumbnail: {e}")

def main():
    print("Starting YouTube automation script...")

    # 1. Select content bundle
    content_item = random.choice(SERVANT_LEADERSHIP_LIBRARY)
    video_title = content_item["title"]
    script_text = content_item["script"]
    video_keywords = content_item["keywords"]
    video_hashtags = content_item["hashtags"]
    thumb_text = content_item["thumb_text"]
    thumb_bg = content_item["thumb_bg"]

    selected_bg_url = random.choice(BACKGROUND_VIDEO_URLS)

    print(f"Selected Title: {video_title}")

    # 2. Generate Voiceover, Thumbnail & Download Assets
    loop = asyncio.get_event_loop()
    loop.run_until_complete(generate_voiceover(script_text, "voiceover.mp3"))

    generate_thumbnail(thumb_text, thumb_bg, "thumbnail.jpg")
    video_downloaded = download_file(selected_bg_url, "background.mp4")
    download_file(BACKGROUND_MUSIC_URL, "bg_music.ogg")

    # 3. Render video with MoviePy
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

    # 4. Upload Video and Custom Thumbnail to YouTube
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
