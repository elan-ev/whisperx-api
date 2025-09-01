import os
import tempfile
from unittest.mock import MagicMock, patch
from src.utils.file_utils import (
    create_directories,
    convert_to_mp3,
    read_output_files,
    zip_files,
)

from src.api.config import FFMPEG_BIN, WHISPERX_API_DATA_PATH, WHISPERX_API_TEMP_PATH

def test_create_directories():
    # Test that the directories are created if they don't exist
    with tempfile.TemporaryDirectory() as temp_dir:
        os.chdir(temp_dir)
        create_directories()
        assert os.path.exists(WHISPERX_API_TEMP_PATH)
        assert os.path.exists(WHISPERX_API_DATA_PATH)


def test_convert_to_mp3(mocker):
    # Test that the video file is converted to MP3 correctly
    with tempfile.TemporaryDirectory() as temp_dir:
        os.chdir(temp_dir)
        # Create a sample video file path
        video_file_path = "test.mp4"

        # Create a sample video file
        with open(video_file_path, "wb") as f:
            f.write(b"sample video content")

        # Mock the subprocess.run function
        mock_run = mocker.patch("subprocess.run")
        mock_run.return_value.returncode = 0

        temp_mp3_path = convert_to_mp3(video_file_path)

        assert temp_mp3_path.endswith(".mp3")

        # Check if ffmpeg command was called with the correct arguments
        mock_run.assert_called_once_with(
            [FFMPEG_BIN, "-y", "-i", video_file_path, temp_mp3_path], check=True
        )


def test_read_output_files():
    # Test that the output files are read correctly
    with tempfile.TemporaryDirectory() as temp_dir:
        os.chdir(temp_dir)
        os.makedirs(WHISPERX_API_DATA_PATH)
        # Create sample output files
        with open(f"{WHISPERX_API_DATA_PATH}/test.vtt", "w") as f:
            f.write("vtt content")
        with open(f"{WHISPERX_API_DATA_PATH}/test.txt", "w") as f:
            f.write("txt content")
        with open(f"{WHISPERX_API_DATA_PATH}/test.json", "w") as f:
            f.write("json content")
        with open(f"{WHISPERX_API_DATA_PATH}/test.srt", "w") as f:
            f.write("srt content")
        output_files = read_output_files("test")
        assert output_files["vtt_content"] == "vtt content"
        assert output_files["txt_content"] == "txt content"
        assert output_files["json_content"] == "json content"
        assert output_files["srt_content"] == "srt content"
        assert output_files["vtt_path"] == "test.vtt"
        assert output_files["txt_path"] == "test.txt"
        assert output_files["json_path"] == "test.json"
        assert output_files["srt_path"] == "test.srt"


def test_zip_files():
    # Test that the files are zipped correctly
    with tempfile.TemporaryDirectory() as temp_dir:
        os.chdir(temp_dir)
        os.makedirs(WHISPERX_API_DATA_PATH)
        # Create sample files
        with open(f"{WHISPERX_API_DATA_PATH}/test.vtt", "w") as f:
            f.write("vtt content")
        with open(f"{WHISPERX_API_DATA_PATH}/test.txt", "w") as f:
            f.write("txt content")
        memory_file = zip_files("test.vtt", "test.txt")
        assert memory_file.getvalue().startswith(
            b"PK"
        )  # Check if the file starts with a ZIP file signature
