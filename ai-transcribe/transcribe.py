import os
import datetime
import tempfile
import boto3
import subprocess
import srt
import time
import re
import tiktoken

from logger_config import logger
from config_loader import load_client_configs, get_client_config

import openai
from openai import OpenAI
from openai import OpenAI, AsyncOpenAI

from itsdangerous import URLSafeTimedSerializer, BadSignature



# === CONFIGURATION ===
client = OpenAI()

# storage
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
STORAGE_DIR = os.path.join(BASE_DIR, "storage")
os.makedirs(STORAGE_DIR, exist_ok=True)

# Load client configs
client_configs = load_client_configs()

# aws
def get_s3_client():
    return boto3.client("s3")

s3 = get_s3_client()

# -------------------------------------

CHUNK_DURATION = 300  # seconds
AUDIO_CODEC = "aac"
VIDEO_EXTENSIONS = [".mp4", ".mov", ".mkv", ".avi", ".qt"]
SUPPORTED_LANGUAGES = ["en", "de", "es", "hu", "cs", "sv", "ru", "zh", "ja", "he", "ro", "fr"]

logger.debug("Logger is active")

# === HELPERS ===
SECRET_KEY = "lets-change-the-world-for-the-better-2025#"
serializer = URLSafeTimedSerializer(SECRET_KEY)

def generate_signed_url(filename, client_id='default'):
    """Generate a signed URL for secure access to files"""
    config = get_client_config(client_configs, client_id)
    token = serializer.dumps(filename)
    return f"/api/storage-secure/{token}"


def list_video_files(bucket, prefix):
    logger.info(f"Listing video files in s3://{bucket}/{prefix}")
    paginator = s3.get_paginator("list_objects_v2")
    pages = paginator.paginate(Bucket=bucket, Prefix=prefix)

    video_files = []
    for page in pages:
        for obj in page.get("Contents", []):
            key = obj["Key"]
            if any(key.lower().endswith(ext) for ext in VIDEO_EXTENSIONS):
                video_files.append(key)

    logger.info(f"Found {len(video_files)} video files under {prefix}")
    return video_files


def download_file_from_s3(bucket, key):
    tmp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".mp4")
    logger.info(f"Downloading {key} from S3...")
    logger.debug(f"Temporary file path for download: {tmp_file.name}")
    s3.download_fileobj(bucket, key, tmp_file)
    tmp_file.close()
    return tmp_file.name


def extract_audio_chunks(video_path):
    logger.info("Extracting audio and splitting into chunks...")
    logger.debug(f"Input video path: {video_path}")
    audio_base = tempfile.mkdtemp()
    audio_template = os.path.join(audio_base, "chunk_%03d.m4a")
    logger.debug(f"Chunk output path template: {audio_template}")

    command = [
        "ffmpeg",
        "-i", video_path,
        "-f", "segment",
        "-segment_time", str(CHUNK_DURATION),
        "-c:a", AUDIO_CODEC,
        "-vn",
        audio_template
    ]
    logger.debug(f"Running ffmpeg command: {' '.join(command)}")
    subprocess.run(command, check=True)
    return sorted([os.path.join(audio_base, f) for f in os.listdir(audio_base)])


def transcribe_audio(file_path, prompt_lang="en", target_lang=None):
    logger.debug(f"Transcribing file: {file_path}, source: {prompt_lang}, target: {target_lang}")
    with open(file_path, "rb") as audio_file:
        if target_lang and target_lang != prompt_lang:
            logger.info(f"Using Whisper translation: {prompt_lang} → {target_lang}")
            response = client.audio.translations.create(
                model="whisper-1",
                file=audio_file,
                response_format="verbose_json"
            )
        else:
            logger.info(f"Using Whisper transcription in {prompt_lang}")
            response = client.audio.transcriptions.create(
                model="whisper-1",
                file=audio_file,
                language=prompt_lang,
                response_format="verbose_json"
            )

    text = response.text
    segments = response.segments if hasattr(response, "segments") else []
    logger.debug(f"Transcription result length: {len(text)}, segments: {len(segments)}")
    return text, segments



def build_srt(segments_all):
    subtitles = []
    count = 1
    time_offset = datetime.timedelta()
    logger.debug(f"Building SRT with chunk duration offset: {CHUNK_DURATION}s")

    for segment_group in segments_all:
        for segment in segment_group:
            start = time_offset + datetime.timedelta(seconds=segment.start)
            end = time_offset + datetime.timedelta(seconds=segment.end)
            subtitle = srt.Subtitle(index=count, start=start, end=end, content=segment.text.strip())
            subtitles.append(subtitle)
            count += 1
        time_offset += datetime.timedelta(seconds=CHUNK_DURATION)

    # Sort subtitles by start time to avoid TypeError in srt.compose
    subtitles.sort(key=lambda s: s.start)

    logger.debug(f"Generated {len(subtitles)} subtitles in total")
    return srt.compose(subtitles)



def translate_with_gpt4(text, lang, max_retries=5):
    delay = 60  # Start with 60 seconds for rate limit issues

    for attempt in range(max_retries):
        try:
            response = client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {
                        "role": "system",
                        "content": f"Translate the following subtitles to {lang}. Preserve timestamps and subtitle formatting exactly."
                    },
                    {
                        "role": "user",
                        "content": text
                    }
                ],
                temperature=0.3
            )

            if response.choices and response.choices[0].message and response.choices[0].message.content:
                return response.choices[0].message.content.strip()
            else:
                raise Exception("Empty response from GPT-4")

        except openai.RateLimitError:
            print(f"Rate limit hit. Waiting {delay}s before retrying... (Attempt {attempt + 1}/{max_retries})")
            time.sleep(delay)
            delay *= 2  # Exponential backoff

        except openai.Timeout:
            print(f"Timeout. Waiting {delay}s before retrying... (Attempt {attempt + 1}/{max_retries})")
            time.sleep(delay)
            delay *= 2

        except Exception as e:
            print(f"Unexpected error during GPT-4 translation: {e}")
            break

    print(f"Translation to {lang} failed after {max_retries} attempts.")
    return None




def process_s3_target(bucket, key_or_prefix, prompt_lang="en", enable_translation=False,
                      upload=False, upload_bucket=None, upload_prefix=None,
                      cloudfront_base_url=None, advanced_encoding=False,
                      translate_languages=None, override=False, client_id='default'):
    logger.info(f"Processing S3 target: {key_or_prefix}")
    if any(key_or_prefix.lower().endswith(ext) for ext in VIDEO_EXTENSIONS):
        logger.info("Detected single MP4 file input.")
        return [process_single_video(
            bucket, key_or_prefix, prompt_lang, enable_translation,
            upload=upload, upload_bucket=upload_bucket, upload_prefix=upload_prefix,
            cloudfront_base_url=cloudfront_base_url, advanced_encoding=advanced_encoding,
            translate_languages=translate_languages,
            override=override,
            client_id=client_id
        )]
    else:
        logger.info("Detected directory input.")
        video_keys = list_video_files(bucket, key_or_prefix)
        return [process_single_video(
            bucket, key, prompt_lang, enable_translation,
            upload=upload, upload_bucket=upload_bucket, upload_prefix=upload_prefix,
            cloudfront_base_url=cloudfront_base_url, advanced_encoding=advanced_encoding,
            translate_languages=translate_languages,
            override=override,
            client_id=client_id
        ) for key in video_keys]


def upload_to_s3(bucket, key, content, suffix):
    output_key = key.rsplit(".", 1)[0] + suffix
    logger.debug(f"Uploading to S3: bucket={bucket}, key={output_key}, size={len(content)}")
    s3.put_object(Bucket=bucket, Key=output_key, Body=content)
    logger.info(f"Uploaded {output_key} to bucket {bucket}")
    return output_key


def write_to_local(dir_path, base_filename, content, suffix):
    out_path = os.path.join(STORAGE_DIR, dir_path, base_filename + suffix)
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    logger.debug(f"Writing file to: {out_path}, length: {len(content)} chars")
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(content)
    logger.info(f"Stored file locally at {out_path}")
    return out_path


def check_existing_files(bucket, key, translate_languages=None):
    base_key = key.rsplit(".", 1)[0]
    filename_base = os.path.basename(base_key)
    dir_path = base_key  # Use the full key as directory path
    existing_files = {
        "transcription": False,
        "translations": {}
    }

    vtt_path = os.path.join(STORAGE_DIR, base_key, f"{filename_base}.vtt")
    if os.path.exists(vtt_path):
        existing_files["transcription"] = True

    if translate_languages:
        for lang in translate_languages:
            lang_vtt_path = os.path.join(STORAGE_DIR, base_key, f"{filename_base}_{lang}.vtt")
            existing_files["translations"][lang] = os.path.exists(lang_vtt_path)

    return existing_files


def get_source_language_from_filename(base_key):
    """Try to determine source language from filename or return default"""
    # This could be enhanced by storing metadata or analyzing content
    # For now, we'll use a simple approach
    filename = os.path.basename(base_key)
    
    # Check if filename contains language indicators
    for lang in SUPPORTED_LANGUAGES:
        if f"_{lang}." in filename or f"_{lang}_" in filename:
            return lang
    
    # Default to English if no language indicator found
    return "en"

def get_available_languages(base_key):
    filename_base = os.path.basename(base_key)
    dir_path = base_key
    available_languages = []

    # Check for source language file (no language suffix)
    source_vtt_path = os.path.join(STORAGE_DIR, dir_path, f"{filename_base}.vtt")
    if os.path.exists(source_vtt_path):
        # Determine source language
        source_lang = get_source_language_from_filename(base_key)
        available_languages.append(source_lang)

    # Check for translated language files
    for lang in SUPPORTED_LANGUAGES:
        lang_file = os.path.join(STORAGE_DIR, dir_path, f"{filename_base}_{lang}.vtt")
        if os.path.exists(lang_file):
            if lang not in available_languages:  # Avoid duplicates
                available_languages.append(lang)

    return available_languages



def fix_timestamp_format(vtt_text):
    # Replace timestamps like 00:01:02,123 --> 00:01:04,567 with dots instead of commas
    return re.sub(r'(\d{2}:\d{2}:\d{2}),(\d{3})', r'\1.\2', vtt_text)


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


def chunk_subtitles(subtitles, max_per_chunk=30):
    for i in range(0, len(subtitles), max_per_chunk):
        yield subtitles[i:i + max_per_chunk]




def process_single_video(bucket, key, prompt_lang="en", enable_translation=False,
                         upload=False, upload_bucket=None, upload_prefix=None,
                         cloudfront_base_url=None, advanced_encoding=False,
                         translate_languages=None, override=False, client_id='default'):
    logger.info(f"Processing single video: {key}")
    logger.debug(f"Prompt lang: {prompt_lang}, Translate: {enable_translation}, Upload: {upload}")
    logger.debug(f"Upload bucket: {upload_bucket}, Upload prefix: {upload_prefix}")
    logger.debug(f"CloudFront base URL: {cloudfront_base_url}")
    logger.debug(f"Translation languages requested: {translate_languages}")
    logger.debug(f"Override existing files: {override}")
    logger.debug(f"Client ID: {client_id}")

    # Get client config
    config = get_client_config(client_configs, client_id)
    if not cloudfront_base_url:
        cloudfront_base_url = config['CLOUDFRONT_BASE_URL']

    # Check for existing files
    existing_files = check_existing_files(bucket, key, translate_languages)
    base_key = key.rsplit(".", 1)[0]
    filename_base = clean_filename(base_key.split("/")[-1])

    # If transcription exists and override is False, skip the transcription process
    if existing_files["transcription"] and not override:
        logger.info(f"Found existing transcription for {key}, skipping transcription")
        # Use existing VTT file
        vtt_path = os.path.join(STORAGE_DIR, base_key, f"{filename_base}.vtt")
        with open(vtt_path, "r", encoding="utf-8") as f:
            full_transcript = f.read()
            srt_data = full_transcript.replace("WEBVTT\n\n", "")  # Remove WEBVTT header if present
    else:
        # Process video as before
        local_path = download_file_from_s3(bucket, key)
        chunks = extract_audio_chunks(local_path)

        full_transcript = ""
        all_segments = []

        for chunk_path in chunks:
            logger.info(f"Transcribing chunk: {chunk_path}")
            
            # Determine if we should use Whisper translation or transcription
            # Only use translation if we specifically want to translate to a different language
            use_whisper_translation = False
            target_lang_for_whisper = None
            
            if enable_translation and prompt_lang != "en":
                # If source is not English and translation is enabled, translate to English
                use_whisper_translation = True
                target_lang_for_whisper = "en"
                logger.info(f"Using Whisper translation: {prompt_lang} → English")
            elif enable_translation and prompt_lang == "en":
                # If source is English and translation is enabled, keep it in English
                use_whisper_translation = False
                target_lang_for_whisper = None
                logger.info("Source is English, using transcription (no translation needed)")
            else:
                # No translation requested, transcribe in original language
                use_whisper_translation = False
                target_lang_for_whisper = None
                logger.info(f"Transcribing in original language: {prompt_lang}")
            
            text, segments = transcribe_audio(
                chunk_path,
                prompt_lang=prompt_lang,
                target_lang=target_lang_for_whisper
            )
            full_transcript += text.strip() + "\n"
            if segments:
                all_segments.append(segments)
            os.remove(chunk_path)

        srt_data = build_srt(all_segments)
        fixed_srt_data = fix_timestamp_format(srt_data)
        
        # Save the transcription
        if upload:
            upload_to_s3(upload_bucket or bucket, key, full_transcript, ".txt")
            upload_to_s3(upload_bucket or bucket, key, fixed_srt_data, ".vtt")
        else:
            write_to_local(base_key, filename_base, full_transcript, ".txt")
            write_to_local(base_key, filename_base, "WEBVTT\n\n" + fixed_srt_data, ".vtt")

    # --- TRANSLATION WITH GPT-4 ---
    if translate_languages:
        logger.info(f"Starting GPT-4 translation for languages: {translate_languages}")
        
        # If we have existing transcription, we need to parse the SRT data
        if existing_files["transcription"] and not override:
            subtitles = list(srt.parse(srt_data))
            flat_segments = [
                s for s in subtitles
                if hasattr(s, "start") and hasattr(s, "end") and hasattr(s, "content")
            ]
        else:
            # Flatten and sort all subtitle segments from transcription
            flat_segments = [
                s for group in all_segments for s in group
                if hasattr(s, "start") and hasattr(s, "end") and hasattr(s, "text")
                and isinstance(s.start, (int, float)) and isinstance(s.end, (int, float)) and s.end > s.start
            ]

        flat_segments.sort(key=lambda s: s.start if hasattr(s, "start") else s.start.total_seconds())

        original_srt_text = srt.compose([
            srt.Subtitle(
                index=i + 1,
                start=s.start if isinstance(s.start, datetime.timedelta) else datetime.timedelta(seconds=s.start),
                end=s.end if isinstance(s.end, datetime.timedelta) else datetime.timedelta(seconds=s.end),
                content=s.text.strip() if hasattr(s, "text") else s.content.strip() if hasattr(s, "content") else str(s).strip()
            )
            for i, s in enumerate(flat_segments)
        ])

        encoding = tiktoken.encoding_for_model("gpt-4")

        for lang in translate_languages:
            # Skip translation if it's the same as the source language
            if lang == prompt_lang:
                logger.info(f"Skipping GPT-4 translation to {lang} — same as source language.")
                continue
            
            # Skip English translation if source is already English
            if lang == "en" and prompt_lang == "en":
                logger.info("Skipping GPT-4 translation to English — already source language.")
                continue
            
            if existing_files["translations"].get(lang, False) and not override:
                logger.info(f"Found existing translation for {lang}, skipping")
                continue
                
            logger.info(f"Translating to {lang}")
            translated_text = translate_with_gpt4(original_srt_text, lang)
            if not translated_text:
                logger.warning(f"No translated text returned for {lang}. Skipping.")
                continue
                
            fixed_translated_text = "WEBVTT\n\n" + fix_timestamp_format(translated_text)

            if upload:
                s3_path = f"{upload_prefix or 'vtt'}/{filename_base}_{lang}.vtt"
                upload_to_s3(upload_bucket or bucket, s3_path, fixed_translated_text, "")
            else:
                write_to_local(base_key, filename_base, fixed_translated_text, f"_{lang}.vtt")

    # Generate streaming URLs based on encoding type with sanitization
    file_name = os.path.basename(key)
    file_base = sanitize_filename(os.path.splitext(file_name)[0])
    encoded_path = key

    if advanced_encoding:
        cleaned_encoded_path = sanitize_path(encoded_path)
        dash_url = f"https://{cloudfront_base_url}/{cleaned_encoded_path}/dash/{file_base}.mpd"
        hls_url = f"https://{cloudfront_base_url}/{cleaned_encoded_path}/hls/{file_base}.m3u8"
        preview_url = f"https://{cloudfront_base_url}/{cleaned_encoded_path}/img/{file_base}_01.png"
        logger.debug(f"Advanced encoding URLs: DASH={dash_url}, HLS={hls_url}")
    else:
        media_path = os.path.splitext(key)[0]  # full path without extension
        cleaned_media_path = sanitize_path(media_path)
        dash_url = f"https://{cloudfront_base_url}/{cleaned_media_path}/dash/stream.mpd"
        hls_url = f"https://{cloudfront_base_url}/{cleaned_media_path}/hls/master.m3u8"
        preview_url = f"https://{cloudfront_base_url}/{cleaned_media_path}/img/{file_base}_01.png"
        logger.debug(f"Default encoding URLs: DASH={dash_url}, HLS={hls_url}")

    # Clean up
    if not existing_files["transcription"]:  # Only remove if we downloaded it
        os.remove(local_path)

    # Return the result structure with all available languages
    base_url = f"/api/storage/{base_key}"

    # MUST COME BEFORE using in result
    available_languages = get_available_languages(base_key)
    logger.info(f"Found available languages: {available_languages}")

    subtitle_path = f"{base_key}/{filename_base}.vtt"
    signed_url = generate_signed_url(subtitle_path, client_id)

    result = {
        "transcript": f"{base_url}/{filename_base}.txt",
        "subtitle": f"{base_url}/{filename_base}.vtt",
        "transcript_url": f"{base_url}/{filename_base}.txt",
        "subtitle_url": signed_url,
        "source_video": key,
        "dash_url": dash_url,
        "hls_url": hls_url,
        "preview_url": preview_url,
        "available_languages": available_languages
    }

    # Add signed URLs for all available languages (including translated subtitles)
    for lang in available_languages:
        if lang == "en":
            continue  # Already handled above

        translated_path = f"{base_key}/{filename_base}_{lang}.vtt"
        signed_translated_url = generate_signed_url(translated_path, client_id)
        result[f"subtitle_url_{lang}"] = signed_translated_url

    return result

