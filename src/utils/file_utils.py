import os
import json
import subprocess
import uuid
import requests
import logging
from urllib.parse import urlparse
from zipfile import ZipFile
from io import BytesIO
from src.api.config import FFMPEG_BIN, FFPROBE_BIN, WHISPERX_API_DATA_PATH, WHISPERX_API_TEMP_PATH


def create_directories():
    if not os.path.exists(WHISPERX_API_TEMP_PATH):
        os.makedirs(WHISPERX_API_TEMP_PATH)
    if not os.path.exists(WHISPERX_API_DATA_PATH):
        os.makedirs(WHISPERX_API_DATA_PATH)


def has_audio_streams(file_path):
    command = [
        FFPROBE_BIN,
        "-v", "error",
        "-show_streams",
        "-print_format", "json",
        file_path,
    ]
    try:
        output = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True, text=True).stdout
        streams = json.loads(output).get("streams", [])
        return any(s.get("codec_type") == "audio" for s in streams)
    except (subprocess.CalledProcessError, json.JSONDecodeError):
        return False


def convert_to_mp3(file_path):
    temp_mp3_path = os.path.splitext(file_path)[0] + ".mp3"
    try:
        logging.info(f"Converting {file_path} to {temp_mp3_path}")
        subprocess.run([FFMPEG_BIN, "-y", "-i", file_path, temp_mp3_path], check=True)
        logging.info(f"Conversion to MP3 successful: {temp_mp3_path}")
    except subprocess.CalledProcessError as e:
        logging.error(f"ffmpeg conversion failed: {e}")
        raise
    return temp_mp3_path


def read_output_files(base_name):
    output_dir = WHISPERX_API_DATA_PATH
    vtt_path = f"{base_name}.vtt"
    txt_path = f"{base_name}.txt"
    json_path = f"{base_name}.json"
    srt_path = f"{base_name}.srt"

    with open(os.path.join(output_dir, vtt_path), "r") as vtt_file:
        vtt_content = vtt_file.read()

    with open(os.path.join(output_dir, txt_path), "r") as txt_file:
        txt_content = txt_file.read()

    with open(os.path.join(output_dir, json_path), "r") as json_file:
        json_content = json_file.read()

    with open(os.path.join(output_dir, srt_path), "r") as srt_file:
        srt_content = srt_file.read()

    return {
        "vtt_content": vtt_content,
        "txt_content": txt_content,
        "json_content": json_content,
        "srt_content": srt_content,
        "vtt_path": vtt_path,
        "txt_path": txt_path,
        "json_path": json_path,
        "srt_path": srt_path,
    }


def zip_files(vtt_path, txt_path):
    memory_file = BytesIO()
    with ZipFile(memory_file, "w") as zf:
        zf.write(os.path.join(WHISPERX_API_DATA_PATH, vtt_path), vtt_path)
        zf.write(os.path.join(WHISPERX_API_DATA_PATH, txt_path), txt_path)
        memory_file.seek(0)
    return memory_file


def download_file_from_url(url):
    try:
        filename = f"{uuid.uuid4()}"
        temp_path = f"{WHISPERX_API_TEMP_PATH}/{filename}"

        logging.info(f"Downloading file from {url} to {temp_path}")
        chunk_size = 1024 * 1024

        with requests.get(url, stream=True) as response:
            response.raise_for_status()

            with open(temp_path, "wb") as f:
                for chunk in response.iter_content(chunk_size=chunk_size):
                    f.write(chunk)

        logging.info(f"Successfully downloaded file to {temp_path}")
        return temp_path
    except requests.RequestException as e:
        logging.error(f"Failed to download file from URL: {str(e)}")
        raise Exception(f"Failed to download file from URL: {str(e)}")
    except Exception as e:
        logging.error(f"Error processing file URL: {str(e)}")
        raise Exception(f"Error processing file URL: {str(e)}")
