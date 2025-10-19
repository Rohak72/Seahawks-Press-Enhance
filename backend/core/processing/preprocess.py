import ffmpeg
import os

def audio_enhance(input_file: str, output_file: str, model_path: str = "sh.rnnn", denoise_mix: float = 0.9,
                  speech_expansion: float = 25.0, safety_limit_db: float = -1.0):
    """
    Enhance raw audio by passing it through multiple intelligent filtration techniques.
    """

    # Get the absolute path to the core/processing directory.
    script_dir = os.path.dirname(os.path.abspath(__file__))

    # Append the absolute path directory prefix to the in-house model file.
    model_path = os.path.join(script_dir, "sh.rnnn")
    print(model_path)

    # Raise an exception if the RNN model isn't available in the prescribed path.
    if not os.path.exists(model_path):
        print(f"Model file not found: {model_path}!")
        return

    print("Running advanced speech enhancement pipeline...")
    stream = ffmpeg.input(input_file).audio

    # Stage 1: AI Denoiser & Distraction Removal
    # Purpose: Leverage the RNNoise noise suppression algorithm to distinguish human speech from
    # everything else and remove the extraneous parts accordingly.
    # Notes:
    #   - 'mix' determines the strength of the transformation.
    stream = stream.filter("arnndn", m=model_path, mix=denoise_mix)

    # Stage 2: Speech Volume Normalization
    # Purpose: Intelligently boost the quieter reporter snippets without affecting the already-loud parts.
    # After the clean signal produced by stage 1, this consistent gain can be found a lot quicker.
    # Notes:
    #   - 'e' controls how much to "expand" the volume of quieter sounds.
    #   - 'r' regulates the rise/fall dynamics, how quickly the filter reacts to volume changes.
    #   - Here, a low 'r' value was used to adapt to the fast-moving Q&A format and moderate
    #     expansion allowed the lowpass reporter mics to be picked up on.
    stream = stream.filter("speechnorm", e=speech_expansion, r=0.001)

    # Stage 3: Protective Safety Limiter
    # Purpose: Catch any sudden loud peaks that might cause distortion or clipping. Acts as the final
    # clean-up stage to remove any inconsistencies from the prior filters. Also sets a hard brickwall
    # limit on the audio's maximum volume.
    # Notes:
    #   - 'limit' sets a ceiling or upper bound on how loud the volume can get.
    #   - 'attack' resembles how fast the limiter cracks down on a loud sound.
    #   - 'release' controls how fast the limiter lets go after sound is quiet again.
    #   - Input/output levels are kept neutral.
    stream = stream.filter(
        "alimiter",
        level_in="1",
        level_out="1",
        limit=f"{safety_limit_db}dB",
        attack="5",
        release="50",
    )

    # Stage 4: Final Standardization for Whisper
    # WAV is an uncompressed audio format (for max quality); mono audio and 16Hz sample rate Whisper expects.
    print(f"Applying final standardization and saving to {output_file}...")
    stream = stream.output(
        output_file, format="wav", acodec="pcm_s16le", ac=1, ar="16k"
    ).overwrite_output()

    try:
        stream.run(capture_stdout=True, capture_stderr=True)
        print("Pipeline complete.")
    except ffmpeg.Error as e:
        print("An error occurred during preprocessing:")
        print(e.stderr.decode())
        raise

'''
Sample Testing Code:

input_filename = "sample.mp3"
output_filename = "enhanced.wav"

audio_enhance(input_filename, output_filename)
'''
