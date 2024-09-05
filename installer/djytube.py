import yt_dlp
import argparse
import sys
import re
import os
import subprocess
import platform
import shutil

VERSION = "0.1.7"

# Regular expression pattern to check if the input URL is a valid YouTube URL
YOUTUBE_URL_PATTERN = re.compile(r'(https?://)?(www\.)?(youtube|youtu|youtube-nocookie)\.(com|be)/.+')

def is_valid_youtube_url(url):
    """Check if the provided URL is a valid YouTube URL."""
    return re.match(YOUTUBE_URL_PATTERN, url) is not None

def check_ffmpeg():
    """Check if ffmpeg is installed and available."""
    if shutil.which("ffmpeg") is not None:
        return True
    return False

def install_ffmpeg():
    """Provide platform-specific instructions for installing ffmpeg."""
    current_platform = platform.system()

    if current_platform == "Windows":
        print("Please install ffmpeg manually on Windows from: https://ffmpeg.org/download.html")
        print("After installing, add ffmpeg to your system PATH.")
    elif current_platform == "Darwin":  # macOS
        print("It looks like ffmpeg is not installed.")
        print("You can install ffmpeg using Homebrew by running: brew install ffmpeg")
    elif current_platform == "Linux":
        print("It looks like ffmpeg is not installed.")
        print("You can install ffmpeg using your package manager. For example:")
        print("Ubuntu/Debian: sudo apt-get install ffmpeg")
        print("Fedora: sudo dnf install ffmpeg")
        print("Arch: sudo pacman -S ffmpeg")
    else:
        print("Unknown platform. Please install ffmpeg manually.")

def download_video(youtube_url, output_dir):
    """Download the YouTube video using yt-dlp, and save it in the specified directory."""
    # Ensure output directory exists
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    # yt-dlp options, including specifying the output directory
    ydl_opts = {
        'format': 'bv[height<=1080][ext=mp4]+ba[ext=m4a]/best[ext=mp4]/best',
        'outtmpl': os.path.join(output_dir, '%(title)s.%(ext)s'),  # Save the file in the specified directory
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([youtube_url])
    except yt_dlp.utils.DownloadError as e:
        print(f"Error: Failed to download the video. The video may not be available, or the URL is incorrect.")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")

def download_low_quality_video(youtube_url, output_dir):
    """Download the YouTube video in the lowest quality using yt-dlp."""
    # Ensure output directory exists
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    # yt-dlp options to download the lowest quality
    ydl_opts = {
        'format': 'worstvideo[ext=mp4]+worstaudio[ext=m4a]/worst[ext=mp4]/worst',  # Download lowest quality
        'outtmpl': os.path.join(output_dir, '%(title)s.%(ext)s'),  # Save the file in the specified directory
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([youtube_url])
    except yt_dlp.utils.DownloadError as e:
        print(f"Error: Failed to download the video: {e}")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")

def main():
    """Main function to handle command-line arguments and initiate the download process."""
    parser = argparse.ArgumentParser(description='Download videos from YouTube formatted for DJs.')
    parser.add_argument('url', type=str, help='The YouTube URL of the video to download')

    # Add multiple options for version
    parser.add_argument(
        '--version', '-v',
        action='version', 
        version=f'%(prog)s {VERSION}',
        help='Show the version of the program and exit'
    )

    # Optional argument for specifying output directory
    parser.add_argument(
        '-o', '--output', 
        type=str, 
        default=os.getcwd(),  # If not specified, download to the current working directory
        help='The directory where the downloaded video will be saved (default: current directory)'
    )

    args = parser.parse_args()

    youtube_url = args.url
    output_dir = args.output

    # Check if ffmpeg is installed
    if not check_ffmpeg():
        print("Error: ffmpeg is not installed or not found in your system PATH.")
        install_ffmpeg()
        sys.exit(1)

    # Check if the URL is valid
    if not is_valid_youtube_url(youtube_url):
        print("Error: The URL provided is not a valid YouTube URL. Please enter a valid URL.")
        sys.exit(1)

    # Try to download the video
    download_video(youtube_url, output_dir)

if __name__ == "__main__":
    main()
