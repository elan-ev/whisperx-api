import logging
import os
from time import time
from typing import Dict, Optional, Any

import requests
from celery import Celery
from celery.signals import setup_logging

from src.api.config import BROKER_URL
from src.api.models import WebhookStatusEnum
from src.utils.file_utils import (
    convert_to_mp3,
    has_audio_streams,
    read_output_files,
    download_file_from_url,
)
from src.utils.transcription_utils import run_whisperx

# Configure Celery
celery_app = Celery(
    "whisperx-tasks", backend="db+sqlite:///celery.db", broker=BROKER_URL
)

# Configure logging
logger = logging.getLogger("whisperx-api")

@setup_logging.connect
def configure_celery_logging(**kwargs):
    # Suppress task success logging
    logging.getLogger("celery.app.trace").setLevel(logging.INFO)


def send_webhook(url: Optional[str], data: Dict[str, Any]) -> None:
    """
    Send webhook notification to the specified URL.

    Args:
        url: The webhook URL to send the notification to
        data: The data to send in the webhook payload
    """
    if not url:
        return

    timeout = 10
    try:
        response = requests.post(url, json=data, timeout=timeout)
        status = data.get("status", "unknown")
        logger.info(f"Webhook notification ({status}) sent to {url}, status code: {response.status_code}")
    except requests.Timeout:
        logger.error(f"Webhook request to {url} timed out after {timeout} seconds")
    except Exception as exception:
        logger.error(f"Failed to send webhook to {url}: {str(exception)}")


def cleanup_temp_files(video_path: Optional[str], mp3_path: Optional[str]) -> None:
    """
    Clean up temporary files created during transcription.

    Args:
        video_path: Path to the temporary video file
        mp3_path: Path to the temporary MP3 file
    """
    try:
        if video_path and os.path.exists(video_path):
            os.remove(video_path)
            logger.info(f"Cleaned up temporary video file: {video_path}")

        if mp3_path and os.path.exists(mp3_path):
            os.remove(mp3_path)
            logger.info(f"Cleaned up temporary mp3 file: {mp3_path}")
    except Exception as cleanup_error:
        logger.warning(f"Failed to clean up temporary files: {str(cleanup_error)}")


@celery_app.task(name="transcribe_file", bind=True)
def transcribe_file(
    self,
    file_url: str,
    lang: str,
    model: str,
    min_speakers: int = 0,
    max_speakers: int = 0,
    prompt: Optional[str] = None,
    webhook_url: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Celery task to transcribe an audio/video file.

    Args:
        file_url: URL to download the file from
        lang: Language code for transcription
        model: Model to use for transcription
        min_speakers: Minimum number of speakers to detect
        max_speakers: Maximum number of speakers to detect
        prompt: Optional prompt to guide transcription
        webhook_url: URL to send status updates to

    Returns:
        Dictionary containing transcription results and metadata
    """
    task_id = self.request.id
    temp_video_path = None
    temp_mp3_path = None

    try:
        logger.info(f"Starting transcription task {task_id} for file URL: {file_url}")
        send_webhook(
            webhook_url, {"id": task_id, "status": WebhookStatusEnum.starting}
        )

        # Download file
        logger.info(f"Downloading file from URL: {file_url}")
        temp_video_path = download_file_from_url(file_url)

        if not os.path.exists(temp_video_path):
            error_msg = f"File not found after download: {temp_video_path}"
            logger.error(error_msg)
            raise FileNotFoundError(error_msg)

        # Convert to MP3
        logger.info("Converting video to mp3...")

        if not has_audio_streams(temp_video_path):
            raise Exception("No audio stream found in file")

        temp_mp3_path = convert_to_mp3(temp_video_path)
        base_name = os.path.splitext(os.path.basename(temp_mp3_path))[0]

        logger.info(
            f"Starting transcription for file: {base_name}"
        )
        send_webhook(
            webhook_url, {"id": task_id, "status": WebhookStatusEnum.processing}
        )

        # Run transcription
        start_time = time()
        run_whisperx(temp_mp3_path, lang, model, min_speakers, max_speakers, prompt)
        exec_time = time() - start_time
        logger.info(f"Transcription completed in {exec_time:.2f}s for file: {base_name}")

        # Process results
        output_files = read_output_files(base_name)
        logger.info(f"Successfully read output files for {base_name}")

        # Prepare result
        result = {
            "id": task_id,
            "error": None,
            "output": {
                "vtt_content": output_files["vtt_content"],
                "txt_content": output_files["txt_content"],
                "json_content": output_files["json_content"],
                "srt_content": output_files["srt_content"],
                "vtt_path": output_files["vtt_path"],
                "txt_path": output_files["txt_path"],
                "json_path": output_files["json_path"],
                "srt_path": output_files["srt_path"],
            },
            "status": WebhookStatusEnum.succeeded,
            "metrics": {
                "predict_time": exec_time,
            },
            "webhook": webhook_url,
        }

        send_webhook(webhook_url, result)
        return result

    except Exception as exception:
        error_message = f"Transcription failed: {str(exception)}"
        logger.error(error_message)
        send_webhook(
            webhook_url,
            {
                "id": task_id,
                "status": WebhookStatusEnum.failed,
                "error": str(exception)
            }
        )
        raise exception
    finally:
        cleanup_temp_files(temp_video_path, temp_mp3_path)
