# YouTube Downloader Telegram Bot

A powerful Telegram bot that downloads YouTube videos in MP3 and MP4 formats with owner-based broadcast system.

## Features

- Download YouTube videos as MP3 (audio only)
- Download YouTube videos as MP4 (video with audio)
- Owner-based broadcast system (first user becomes owner)
- Automatic file size checking (50MB limit for Telegram)
- Clean user interface with status updates
- Error handling and retry mechanisms

## Setup

1. Get your Telegram API credentials:
   - Visit https://my.telegram.org
   - Create a new application
   - Note down API_ID and API_HASH

2. Create a bot:
   - Chat with @BotFather on Telegram
   - Use /newbot command
   - Get your BOT_TOKEN

3. Set environment variables:
   - API_ID
   - API_HASH
   - BOT_TOKEN

## Commands

- `/start` - Start the bot and set owner
- `/help` - Show help information
- `/broadcast <message>` - Send message to all users (owner only)
- `/mp3` - Download as audio after sending YouTube link
- `/mp4` - Download as video after sending YouTube link

## Usage

1. Send /start to the bot
2. Send any YouTube link
3. Choose MP3 or MP4 format
4. Wait for download and upload

Made by Study Dimension