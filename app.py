import logging
import os
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
import yt_dlp
import validators

# Set up logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

# Define constants
MAX_FILE_SIZE = 400 * 1024 * 1024  # 400 MB
DOWNLOAD_DIR = "downloads"

# Ensure download directory exists
if not os.path.exists(DOWNLOAD_DIR):
    os.makedirs(DOWNLOAD_DIR)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send a welcome message with animation and emoji."""
    welcome_message = (
        "🎥 <b>Welcome to Video Downloader Bot! 🎥</b>\n\n"
        "✨ Send me a valid video URL, and I'll grab it for you!\n"
        "🚀 Supported platforms: YouTube, Vimeo, and more!\n"
        "ℹ️ Type /help for assistance.\n"
        "<i>(Watch the magic unfold! ✨)</i>"
    )
    await update.message.reply_text(welcome_message, parse_mode='HTML')

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send a help message with interactive flair."""
    help_message = (
        "ℹ️ <u>How to Use Video Downloader Bot:</u> ✨\n\n"
        "1. Send a valid video URL 🎬\n"
        "2. I'll download it lightning-fast! ⚡\n"
        "3. Get it back if under 400MB 📥\n\n"
        "<b>Commands:</b>\n"
        "/start - Kick things off 🎉\n"
        "/help - See this message ❓\n\n"
        "<i>(Hover over text for a surprise! 😄)</i>"
    )
    await update.message.reply_text(help_message, parse_mode='HTML')

async def download_video(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle video download with optimized speed and file sending as document."""
    url = update.message.text.strip()
    user_id = update.message.from_user.id
    chat_id = update.message.chat_id

    # Validate URL
    if not validators.url(url):
        await update.message.reply_text("❌ <b>Oops!</b> Send a valid URL! 😕", parse_mode='HTML')
        return

    # Notify user with animation
    await update.message.reply_text("⏳ <b>Downloading...</b> 🌠 (Spinning up turbo mode!)", parse_mode='HTML')

    # Set up yt-dlp options for super fast download
    ydl_opts = {
        'outtmpl': f'{DOWNLOAD_DIR}/{user_id}_%(title)s.%(ext)s',
        'format': 'bestvideo[filesize<400M][ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best',
        'merge_output_format': 'mp4',
        'quiet': True,
        'no_warnings': True,
        'nocheckcertificate': True,  # Optimize speed by skipping cert checks
        'http_chunk_size': 10485760,  # 10MB chunks for faster streaming
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            # Extract video info
            info = ydl.extract_info(url, download=False)
            video_title = info.get('title', 'video')
            output_path = ydl.prepare_filename(info)

            # Download the video
            ydl.download([url])

            # Check file size
            file_size = os.path.getsize(output_path)
            if file_size > MAX_FILE_SIZE:
                await update.message.reply_text(
                    f"❌ <b>Sorry!</b> '{video_title}' is too large ({file_size / 1024 / 1024:.2f} MB). Max is 400MB! 😞",
                    parse_mode='HTML'
                )
                os.remove(output_path)
                return

            # Send as document (file) instead of media, with content type detection disabled
            with open(output_path, 'rb') as video_file:
                await context.bot.send_document(
                    chat_id=chat_id,
                    document=video_file,
                    filename=f"{video_title}.mp4",
                    caption=f"🎉 <b>Here’s your file!</b> {video_title} 🚀",
                    parse_mode='HTML',
                    disable_content_type_detection=True  # Force Telegram to treat as a file
                )

            # Clean up the file after sending
            os.remove(output_path)
            await update.message.reply_text("🗑️ <b>Cleanup complete!</b> File deleted from server. 🌟", parse_mode='HTML')

    except yt_dlp.DownloadError:
        await update.message.reply_text(
            "❌ <b>Uh-oh!</b> Download failed. URL might not work or is unsupported. 😔 Try again!",
            parse_mode='HTML'
        )
    except Exception as e:
        logger.error(f"Error processing video download: {e}")
        await update.message.reply_text(
            "❌ <b>Oops!</b> Something went wrong. Try again later! 😕",
            parse_mode='HTML'
        )

async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Log errors with a user-friendly response."""
    logger.error(f"Update {update} caused error {context.error}")
    if update and update.message:
        await update.message.reply_text(
            "❌ <b>Yikes!</b> An error occurred. Please try again! 😣",
            parse_mode='HTML'
        )

def main() -> None:
    """Run the bot with the provided token."""
    bot_token = '7762460516:AAE_hFtCqp3X-0vvzYuXgJGXvXbYiMUrwxY'

    # Create the Application
    application = Application.builder().token(bot_token).build()

    # Add handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, download_video))
    application.add_error_handler(error_handler)

    # Start the bot
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == '__main__':
    main()
