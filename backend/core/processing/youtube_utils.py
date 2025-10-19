from django.conf import settings
from pytubefix import YouTube
from pytubefix.cli import on_progress
from pydub import AudioSegment
import requests
import io
import re

def download_yt_audio(url: str, output_path: str) -> str:
    """
    Retrieve .mp3 audio from a specified YouTube video URL.
    """

    try:
        yt = YouTube(url, on_progress_callback=on_progress)
        ys = yt.streams.get_audio_only()

        # Create an in-memory RAM buffer to avoid having to download an intermediate .m4a file.
        buffer = io.BytesIO()
        ys.stream_to_buffer(buffer)
        buffer.seek(0)

        # Load the audio from the buffer and coerce it into MP3.
        raw_audio = AudioSegment.from_file(buffer)
        # output_filename = os.path.splitext(ys.default_filename)[0] + ".mp3"
        raw_audio.export(output_path, format="mp3")

    except Exception as e:
        print(e)

    print(f"Audio saved to: {output_path}!")
    return output_path

def download_yt_video(url: str) -> str:
    """
    Download .mp4 video (no audio) from the given YouTube URL.
    """

    yt = YouTube(url, on_progress_callback=on_progress)    
    yt.streams.first().download("video.mp4")

    return "video.mp4"

def extract_video_metadata(url: str) -> dict:
    """
    Pull out all of the relevant metadata from the YouTube video.
    """

    print(f"Fetching video metadata from {url}!")

    # Reliably extract the Video ID from any URL format, using a regular expression
    # that handles both "watch?v=" and "youtu.be/" links.
    video_id_match = (
        re.search(r"(?<=v=)[\w-]+", url) or
        re.search(r"(?<=youtu\.be/)[\w-]+", url)
    )
    
    if not video_id_match:
        print("ERROR: Could not extract a valid YouTube Video ID from the URL.")
        return {}
    
    video_id = video_id_match.group(0)
    print(f"Extracted Video ID: {video_id}.")

    # Build the correct API URL to get data for this specific video.
    api_key = settings.YOUTUBE_API_KEY

    # We use the 'videos' endpoint with the 'snippet' part to get the metadata. Could also
    # use 'contentDetails' here but that pulls the description, which isn't that useful.
    api_url = f"https://www.googleapis.com/youtube/v3/videos?part=snippet&id={video_id}&key={api_key}"

    try:
        # Invoke the YouTube Data API and store the returned JSON.
        response = requests.get(api_url)
        response.raise_for_status()
        data = response.json()
        
        # Check if the 'items' list exists and has content.
        if not data.get("items"):
            print("ERROR: YouTube API returned no 'items' for this video.")
            return {}

        # The metadata is inside the 'snippet' object of the first item. Use it to safely
        # get the title, publication date, and best available thumbnail URL.
        snippet = data["items"][0]["snippet"]
        title = snippet.get("title", "Unknown Title")
        published_at = snippet.get("publishedAt")

        # It tries to find 'high', then 'medium', then 'default'.
        thumbnails = snippet.get("thumbnails", {})
        thumbnail_url = (
            thumbnails.get("high", {}) or
            thumbnails.get("medium", {}) or
            thumbnails.get("default", {})
        ).get("url")

        print(f"Successfully parsed title: {title}.")
        
        # Return a clean dictionary of the parsed JSON.
        return {
            "title": title,
            "thumbnail_url": thumbnail_url,
            "published_at": published_at,
        }

    except requests.exceptions.RequestException as e:
        print(f"ERROR: Failed to interface with YouTube API: {e}.")
        return {}
    