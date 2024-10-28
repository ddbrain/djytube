import yt_dlp
import argparse
import sys
import re
import os
import subprocess
import platform
import shutil

VERSION = "0.2.1"

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

    # yt-dlp options, specifying output directory and file format
    ydl_opts = {
        'format': 'bv[height<=1080][vcodec=avc1][ext=mp4]+ba[ext=m4a]/bv[height<=1080][ext=mp4]+ba[ext=m4a]/best[ext=mp4]/best',  # Ensure video and audio are merged into mp4
        'outtmpl': os.path.join(output_dir, '%(title)s.%(ext)s'),  # Save the file in the specified directory
    }

    ydl_opts2 = {
        'outtmpl': '%(title)s.mp4',  # Output template
        'simulate': True,            # Only simulate to print info without downloading
        'forcefilename': True,        # Force to print the filename
        'postprocessors': [{
            'key': 'FFmpegVideoConvertor',
            'preferedformat': 'mp4'      # Ensures the output is always .mp4
        }]
    }

    try:
        downloaded_file = None  # Placeholder to store the actual downloaded and merged .mp4 file path

        # Define a hook to capture the .mp4 file path once the download and merging is complete
        def ydl_hook(d):
            nonlocal downloaded_file
            if d['status'] == 'finished' and d['filename'].endswith('.mp4'):
                downloaded_file = d['filename']  # Capture the final .mp4 filename

        # Add the hook to options
        ydl_opts['progress_hooks'] = [ydl_hook]

        # Perform the download and merging
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([youtube_url])

        with yt_dlp.YoutubeDL(ydl_opts2) as ydl2:
            info = ydl2.extract_info(youtube_url, download=False)
            # Manually adjust the filename to .mp4
            downloaded_file = ydl.prepare_filename(info).rsplit(".", 1)[0] + ".mp4"
        
        # Check if the merged .mp4 file was captured
        if downloaded_file:
            # Properly escape the filename for the ffprobe command
            safe_filename = shlex.quote(downloaded_file)
            codec_check_cmd = f"ffprobe -v error -select_streams v:0 -show_entries stream=codec_name -of default=noprint_wrappers=1:nokey=1 '{safe_filename}'"
            codec = subprocess.check_output(codec_check_cmd, shell=True).decode().strip()
            
            if codec == 'h264':
                print(f"Video is already in H.264 format: {downloaded_file}")
            else:
                # Convert the final .mp4 file to H.264 codec if not already in H.264
                h264_output_file = downloaded_file.replace('.mp4', '_h264.mp4')
                conversion_command = f'ffmpeg -i "{safe_filename}" -c:v libx264 -c:a aac "{h264_output_file}"'
            
                try:
                    subprocess.run(conversion_command, shell=True, check=True)
                    print(f'Video successfully converted to H.264 format: {h264_output_file}')
                except subprocess.CalledProcessError:
                    print('Error: Failed to convert the video to H.264 format.')
        else:
            print("Error: Downloaded .mp4 file path could not be determined.")

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
    parser.add_argument('url', type=str, nargs='?', help='The YouTube URL of the video to download (if not using -f/--file)')

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
        default='.',
        help='Specify the output directory where the downloaded video will be saved'
    )

    # New argument for file input
    parser.add_argument(
        '-f', '--file',
        type=str,
        help='Path to a text file containing YouTube URLs to download, one per line'
    )

    # Parse the command-line arguments
    args = parser.parse_args()

    # Check if ffmpeg is installed
    if not check_ffmpeg():
        install_ffmpeg()
        sys.exit("ffmpeg is required for video conversion. Please install it and try again.")

    # Determine the mode of processing based on the presence of -f/--file
    if args.file:
        # Bulk processing with file
        try:
            with open(args.file, 'r') as url_file:
                urls = [line.strip() for line in url_file if line.strip()]
        except FileNotFoundError:
            print(f"Error: The file '{args.file}' was not found.")
            sys.exit(1)
    elif args.url:
        # Single URL processing
        urls = [args.url]
    else:
        # Neither file nor single URL provided
        print("Error: Please provide a YouTube URL or use -f/--file to specify a file with URLs.")
        sys.exit(1)

    # Process each URL
    for url in urls:
        if not is_valid_youtube_url(url):
            print(f"Skipping invalid YouTube URL: {url}")
            continue
        download_video(url, args.output)

if __name__ == "__main__":
    main()
