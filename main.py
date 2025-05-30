from pyrogram import Client, filters
import os
import asyncio
import yt_dlp
import tempfile
from keep_alive import keep_alive

# Get credentials from environment variables
API_ID = os.getenv("API_ID", "123456")  # Replace with your api_id from https://my.telegram.org
API_HASH = os.getenv("API_HASH", "your_api_hash")
BOT_TOKEN = os.getenv("BOT_TOKEN", "your_bot_token")

OWNER_FILE = "owner.txt"

# Initialize the bot client
bot = Client("yt_downloader", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

# Store user sessions and YouTube URLs temporarily
user_sessions = {}

@bot.on_message(filters.private & filters.command("start"))
async def start(client, message):
    """Handle /start command and set owner if not exists"""
    try:
        if not os.path.exists(OWNER_FILE):
            # First user becomes the owner
            with open(OWNER_FILE, "w") as f:
                f.write(str(message.from_user.id))
            await message.reply(
                "🎉 **Welcome!** You are now the **OWNER** of this bot.\n\n"
                "✅ **Commands available:**\n"
                "• Send a YouTube link to download\n"
                "• `/broadcast <message>` - Send message to all users\n\n"
                "🎵 **Supported formats:** MP3 (audio) and MP4 (video)"
            )
        else:
            await message.reply(
                "👋 **Welcome to YouTube Downloader Bot!**\n\n"
                "📱 **How to use:**\n"
                "1. Send me a YouTube link\n"
                "2. Choose MP3 (audio) or MP4 (video)\n"
                "3. Download and enjoy!\n\n"
                "🔗 **Supported links:**\n"
                "• youtube.com/watch?v=...\n"
                "• youtu.be/..."
            )
    except Exception as e:
        await message.reply(f"❌ **Error:** {str(e)}")

@bot.on_message(filters.private & filters.command("broadcast"))
async def broadcast(client, message):
    """Handle broadcast command - only for owner"""
    try:
        # Check if owner file exists
        if not os.path.exists(OWNER_FILE):
            return await message.reply("❌ No owner set. Use /start first.")
        
        # Read owner ID
        with open(OWNER_FILE, "r") as f:
            owner_id = int(f.read().strip())

        # Check if user is owner
        if message.from_user.id != owner_id:
            return await message.reply("❌ **Access Denied:** Only the owner can use this command.")

        # Check if message provided
        if len(message.command) < 2:
            return await message.reply(
                "❌ **Usage:** `/broadcast <your message>`\n\n"
                "**Example:** `/broadcast Hello everyone! Bot is updated.`"
            )

        # Extract broadcast message
        broadcast_text = message.text.split(" ", 1)[1]
        
        # Send status message
        status_msg = await message.reply("📡 **Broadcasting message...**")
        
        sent_count = 0
        failed_count = 0
        
        # Get all dialogs and send broadcast
        async for dialog in client.get_dialogs():
            if dialog.chat.type in ["private"]:  # Only send to private chats
                try:
                    await client.send_message(
                        dialog.chat.id, 
                        f"📢 **Broadcast from Owner:**\n\n{broadcast_text}"
                    )
                    sent_count += 1
                    await asyncio.sleep(0.1)  # Small delay to avoid flooding
                except Exception:
                    failed_count += 1
        
        # Update status
        await status_msg.edit_text(
            f"✅ **Broadcast Complete!**\n\n"
            f"📊 **Statistics:**\n"
            f"• Sent: {sent_count} users\n"
            f"• Failed: {failed_count} users"
        )
        
    except Exception as e:
        await message.reply(f"❌ **Broadcast Error:** {str(e)}")

@bot.on_message(filters.private & filters.text & ~filters.command(["start", "broadcast", "mp3", "mp4"]))
async def handle_youtube_link(client, message):
    """Handle YouTube links and provide download options"""
    url = message.text.strip()
    
    # Validate YouTube URL
    if not ("youtube.com" in url or "youtu.be" in url):
        return await message.reply(
            "❌ **Invalid Link**\n\n"
            "Please send a valid YouTube link:\n"
            "• https://youtube.com/watch?v=...\n"
            "• https://youtu.be/..."
        )

    processing_msg = None
    try:
        # Show processing message
        processing_msg = await message.reply("🔍 **Processing YouTube link...**")
        
        # Get video information using yt-dlp
        ydl_opts = {
            'quiet': True,
            'no_warnings': True,
        }
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            title = info.get('title', 'Unknown')[:50]
            if len(info.get('title', '')) > 50:
                title += "..."
            duration = f"{info.get('duration', 0) // 60}:{info.get('duration', 0) % 60:02d}" if info.get('duration') else "Unknown"
            views = f"{info.get('view_count', 0):,}" if info.get('view_count') else "Unknown"
        
        # Store URL in user session
        user_sessions[message.from_user.id] = {"url": url, "info": info}
        
        # Update message with video info and options
        await processing_msg.edit_text(
            f"🎞️ **Video Found!**\n\n"
            f"📝 **Title:** {title}\n"
            f"⏱️ **Duration:** {duration}\n"
            f"👀 **Views:** {views}\n\n"
            f"📥 **Choose download format:**\n"
            f"• `/mp3` - Audio only (MP3)\n"
            f"• `/mp4` - Video with audio (MP4)"
        )
        
    except Exception as e:
        if processing_msg:
            try:
                await processing_msg.edit_text(f"❌ **Error processing video:** {str(e)}")
            except:
                await message.reply(f"❌ **Error processing video:** {str(e)}")
        else:
            await message.reply(f"❌ **Error processing video:** {str(e)}")

@bot.on_message(filters.command("mp3"))
async def download_mp3(client, message):
    """Download YouTube video as MP3 audio"""
    user_id = message.from_user.id
    
    # Check if user has a pending YouTube URL
    if user_id not in user_sessions:
        return await message.reply("❌ **No video selected.** Send a YouTube link first.")
    
    try:
        url = user_sessions[user_id]["url"]
        info = user_sessions[user_id]["info"]
        status_msg = await message.reply("🎵 **Downloading audio...**")
        
        # Download audio using yt-dlp
        with tempfile.TemporaryDirectory() as temp_dir:
            filename = f"audio_{user_id}"
            filepath = os.path.join(temp_dir, filename)
            
            ydl_opts = {
                'format': 'bestaudio/best',
                'outtmpl': f'{filepath}.%(ext)s',
                'postprocessors': [{
                    'key': 'FFmpegExtractAudio',
                    'preferredcodec': 'mp3',
                    'preferredquality': '192',
                }],
                'quiet': True,
            }
            
            await status_msg.edit_text("📥 **Downloading... Please wait**")
            
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([url])
            
            # Find the downloaded file
            mp3_file = f"{filepath}.mp3"
            if not os.path.exists(mp3_file):
                # Try other possible extensions
                for ext in ['mp3', 'm4a', 'webm']:
                    test_file = f"{filepath}.{ext}"
                    if os.path.exists(test_file):
                        mp3_file = test_file
                        break
            
            if not os.path.exists(mp3_file):
                return await status_msg.edit_text("❌ **Audio download failed.**")
            
            # Send audio file
            await status_msg.edit_text("📤 **Uploading audio...**")
            await message.reply_audio(
                mp3_file,
                title=info.get('title', 'Unknown'),
                performer="YouTube Downloader Bot",
                caption=f"🎵 **{info.get('title', 'Unknown')}**\n🔗 {url}\n\n📚 **Made by Study Dimension**"
            )
        
        # Clear user session
        del user_sessions[user_id]
        await status_msg.delete()
        
    except Exception as e:
        await message.reply(f"❌ **Download failed:** {str(e)}")

@bot.on_message(filters.command("mp4"))
async def download_mp4(client, message):
    """Download YouTube video as MP4"""
    user_id = message.from_user.id
    
    # Check if user has a pending YouTube URL
    if user_id not in user_sessions:
        return await message.reply("❌ **No video selected.** Send a YouTube link first.")
    
    try:
        url = user_sessions[user_id]["url"]
        info = user_sessions[user_id]["info"]
        status_msg = await message.reply("🎬 **Downloading video...**")
        
        # Download video using yt-dlp
        with tempfile.TemporaryDirectory() as temp_dir:
            filename = f"video_{user_id}.mp4"
            filepath = os.path.join(temp_dir, filename)
            
            ydl_opts = {
                'format': 'best[height<=720][filesize<50M]/best[filesize<50M]',
                'outtmpl': filepath,
                'quiet': True,
            }
            
            await status_msg.edit_text("📥 **Downloading... Please wait**")
            
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([url])
            
            if not os.path.exists(filepath):
                return await status_msg.edit_text("❌ **Video download failed or file too large (>50MB).**")
            
            # Check file size
            file_size = os.path.getsize(filepath)
            if file_size > 50 * 1024 * 1024:  # 50MB
                return await status_msg.edit_text(
                    "❌ **File too large** (>50MB)\n\n"
                    "Try downloading audio instead with `/mp3`"
                )
            
            # Send video file
            await status_msg.edit_text("📤 **Uploading video...**")
            await message.reply_video(
                filepath,
                caption=f"🎬 **{info.get('title', 'Unknown')}**\n🔗 {url}\n\n📚 **Made by Study Dimension**",
                supports_streaming=True
            )
        
        # Clear user session
        del user_sessions[user_id]
        await status_msg.delete()
        
    except Exception as e:
        await message.reply(f"❌ **Download failed:** {str(e)}")

@bot.on_message(filters.command("help"))
async def help_command(client, message):
    """Show help information"""
    help_text = (
        "🤖 **YouTube Downloader Bot Help**\n\n"
        "📱 **Commands:**\n"
        "• `/start` - Start the bot\n"
        "• `/help` - Show this help\n"
        "• `/mp3` - Download as audio (after sending link)\n"
        "• `/mp4` - Download as video (after sending link)\n\n"
        "👑 **Owner Commands:**\n"
        "• `/broadcast <message>` - Send message to all users\n\n"
        "📝 **How to use:**\n"
        "1. Send a YouTube link\n"
        "2. Choose MP3 or MP4 format\n"
        "3. Wait for download and upload\n\n"
        "⚠️ **Limitations:**\n"
        "• Video files must be under 50MB\n"
        "• Only YouTube links are supported"
    )
    await message.reply(help_text)

def main():
    """Main function to start the bot"""
    print("🤖 Starting YouTube Downloader Bot...")
    
    # Start keep-alive server
    keep_alive()
    
    # Start the bot
    print("✅ Bot is running!")
    bot.run()

if __name__ == "__main__":
    main()
