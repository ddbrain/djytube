# DJytube Youtube Downloader

A simple command-line tool to download YouTube videos using `yt-dlp`. This tool allows you to download videos in the highest available quality up to 1080p, with audio merged into a single file.

## Features

- Downloads YouTube videos in 1080p or the best available quality.
- Merges video and audio into a single MP4 file.
- Easy to install as a command-line tool using `pipx` or `poetry`.

## Requirements

- Python 3.7 or higher
- [ffmpeg] (https://www.ffmpeg.org/download.html)
- [pipx](https://pypa.github.io/pipx/installation/) for installing as a standalone CLI tool

## Installation

### Option 1: Installing via `pipx` on `MacOS`

1. Ensure `pipx` is installed:

   ```bash
   brew install pipx
   pipx ensurepath
   sudo pipx ensurepath --global # optional to allow pipx actions with --global argument
   ```
2. Install djytube
   ```bash
   pipx install git+https://github.com/ddbrain/djytube.git
   ```
