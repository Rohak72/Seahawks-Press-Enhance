import whisperx
from whisperx.utils import get_writer

import os
import warnings
from dotenv import load_dotenv
from datetime import datetime
from django.conf import settings

warnings.filterwarnings("ignore")

load_dotenv()
start_time = datetime.now()

# Define global constants for Whisper functions.
DEVICE = "cpu"
BATCH_SIZE = 16               # Reduce if low on GPU mem.
COMPUTE_TYPE = "float32"      # Change to "int8" if low on GPU mem (may reduce accuracy).
HF_TOKEN = settings.HF_TOKEN  # Load HuggingFace token for speaker diarization.

def run_whisperx(audio_file_path, results_export=False):
    """
    Run the WhisperX ASR model end-to-end.
    """

    print(f"[{datetime.now()}] Checkpoint #1: Loading Whisper model and audio for transcription...")
    # 1: Transcribe with original Whisper (batched).
    model = whisperx.load_model("small", DEVICE, compute_type=COMPUTE_TYPE, language="en")
    audio = whisperx.load_audio(audio_file_path)
    result = model.transcribe(audio, batch_size=BATCH_SIZE)

    print(f"[{datetime.now()}] Checkpoint #2: Using phoneme recognition model to force-align and generate "
        "word-level timestamps...")

    # 2: Align whisper output.
    model_a, metadata = whisperx.load_align_model(
        language_code=result["language"], device=DEVICE
    )
    aligned_result = whisperx.align(result["segments"], model_a, metadata, audio, DEVICE, return_char_alignments=True)
    result.update(aligned_result)

    print(f"[{datetime.now()}] Checkpoint #3: Initializing output directory...")

    output_dir = "outputs/"
    os.makedirs(output_dir, exist_ok=True)

    print(f"[{datetime.now()}] Checkpoint #4: Executing speaker diarization pipeline...")

    # 3: Assign speaker labels.
    diarize_model = whisperx.diarize.DiarizationPipeline(use_auth_token=HF_TOKEN, device=DEVICE)
    diarize_segments = diarize_model(audio)  # Can optionally specify 'min_speakers' and 'max_speakers'.

    diarized_result = whisperx.assign_word_speakers(diarize_segments, result)
    result.update(diarized_result)

    # print(diarized_result["segments"]) => Debugging Output

    if results_export:
        print(f"[{datetime.now()}] Checkpoint #5: Writing results...")

        # 4: Work with the writer for export in various file formats.
        writer = get_writer("all", output_dir)
        writer_options = {
            "max_line_width": None,
            "max_line_count": None,
            "highlight_words": False,
        }
        writer(result, audio_file_path, writer_options)

    elapsed_time = datetime.now() - start_time
    total_seconds = elapsed_time.total_seconds()
    print("\nWhisperX has run successfully!")
    print(f"Total time elapsed: {int(total_seconds // 60)} minutes and {(total_seconds % 60):.2f} seconds.\n")

    return result
