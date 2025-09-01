# Environment Variables
import os
import dotenv

# Load environment variables
dotenv.load_dotenv()


API_PORT = os.getenv("API_PORT", 11300)
API_HOST = os.getenv("API_HOST", "0.0.0.0")

BROKER_URL = os.getenv("RABBIT_MQ_URI", "amqp://guest:guest@localhost:5672//")

HF_TOKEN = os.getenv("HUGGING_FACE_TOKEN", "")

FFMPEG_BIN = os.getenv("FFMPEG_BIN", "ffmpeg")
FFPROBE_BIN = os.getenv("FFPROBE_BIN", "ffprobe")
WHISPERX_API_DATA_PATH = os.getenv("WHISPERX_API_DATA_PATH", "./data")
WHISPERX_API_TEMP_PATH = os.getenv("WHISPERX_API_TEMP_PATH", "./temp")

WHISPERX_CPU_ONLY = os.getenv("WHISPERX_CPU_ONLY", False)
