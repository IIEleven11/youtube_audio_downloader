#!/usr/bin/env python3

import os
import subprocess
import json
import re
from urllib.parse import urlparse

# Ensure the downloaded_audio directory exists
if not os.path.exists('downloaded_audio'):
    os.makedirs('downloaded_audio')

def sanitize_filename(filename):
    """Sanitize filename to be compatible with ffmpeg and file systems.

    Removes special characters, replaces spaces with underscores,
    and ensures the filename is not too long.
    """
    # Remove any non-alphanumeric characters except for periods, underscores, and hyphens
    # Also replace spaces with underscores
    sanitized = re.sub(r'[^\w\-\.]', '_', filename.replace(' ', '_'))

    # Remove consecutive underscores
    sanitized = re.sub(r'_+', '_', sanitized)

    # Remove leading/trailing underscores
    sanitized = sanitized.strip('_')

    # Limit filename length (some filesystems have limits)
    max_length = 200  # Safe length for most filesystems
    if len(sanitized) > max_length:
        # Keep the extension if present
        name, ext = os.path.splitext(sanitized)
        sanitized = name[:max_length - len(ext)] + ext

    # Ensure we have a valid filename
    if not sanitized or sanitized == '.':
        sanitized = 'unnamed_audio'

    return sanitized

def validate_url(url):
    """Validate if the URL is from YouTube or Twitch."""
    parsed_url = urlparse(url)
    domain = parsed_url.netloc.lower()

    if 'youtube.com' in domain or 'youtu.be' in domain or 'twitch.tv' in domain:
        return True
    return False

def get_video_duration(video_info):
    """Extract video duration in seconds from video info."""
    try:
        duration = float(video_info.get('duration', 0))
        return duration
    except (ValueError, TypeError):
        return 0

def get_total_duration(url):
    """Get the total duration of all videos in the playlist or channel."""
    cmd = [
        'yt-dlp',
        '--dump-json',
        '--flat-playlist',
        url
    ]

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        lines = result.stdout.strip().split('\n')

        total_seconds = 0
        video_count = 0

        for line in lines:
            if line.strip():
                try:
                    video_info = json.loads(line)
                    duration = get_video_duration(video_info)
                    if duration > 0:
                        total_seconds += duration
                        video_count += 1
                except json.JSONDecodeError:
                    continue

        return total_seconds, video_count
    except subprocess.CalledProcessError:
        print("Error: Could not retrieve video information.")
        return 0, 0

def download_audio(url, max_hours, sample_rate, channels):
    """Download videos and convert to audio with specified parameters."""
    # Calculate max duration in seconds
    max_seconds = max_hours * 3600

    # Get total duration of all videos
    total_seconds, video_count = get_total_duration(url)

    if total_seconds == 0 or video_count == 0:
        print("Could not determine video durations or no videos found.")
        return False

    print(f"Found {video_count} videos with total duration of {total_seconds/3600:.2f} hours.")

    # Determine how many videos to download
    if total_seconds <= max_seconds:
        # Download all videos
        playlist_end = None
        print(f"Will download all {video_count} videos (total duration: {total_seconds/3600:.2f} hours).")
    else:
        # Estimate how many videos to download based on average duration
        avg_duration = total_seconds / video_count
        videos_to_download = max(1, int(max_seconds / avg_duration))
        playlist_end = videos_to_download
        print(f"Will download approximately {videos_to_download} videos to match requested {max_hours} hours.")

    # Set audio format parameters
    audio_format = 'wav'
    audio_quality = 0  # Best quality

    # Set channel parameter
    audio_channels = '1' if channels.lower() == 'mono' else '2'

    # Create a temporary output template file that uses our sanitize_filename function
    output_template = '%(title)s.%(ext)s'

    # Build the yt-dlp command
    cmd = [
        'yt-dlp',
        '-x',  # Extract audio
        '--audio-format', audio_format,
        '--audio-quality', str(audio_quality),
        '--paths', 'downloaded_audio',
        '--output', output_template,
        '--postprocessor-args', f'ffmpeg:-ar {sample_rate} -ac {audio_channels}',
        '--max-filesize', '1000M',  # Limit file size to 100MB for testing
        '--socket-timeout', '30',  # 30 seconds timeout
    ]

    # Add playlist end if needed
    if playlist_end:
        cmd.extend(['--playlist-end', str(playlist_end)])

    # Add the URL
    cmd.append(url)

    print("\nStarting download and conversion...")
    print(f"Command: {' '.join(cmd)}")

    try:
        # Run the download command
        subprocess.run(cmd, check=True)

        # After download, sanitize all filenames in the downloaded_audio directory
        print("\nSanitizing filenames...")
        sanitized_count = 0
        for filename in os.listdir('downloaded_audio'):
            if filename.endswith('.wav'):  # Only process WAV files
                old_path = os.path.join('downloaded_audio', filename)
                sanitized_name = sanitize_filename(os.path.splitext(filename)[0]) + '.wav'
                new_path = os.path.join('downloaded_audio', sanitized_name)

                if old_path != new_path:
                    try:
                        os.rename(old_path, new_path)
                        sanitized_count += 1
                        print(f"Renamed: {filename} -> {sanitized_name}")
                    except Exception as rename_error:
                        print(f"Error renaming {filename}: {rename_error}")

        if sanitized_count > 0:
            print(f"Sanitized {sanitized_count} filenames.")
        else:
            print("No filenames needed sanitizing.")

        print("\nDownload and conversion completed successfully!")
        return True
    except subprocess.CalledProcessError as e:
        print(f"\nError during download: {e}")
        return False

def get_clean_input(prompt):
    """Get user input and clean it by removing any trailing newlines."""
    user_input = input(prompt)
    # Remove any trailing newlines that might be included
    return user_input.rstrip('\n')

def main():
    print("YouTube/Twitch Audio Downloader")
    print("================================\n")

    # Check if yt-dlp is installed
    try:
        subprocess.run(['yt-dlp', '--version'], capture_output=True, check=True)
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("Error: yt-dlp is not installed or not in PATH.")
        print("Please install it with: pip install yt-dlp")
        return

    # Get URL
    url = get_clean_input("Enter YouTube or Twitch URL (or 'test' for a short test video): ").strip()

    # Use a short test video if requested
    if url.lower() == 'test':
        url = 'https://youtube.com/shorts/Zxe4n0QEj_s'  # Short YouTube video for testing
        print(f"Using test video: {url}")
    elif not validate_url(url):
        print("Error: Invalid URL. Please enter a YouTube or Twitch URL.")
        return

    # Get hours to download
    while True:
        try:
            hours_input = get_clean_input("How many hours of video do you want to download? ").strip()
            max_hours = float(hours_input)
            if max_hours <= 0:
                print("Please enter a positive number.")
                continue
            break
        except ValueError:
            print(f"Please enter a valid number. You entered: '{hours_input}'")

    # Get sample rate
    valid_sample_rates = [8000, 11025, 16000, 22050, 24000, 32000, 44100, 48000, 88200, 96000, 192000]
    while True:
        try:
            rate_input = get_clean_input(f"Enter desired sample rate {valid_sample_rates}: ").strip()
            sample_rate = int(rate_input)
            if sample_rate not in valid_sample_rates:
                print(f"Please enter one of the valid sample rates: {valid_sample_rates}")
                continue
            break
        except ValueError:
            print(f"Please enter a valid number. You entered: '{rate_input}'")

    # Get channels
    while True:
        channels = get_clean_input("Enter audio channels (mono/stereo): ").strip().lower()
        if channels not in ['mono', 'stereo']:
            print(f"Please enter either 'mono' or 'stereo'. You entered: '{channels}'")
            continue
        break

    # Download and convert
    success = download_audio(url, max_hours, sample_rate, channels)

    if success:
        print("\nAudio files have been saved to the 'downloaded_audio' directory.")
        print(f"Sample rate: {sample_rate} Hz, Channels: {channels}")
    else:
        print("\nDownload failed. Please check your inputs and try again.")

if __name__ == "__main__":
    main()
