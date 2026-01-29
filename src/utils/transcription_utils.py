import subprocess
import logging

from src.api.config import HF_TOKEN, WHISPERX_API_DATA_PATH, WHISPERX_CPU_ONLY


def run_whisperx(temp_mp3_path, lang, model, min_speakers, max_speakers, prompt):
    output_dir = WHISPERX_API_DATA_PATH

    # Start building the base command
    cmd = [
        "whisperx",
        #"whisper",
        temp_mp3_path,
        "--model", model,
        "--vad_method", "silero",
        "--language", lang,
        "--output_format", "all",
        "--output_dir", output_dir,
        # whisperx option
        "--align_model", "WAV2VEC2_ASR_LARGE_LV60K_960H",
        "--verbose", "False"
    ]

    if WHISPERX_CPU_ONLY:
        cmd.extend(["--device", "cpu"])

    # Include the prompt if provided
    if prompt:
        prompt_with_quotes = f'"{prompt}"'
        cmd.extend(["--initial_prompt", prompt_with_quotes])

    # Add diarization options if applicable
    if min_speakers > 0 and max_speakers > 0:
        cmd.extend(["--hf_token", HF_TOKEN])
        cmd.extend([
            "--diarize",
            "--min_speakers", str(min_speakers),
            "--max_speakers", str(max_speakers)
        ])

    # Log the command for debugging
    print(f"WHISPERX COMMAND: {' '.join(cmd)}", flush=True)
    logging.info(f"Running whisperx command: {' '.join(cmd)}")

    # Run the command
    subprocess.run(cmd, check=True)
