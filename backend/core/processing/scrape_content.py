from dotenv import load_dotenv
import requests
import os

load_dotenv()

CHANNEL_ID = "UCePXu-1RLT0s6EE0Dh0JqgQ"
PLAYLIST_ID = "PLtY4N4jspn1KKnRp1TjSNZey21leiTMjj"
API_KEY = os.getenv("YOUTUBE_API_KEY")

# Alternative method of extracting the videos from a given YT channel:
# https://www.googleapis.com/youtube/v3/channels?part=contentDetails&id={CHANNEL_ID}&key={API_KEY}

# Survey the top few videos from the press conference playlist.
URL = f"https://www.googleapis.com/youtube/v3/playlistItems?part=snippet,contentDetails&playlistId={PLAYLIST_ID}&key={API_KEY}"

# Parse the response JSON.
response = requests.get(URL)
for item in response.json()["items"]:
    print(item.get("contentDetails"))
    print()
