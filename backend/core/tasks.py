from celery import shared_task, group
from django.conf import settings
from .models import Video, DailyDigest

# Imports all of the service functions feature-by-feature (i.e. processing, llm, rag, tts).
from .processing.youtube_utils import download_yt_audio, extract_video_metadata
from .processing.preprocess import audio_enhance
from .processing.transcribe import run_whisperx
from .processing.ner_utils import infer_person_from_title
from .llm.services import generate_video_summary, generate_master_summary
from .rag.services import create_video_embeddings
from .tts.services import produce_tts_audio

import uuid
import os

@shared_task
def process_video_pipeline(video_id):
    """
    The main, multi-stage asynchronous pipeline for processing a single video, including
    metadata extraction, audio preprocessing, WhisperX transcription, LLM calls for intelligent
    summaries, and a final post-hoc RAG enrichment task that runs in the background.
    """

    job_id = str(uuid.uuid4())  # Assign a unique job ID for file prefixing.
    original_audio_path = None
    enhanced_audio_path = None

    try:
        video = Video.objects.get(id=video_id)

        # For the selected video, we pull out all of the semantic details and assign
        # them to the appropriate model attributes.
        metadata = extract_video_metadata(video.youtube_url)
        if metadata:
            video.title = metadata.get("title")
            video.thumbnail_url = metadata.get("thumbnail_url")
            video.published_at = metadata.get("published_at")

            # If the video title is available, we leverage spaCy Named Entity Recognition (NER)
            # to dynamically infer the speaker/subject of the press conference.
            if video.title:
                speaker_name = infer_person_from_title(video.title)
                if speaker_name:
                    video.speaker = speaker_name

        video.status = 'PROCESSING'
        video.save()

        # Set up the audio file paths to be stored in a reserved /tmp directory.
        tmp_dir = os.path.join(settings.BASE_DIR, 'tmp')
        original_audio_path = os.path.join(tmp_dir, f"{job_id}_original.mp3")
        enhanced_audio_path = os.path.join(tmp_dir, f"{job_id}_enhanced.wav")

        # Extract the MP3 audio via Pytube, then pass it through the RNNoise and FFmpeg filters
        # to end up with a 16Hz '...enhanced.wav' file that can be plugged into WhisperX.
        download_yt_audio(video.youtube_url, original_audio_path)
        audio_enhance(original_audio_path, enhanced_audio_path)

        # Compile a word-segment transcript and pass the full text into an LLM for summary.
        transcript_dictionary = run_whisperx(enhanced_audio_path)
        full_text = " ".join(seg['text'] for seg in transcript_dictionary['segments'])
        summary = generate_video_summary(full_text)

        if 'error' in summary:
            raise Exception(f"LLM summary generation failed with error {summary['error']}.")
        
        # Update the relevant model fields, along with their status in the PostgreSQL DB.
        video.transcript_data = transcript_dictionary
        video.summary_data = summary
        video.status = 'COMPLETED'
        video.save()

        # In this post-processing fan-out step, we trigger a "fire and forget" async operation
        # to add the newly-processed video to the RAG index/embeddings.
        print(f"Triggering post-processing enrichment tasks for video {video_id}...")
        enrichment_tasks = group(develop_rag_embeddings.s(video_id))
        enrichment_tasks.apply_async()

    except Exception as e:
        video_to_fail = Video.objects.get(id=video_id)
        video_to_fail.status = 'FAILED'
        video_to_fail.save()

        print(f"Process task failed for video {video_id}: {e}.")
    
    finally:
        # Ensures temporary audio files are cleaned up (regardless of success/failure).
        print("Running cleanup...")
        if original_audio_path and os.path.exists(original_audio_path):
            print(f"Deleting temporary file (1/2): {original_audio_path}.")
            os.remove(original_audio_path)
        if enhanced_audio_path and os.path.exists(enhanced_audio_path):
            print(f"Deleting temporary file (2/2): {enhanced_audio_path}.")
            os.remove(enhanced_audio_path)

@shared_task
def develop_rag_embeddings(video_id: int):
    """
    Invokes the RAG embedding service to index a video's transcript.
    """

    print(f"RAG Task: received job for Video ID: {video_id}.")
    create_video_embeddings(video_id)

@shared_task
def build_daily_digest(digest_id: int):
    """
    Synthesizes multiple video summaries into a single daily digest (on-demand), using
    the Google Text-to-Speech API for lifelike speech synthesis.
    """

    # Set up the new digest object and initialize its status to processing.
    print(f"RAG Task: received job for Digest ID: {digest_id}.")
    digest = DailyDigest.objects.get(id=digest_id)
    digest.status = 'PROCESSING'
    digest.save()

    audio_file_path = None
    try:
        # Compile and aggregate video summaries via loop comprehension.
        video_summaries = [v.summary_data['one_sentence_summary'] 
                           for v in digest.videos.all() 
                           if v.summary_data and 'one_sentence_summary' in v.summary_data]
        
        if not video_summaries:
            raise ValueError("Cannot create a digest -- no video summaries found.")
        
        master_summary = generate_master_summary(video_summaries)

        # As with the YouTube audio artifacts, shelve the TTS audio result onto /tmp.
        audio_filename = f"{uuid.uuid4()}.mp3"
        tmp_dir = os.path.join(settings.BASE_DIR, 'tmp')
        audio_file_path = os.path.join(tmp_dir, audio_filename)

        produce_tts_audio(master_summary, audio_file_path)

        # Populate the digest model fields and execute the DB save.
        digest.summary_text = master_summary
        digest.audio_url = audio_file_path
        digest.status = 'COMPLETED'
        digest.save()
        print(f"Daily digest {digest_id} completed successfully!")

    except Exception as e:
        digest.status = 'FAILED'
        digest.save()
        print(f"Daily digest task failed for digest ID {digest_id}!")
