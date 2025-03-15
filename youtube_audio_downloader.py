import yt_dlp
import sys
import re
import os

# Create download directory
DOWNLOAD_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "downloaded_audio")
os.makedirs(DOWNLOAD_DIR, exist_ok=True)

def get_duration_in_seconds():
    while True:
        try:
            unit = input("Enter duration unit (h for hours, m for minutes): ").lower()
            if unit not in ['h', 'm']:
                print("Please enter 'h' for hours or 'm' for minutes")
                continue
            
            amount = float(input("Enter the amount: "))
            if amount <= 0:
                print("Please enter a positive number")
                continue
            
            # Convert to seconds
            if unit == 'h':
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
        'extract_flat': True,  # Don't download videos yet, just get metadata
        'quiet': True
    }
    
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            result = ydl.extract_info(url, download=False)
            if 'entries' not in result:
                print("No videos found in the channel/playlist")
                return []

            for entry in result['entries']:
                if entry is None:
                    continue
                    
                # Get detailed info for each video
                video_info = ydl.extract_info(entry['url'], download=False)
                duration = video_info.get('duration', 0)
                
                if duration:
                    total_duration += duration
                    videos_to_download.append(entry['url'])
                    print(f"Added video: {video_info['title']} (Duration: {duration/60:.2f} minutes)")
                    
                    if total_duration >= target_duration:
                        break
                        
            print(f"\nTotal duration of selected videos: {total_duration/60:.2f} minutes")
            return videos_to_download
            
    except Exception as e:
        print(f"Error extracting videos: {str(e)}")
        return []

# Get user input
url = input("Enter YouTube channel URL (e.g., https://www.youtube.com/@ChannelName/videos): ")
target_duration = get_duration_in_seconds()

# Get list of videos to download
videos = extract_channel_videos(url, target_duration)

if not videos:
    print("No videos to download")
    sys.exit(1)

# Configure download options
ydl_opts = {
    'format': 'm4a/bestaudio/best',
    'postprocessors': [{
        'key': 'FFmpegExtractAudio',
        'preferredcodec': 'mp3',
        'preferredquality': '192',
    }],
    'outtmpl': os.path.join(DOWNLOAD_DIR, '%(title)s.%(ext)s'),  # Save in download directory
    'quiet': False,
}

# Download the audio from selected videos
print(f"\nStarting downloads to: {DOWNLOAD_DIR}")
try:
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        ydl.download(videos)
    print("All downloads completed successfully!")
except Exception as e:
    print(f"An error occurred during download: {str(e)}")
    sys.exit(1)