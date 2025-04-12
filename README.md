# Download Youtube or Twitch videos as audio only. 
- Choose sample rate
- Choose channels
- Chosose how many minutes or hours to download.

## Requirements
- Python 3.8 or higher
- FFMPEG installed and available in system PATH

## Installation
1. Create and activate a virtual environment:
   ```bash
   # Windows
   python -m venv venv 
   .\venv\Scripts\activate

   # Linux/macOS
   python3 -m venv venv 
   source venv/bin/activate
   ```

2. Install dependencies:
   ```bash
   pip install yt-dlp
   ```

3. Run the script:
   - Just run the script and follow instructions in the terminal.
   ```bash
   python youtube_audio_downloader.py
   ```

4. Example URLS
      - https://www.youtube.com/@AYoutubeUsername/videos
      - https://www.twitch.tv/aTwitchUsername/videos?filter=archives&sort=time

## Features
- Allows user to specify how many minutes or hours to download.
- Automatic conversion to only audio