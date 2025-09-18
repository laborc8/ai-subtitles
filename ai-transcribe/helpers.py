import os
import tempfile
import traceback
import re
from datetime import datetime, timedelta
import rsa
from botocore.signers import CloudFrontSigner
from itsdangerous import URLSafeTimedSerializer, BadSignature
from dotenv import load_dotenv
import boto3
from logger_config import logger
from config_loader import load_client_configs, get_client_config

# Load environment variables
dotenv_path = os.environ.get("DOTENV_PATH") or os.path.join(os.path.dirname(__file__), '..', '.env')
load_dotenv(dotenv_path)

# Load client configs
client_configs = load_client_configs()

# Storage configuration
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
STORAGE_DIR = os.path.join(BASE_DIR, "storage")
os.makedirs(STORAGE_DIR, exist_ok=True)

# Security configuration
SECRET_KEY = "lets-change-the-world-for-the-better-2025#"
serializer = URLSafeTimedSerializer(SECRET_KEY)

# Environment variables
VALID_USERNAME = os.getenv("LOGIN_USERNAME")
VALID_PASSWORD = os.getenv("LOGIN_PASSWORD")
STORAGE_API_KEY = os.getenv("STORAGE_API_KEY")

# AWS configuration
def setup_aws_credentials():
    """Setup AWS credentials from environment variables"""
    os.environ["AWS_ACCESS_KEY_ID"] = os.getenv("AWS_ACCESS_KEY_ID", "")
    os.environ["AWS_SECRET_ACCESS_KEY"] = os.getenv("AWS_SECRET_ACCESS_KEY", "")

    boto3.setup_default_session(
        aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
        aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
    )

# OpenAI configuration
def validate_openai_key():
    """Validate OpenAI API key is set"""
    openai_api_key = os.getenv("OPENAI_API_KEY")
    if not openai_api_key:
        logger.error("OPENAI_API_KEY is not set.")
        raise EnvironmentError("Missing OPENAI_API_KEY")
    return openai_api_key

# URL helpers
def ensure_https(url):
    """Ensure URL starts with https://"""
    return url if url.startswith('http') else f"https://{url}"

# Filename and path sanitization functions
def clean_filename(filename: str) -> str:
    """Remove parentheses from filename"""
    return filename.replace('(', '').replace(')', '')

def clean_path(path: str) -> str:
    """Remove parentheses from every segment in a path string"""
    return path.replace('(', '').replace(')', '')

def sanitize_filename(name: str) -> str:
    """Remove parentheses and replace any whitespace with underscores in a filename base."""
    without_parens = name.replace('(', '').replace(')', '')
    return re.sub(r"\s", "_", without_parens)

def sanitize_path(path: str) -> str:
    """Remove parentheses and replace any whitespace with underscores across the entire path."""
    without_parens = path.replace('(', '').replace(')', '')
    return re.sub(r"\s", "_", without_parens)

def generate_signed_cloudfront_url(video_key, client_id='default'):
    """Generate a signed CloudFront URL for a video"""
    config = get_client_config(client_configs, client_id)
    
    logger.debug(f"Client config used for signing: {config}")
    logger.debug(f"Key Pair ID: {config['CLOUDFRONT_KEY_PAIR_ID']}")
    logger.debug(f"Private key file: {config['CLOUDFRONT_PRIVATE_KEY_PATH']}")

    # Load the private key
    try:
        with open(config['CLOUDFRONT_PRIVATE_KEY_PATH'], 'rb') as key_file:
            private_key = rsa.PrivateKey.load_pkcs1(key_file.read())
    except Exception as e:
        logger.error(f"Failed to load private key: {e}")
        raise

    # Create a signer
    def rsa_signer(message):
        return rsa.sign(message, private_key, 'SHA-1')

    cloudfront_signer = CloudFrontSigner(config['CLOUDFRONT_KEY_PAIR_ID'], rsa_signer)

    # Generate the signed URL
    url = f"{config['CLOUDFRONT_BASE_URL']}/{video_key}"
    signed_url = cloudfront_signer.generate_presigned_url(url, date_less_than=datetime.utcnow() + timedelta(hours=1))

    logger.debug(f"Signed URL generated: {signed_url}")
    return signed_url

def generate_signed_url(filename, client_id='default'):
    """Generate a signed URL for secure access to files"""
    config = get_client_config(client_configs, client_id)
    token = serializer.dumps(filename)
    return f"/api/storage-secure/{token}"

# File helpers
def create_temp_file(content, suffix=".wav"):
    """Create a temporary file with given content"""
    tmp_file = tempfile.NamedTemporaryFile(delete=False, suffix=suffix)
    tmp_file.write(content)
    tmp_file.close()
    return tmp_file.name

def cleanup_temp_file(file_path):
    """Remove a temporary file"""
    try:
        if os.path.exists(file_path):
            os.remove(file_path)
    except Exception as e:
        logger.warning(f"Failed to cleanup temp file {file_path}: {e}")

# Authentication helpers
def validate_credentials(username, password):
    """Validate user credentials"""
    if username == VALID_USERNAME and password == VALID_PASSWORD:
        logger.info(f"Successful login for user: {username}")
        return True
    else:
        logger.warning(f"Failed login attempt for user: {username}")
        return False

# Error handling helpers
def handle_exception(e, context=""):
    """Standardized exception handling"""
    logger.error(f"Exception in {context}: {str(e)}")
    logger.error(traceback.format_exc())
    return {"error": str(e)}

# Configuration helpers
def get_client_config_safe(client_id='default'):
    """Safely get client configuration with error handling"""
    try:
        return get_client_config(client_configs, client_id)
    except Exception as e:
        logger.error(f"Failed to get client config for {client_id}: {e}")
        return get_client_config(client_configs, 'default')

# Language helpers
def get_supported_languages():
    """Get list of supported languages"""
    return {
        'en': 'English',
        'de': 'German',
        'es': 'Spanish',
        'hu': 'Hungarian',
        'cs': 'Czech',
        'sv': 'Swedish',
        'ru': 'Russian',
        'zh': 'Chinese',
        'ja': 'Japanese',
        'he': 'Hebrew',
        'ro': 'Romanian',
        'fr': 'French'
    }

# Video URL helpers
def build_video_urls(video_key, config, advanced=False, client_id='default'):
    """Build video streaming URLs with proper sanitization and CloudFront signing"""
    media_path = os.path.splitext(video_key)[0]
    extension = os.path.splitext(video_key)[1]
    filename_base = sanitize_filename(os.path.basename(media_path))
    base_key = sanitize_path(media_path)

    if advanced:
        dash_key = f"{base_key}{extension}/dash/{filename_base}.mpd"
        hls_key = f"{base_key}{extension}/hls/{filename_base}.m3u8"
    else:
        base_key = sanitize_path(media_path)
        dash_key = f"{base_key}/dash/stream.mpd"
        hls_key = f"{base_key}/hls/master.m3u8"

    preview_key = f"{base_key}/img/{filename_base}_01.png"

    # Apply CloudFront signing with sanitization
    return {
        "dash_url": generate_signed_cloudfront_url(clean_path(dash_key), client_id),
        "hls_url": generate_signed_cloudfront_url(clean_path(hls_key), client_id),
        "preview_url": generate_signed_cloudfront_url(clean_path(preview_key), client_id)
    }

# Initialize AWS credentials on module load
setup_aws_credentials() 