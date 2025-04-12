import yt_dlp
import sys
import os
import re

# Create download directory
DOWNLOAD_DIR = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "downloaded_audio"
)
os.makedirs(DOWNLOAD_DIR, exist_ok=True)

def sanitize_filename(filename):
    """Sanitize filename to be compatible with various systems and tools"""
    # Remove or replace special characters
    filename = re.sub(r'[^\w\-_.]', '_', filename)
    # Replace spaces with underscores
    filename = filename.replace(' ', '_')
    # Replace multiple underscores with single underscore
    filename = re.sub(r'_+', '_', filename)
    # Remove leading/trailing underscores
    filename = filename.strip('_')
    return filename

def get_audio_settings():
    """Get audio settings from user input"""
    # Sample rate selection
    while True:
        try:
            print("\nSelect sample rate:")
            print("1) 24000 Hz (default)")
            print("2) 44100 Hz")
            print("3) 48000 Hz")
            choice = input("Enter choice (1-3): ")
            
            sample_rates = {"1": "24000", "2": "44100", "3": "48000"}
            if choice in sample_rates:
                sample_rate = sample_rates[choice]
                break
            print("Please enter a valid choice (1-3)")
        except ValueError:
            print("Please enter a valid choice (1-3)")

    # Channels selection
    while True:
        try:
            print("\nSelect audio channels:")
            print("1) Mono (default)")
            print("2) Stereo")
            choice = input("Enter choice (1-2): ")
            
            if choice in ["1", "2"]:
                channels = "1" if choice == "1" else "2"
                break
            print("Please enter a valid choice (1-2)")
        except ValueError:
            print("Please enter a valid choice (1-2)")

    return sample_rate, channels

def get_duration_in_seconds():
    while True:
        try:
            unit = input("Enter duration unit (h for hours, m for minutes): ").lower()
            if unit not in ["h", "m"]:
                print("Please enter 'h' for hours or 'm' for minutes")
                continue

            amount = float(input("Enter the amount: "))
            if amount <= 0:
                print("Please enter a positive number")
                continue

            # Convert to seconds
            if unit == "h":
                return amount * 3600
            else:
                return amount * 60

        except ValueError:
            print("Please enter a valid number")


def extract_channel_videos(url, target_duration):
    """Extract videos from channel until reaching target duration"""
    total_duration = 0
    videos_to_download = []

    ydl_opts = {
        "extract_flat": True,  # Don't download videos yet, just get metadata
        "quiet": True,
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            result = ydl.extract_info(url, download=False)
            if "entries" not in result:
                print("No videos found in the channel/playlist")
                return []

            for entry in result["entries"]:
                if entry is None:
                    continue

                # Get detailed info for each video
                video_info = ydl.extract_info(entry["url"], download=False)
                duration = video_info.get("duration", 0)

                if duration:
                    total_duration += duration
                    videos_to_download.append(entry["url"])
                    print(
                        f"Added video: {video_info['title']} (Duration: {duration / 60:.2f} minutes)"
                    )

                    if total_duration >= target_duration:
                        break

            print(
                f"\nTotal duration of selected videos: {total_duration / 60:.2f} minutes"
            )
            return videos_to_download

    except Exception as e:
        print(f"Error extracting videos: {str(e)}")
        return []


# Get user input
url = input(
    "Enter YouTube channel URL (e.g., https://www.youtube.com/@ChannelName/videos): "
)
target_duration = get_duration_in_seconds()
sample_rate, channels = get_audio_settings()

# Get list of videos to download
videos = extract_channel_videos(url, target_duration)

if not videos:
    print("No videos to download")
    sys.exit(1)

# Configure download options
ydl_opts = {
    "format": "bestaudio/best",
    "outtmpl": os.path.join(DOWNLOAD_DIR, "%(title)s.%(ext)s"),
    "postprocessors": [{
        "key": "FFmpegExtractAudio",
        "preferredcodec": "wav",
        "preferredquality": "192",
    }],
    "ffmpeg_args": [
        "-ar", sample_rate,
        "-ac", channels,
        "-acodec", "pcm_s16le"
    ],
    "quiet": False,
    # Add filename sanitization
    "restrictfilenames": True,
    "force_title": True,
}

class SanitizedLogger:
    def debug(self, msg):
        if msg.startswith('[download] Destination:'):
            # Sanitize the filename in the destination message
            path, filename = os.path.split(msg.split(': ')[1])
            sanitized_filename = sanitize_filename(filename)
            new_path = os.path.join(path, sanitized_filename)
            print(f'[download] Destination: {new_path}')
        else:
            print(msg)

    def warning(self, msg):
        print(f'[warning] {msg}')

    def error(self, msg):
        print(f'[error] {msg}')

# Download the audio from selected videos
print(f"\nStarting downloads to: {DOWNLOAD_DIR}")
try:
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        ydl.add_progress_hook(lambda d: None)  # Disable default progress
        ydl._progress_hooks = []  # Clear progress hooks
        ydl.logger = SanitizedLogger()
        ydl.download(videos)
    print("All downloads completed successfully!")
except Exception as e:
    print(f"An error occurred during download: {str(e)}")
    sys.exit(1)
