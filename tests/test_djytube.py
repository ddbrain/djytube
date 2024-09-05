import pytest
import os
import tempfile
import subprocess
import platform
import re
from installer.djytube import is_valid_youtube_url, check_ffmpeg

# A small, publicly accessible YouTube video for testing
TEST_YOUTUBE_URL = "https://www.youtube.com/watch?v=V5YNMd5N5BY"  # A small, test video provided by YouTube

def print_result(message, passed):
    """Print the result with 'OK' or 'FAIL' on Windows, and checkmark or cross on other platforms."""
    if platform.system() == 'Windows':
        # Use OK/FAIL on Windows
        if passed:
            print(f"OK: {message}")
        else:
            print(f"FAIL: {message}")
            pytest.fail(message)  # Explicitly fail if the test didn't pass
    else:
        # Use checkmark/cross on other platforms
        if passed:
            print(f"✔ {message}")
        else:
            print(f"✖ {message}")
            pytest.fail(message)  # Explicitly fail if the test didn't pass

def test_valid_youtube_url():
    print('\n')
    try:
        assert is_valid_youtube_url(TEST_YOUTUBE_URL)
        print_result("Valid YouTube URL test passed", True)
    except AssertionError as e:
        print_result(f"Valid YouTube URL test failed: {e}", False)

def test_invalid_youtube_url():
    try:
        assert not is_valid_youtube_url("https://www.invalid-url.com/watch?v=12345")
        print_result("Invalid YouTube URL test passed", True)
    except AssertionError as e:
        print_result(f"Invalid YouTube URL test failed: {e}", False)

def test_ffmpeg_installed():
    """Ensure that ffmpeg is installed."""
    try:
        assert check_ffmpeg() == True, "ffmpeg is not installed or not available in PATH."
        print_result("ffmpeg installed test passed", True)
    except AssertionError as e:
        print_result(f"ffmpeg installed test failed: {e}", False)

def get_available_formats(video_url):
    """Get a list of available formats using yt-dlp --list-formats, ignoring any warning messages."""
    try:
        result = subprocess.run(
            ["yt-dlp", "--list-formats", video_url],
            capture_output=True,
            text=True
        )
        
        # Filter out lines that are warnings or error messages, typically starting with '['
        formats_list = [line for line in result.stdout.splitlines() if not line.startswith('[')]
        
        # Join the filtered lines back into a string for further processing
        return "\n".join(formats_list)
    except Exception as e:
        pytest.fail(f"Failed to list formats: {e}")
        return None

def choose_format(formats_list):
    """
    Choose the MP4 video format with the lowest file size based on the available formats.
    The format list should contain information about the formats, including file sizes.
    """
    # Regex to capture file size in the format list (e.g., '100.0MiB', '500KiB')
    size_pattern = re.compile(r'(?P<size>\d+(\.\d+)?)(?P<unit>[KMG]iB)')
    
    # Regex to validate that the format ID consists of safe characters (alphanumeric, dashes, underscores)
    valid_format_id_pattern = re.compile(r'^[a-zA-Z0-9_-]+$')

    lowest_format = None
    lowest_size_in_kb = float('inf')  # Start with a very large size to find the smallest one

    for line in formats_list.splitlines():
        # Ignore lines that are not video formats or contain warnings
        if 'mp4' not in line.lower() or 'm4a' in line.lower() or '[' in line:
            continue

        # Extract the format ID and size if available
        match = size_pattern.search(line)
        if match:
            size = float(match.group('size'))
            unit = match.group('unit')

            # Convert the size to kilobytes (KB) for comparison
            if unit == 'GiB':
                size_in_kb = size * 1024 * 1024
            elif unit == 'MiB':
                size_in_kb = size * 1024
            elif unit == 'KiB':
                size_in_kb = size
            else:
                continue

            # Extract the format ID (the first column) and validate it
            format_id = line.split()[0]
            if not valid_format_id_pattern.match(format_id):
                continue  # Skip invalid format IDs

            # Update the lowest format if this one has a smaller size
            if size_in_kb < lowest_size_in_kb:
                lowest_format = format_id
                lowest_size_in_kb = size_in_kb

    if lowest_format:
        return lowest_format
    else:
        pytest.fail("No suitable MP4 video format with size information found.")
        return None

def test_download_low_quality_video(pytestconfig):
    """Test downloading the lowest quality MP4 video from YouTube and check for combined audio-video file."""
    
    if not pytestconfig.getoption("--run-download-tests"):
        pytest.skip("Skipping download test: --run-download-tests not provided")
    
    if not check_ffmpeg():
        pytest.skip("Skipping download test: ffmpeg is not installed")
    
    # Get available formats for the video
    formats = get_available_formats(TEST_YOUTUBE_URL)
    if formats is None:
        pytest.fail("Could not retrieve video formats.")
    
    # Choose the lowest MP4 format based on available formats
    chosen_format = choose_format(formats)
    if chosen_format is None:
        pytest.fail("Could not select a suitable format.")

    # Create a temporary directory to store the downloaded file
    with tempfile.TemporaryDirectory() as temp_dir:
        try:
            # Adjust quoting and path separators based on the operating system
            if platform.system() == 'Windows':
                download_cmd = f'yt-dlp --format "{chosen_format}" -o "{temp_dir}\\%(title)s.%(ext)s" {TEST_YOUTUBE_URL}'
            else:
                download_cmd = f"yt-dlp --format '{chosen_format}' -o '{temp_dir}/%(title)s.%(ext)s' {TEST_YOUTUBE_URL}"
            
            # Execute the command to download the video and audio, and merge them using ffmpeg
            os.system(download_cmd)
            
            # Check if any files were downloaded to the temporary directory
            downloaded_files = os.listdir(temp_dir)
            assert len(downloaded_files) > 0, "No files were downloaded."

            # Check if the downloaded file has a valid video file extension and is the combined file
            downloaded_file = downloaded_files[0]
            assert downloaded_file.endswith(('.mp4', '.mkv', '.webm')), f"Unexpected file type: {downloaded_file}"

            # Ensure the combined audio-video file exists in the temporary directory
            downloaded_file_path = os.path.join(temp_dir, downloaded_file)
            assert os.path.isfile(downloaded_file_path), f"Downloaded file not found: {downloaded_file_path}"

            print_result("Download and merge audio-video test passed", True)
        except AssertionError as e:
            print_result(f"Download and merge audio-video test failed: {e}", False)