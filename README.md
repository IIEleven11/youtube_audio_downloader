# Download youtube content by using youtube-dl.

## Requirements
- Python 3.8 or higher
- FFMPEG installed and available in system PATH

## Installation
1. Create and activate a virtual environment:
   ```bash
   # Windows
   python -m venv venv --system-site-packages
   .\venv\Scripts\activate

   # Linux/macOS
   python3 -m venv venv --system-site-packages
   source venv/bin/activate
   ```

2. Install dependencies:
   ```bash
   pip install yt-dlp
   ```

3. Run the script:
   ```bash
   python youtube_audio_downloader.py
   ```

4. Follow the instructions in the prompt

## Features
- Allows user to specify how many minutes or hours to download.
- Automatic conversion to only audio