from ninja import Schema, Router
from typing import List, Optional
from datetime import datetime
from ..models import Video
from ..tasks import process_video_pipeline

videos_router = Router()

# Define schemas for expected input on an API call to create/read.

class VideoCreateSchema(Schema):
    youtube_url: str

class VideoSchema(Schema):
    id: int
    youtube_url: str
    status: str
    speaker: Optional[str] = None
    title: Optional[str] = None
    thumbnail_url: Optional[str] = None
    published_at: Optional[datetime] = None
    summary_data: Optional[dict] = None
    transcript_data: Optional[dict] = None

@videos_router.post("/submitVideo", response={201: VideoSchema})
def submit_video(request, payload: VideoCreateSchema):
    """
    Submit a new video for processing.
    """

    video, created = Video.objects.get_or_create(youtube_url=payload.youtube_url)

    # Only retry if the video has status FAILED or PENDING (incomplete prior run).
    if video.status != 'PROCESSING' and video.status != 'COMPLETED':
        print(f"Submitting video {video.id} for processing.")
        video.status = 'PENDING'
        video.save()
        process_video_pipeline.delay(video.id)
    else:
        print(f"Video {video.id} is already processing or complete. Not submitting!")

    # 201: We've successfully created a new resource on the server in response to the
    # client's request, including the resource data on response.
    return 201, video

@videos_router.get("/listVideos", response=List[VideoSchema])
def list_videos(request):
    """
    List all of the videos that have been interacted with so far.
    """

    videos = Video.objects.all()
    return videos

@videos_router.get("/getVideoData/{video_id}", response=VideoSchema)
def get_video(request, video_id: int):
    """
    Retrieve video data for the given video ID.
    """

    video = Video.objects.get(id=video_id)
    return video
