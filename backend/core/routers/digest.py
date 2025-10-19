from ninja import Router, Schema
from typing import List, Optional
from datetime import date
from ..models import DailyDigest, Video
from ..tasks import build_daily_digest

digest_router = Router()

# Build schemas for the input to a digest-create and, conversely, what should be returned
# when we attempt to retrieve digest data.

class DigestCreateSchema(Schema):
    video_ids: List[int]

class DigestSchema(Schema):
    id: int
    digest_date: date
    status: str
    audio_url: Optional[str] = None
    summary_text: Optional[str] = None
    video_ids: List[int]

    @staticmethod
    def resolve_video_ids(obj: DailyDigest):
        return [video.id for video in obj.videos.all()]

@digest_router.post("/", response={202: DigestSchema})
def create_digest(request, payload: DigestCreateSchema):
    """
    Create a new daily digest from a specified set of video IDs.
    """

    digest = DailyDigest.objects.create()
    videos = Video.objects.filter(id__in=payload.video_ids)

    digest.videos.set(videos)
    build_daily_digest.delay(digest.id)  # Perform the Celery task.
    
    # 202: We've received and accepted the request for processing, but that processing
    # is not yet complete (continues to run silently after-the-fact).
    return 202, digest

@digest_router.get("/", response=List[DigestSchema])
def list_digests(request):
    """
    List all of the daily digests we've accumulated.
    """

    return DailyDigest.objects.all()

@digest_router.get("/{digest_id}", response=DigestSchema)
def get_digest(request, digest_id: int):
    """
    Extract digest data attached to a particular digest ID.
    """

    return DailyDigest.objects.get(id=digest_id)
