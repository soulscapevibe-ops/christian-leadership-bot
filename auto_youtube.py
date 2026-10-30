import os
from google import genai
from moviepy.editor import TextClip, CompositeVideoClip, ColorClip, concatenate_videoclips

# Automatically looks for the GEMINI_API_KEY environment variable
client = genai.Client()

print("Client initialized successfully!")
# Add the rest of your automation logic below...
