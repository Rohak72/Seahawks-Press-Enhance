from django.db import models

class Video(models.Model):
    """
    Represents the metadata and processed info associated with a single YouTube video.
    Note that there are also status and created/updated fields to track jobs as they come through.
    """

    # Core identifiers and fetched metadata (via YouTube Data v3 API).
    youtube_url = models.URLField(unique=True)
    title = models.CharField(max_length=255, blank=True)
    thumbnail_url = models.URLField(max_length=512, blank=True, null=True)
    published_at = models.DateTimeField(blank=True, null=True)
    speaker = models.CharField(max_length=100, blank=True, null=True)

    # Acting like a quasi-enum, this section defines the possible states of the video pipeline.
    STATUS_CHOICES = [
        ('PENDING', 'Pending'),
        ('PROCESSING', 'Processing'),
        ('COMPLETED', 'Completed'),
        ('FAILED', 'Failed')
    ]
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')

    # Flexible JSON fields to store the raw Whisper transcript and LLM-generated summaries.
    transcript_data = models.JSONField(null=True, blank=True)
    summary_data = models.JSONField(null=True, blank=True)

    # Bookkeeping for when the video model was created and most recently updated.
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    # Provides a readable to-string implementation for the Django admin.
    def __str__(self):
        return f"Title: {self.title} ({self.youtube_url})."

class DailyDigest(models.Model):
    """
    Captures a single, AI/TTS-generated audio digest compiled from a batch of videos.
    """

    # Records the date of the digest (very important for the client/user to know!).
    digest_date = models.DateField(auto_now_add=True)

    # Stores the final LLM master script and the path to the prepared audio file (on disc).
    summary_text = models.TextField(blank=True, null=True)
    audio_url = models.CharField(max_length=512, blank=True, null=True)
    status = models.CharField(max_length=20, default='PENDING')

    # This code creates a many-to-many relationship. A single Digest can be associated with many 
    # Videos, and a single Video could potentially be part of many Digests.
    videos = models.ManyToManyField(Video, related_name='digests')

    # Similar to the Video model, we include a string-form representation of the digest.
    def __str__(self):
        return f"Daily digest for {self.digest_date}."
    