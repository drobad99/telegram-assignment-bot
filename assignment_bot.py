# assignment_bot.py - Teacher's Assignment Bot with Group Forwarding
import logging
import os
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackQueryHandler, ContextTypes

# Setup logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

# Your bot token
BOT_TOKEN = "8292745525:AAGayCnqqlMLG5bVdByB2JYh_iuT8df_1x4"

# REPLACE THESE WITH YOUR ACTUAL GROUP IDs
CLASS_GROUPS = {
    "Prosthodontics": "-5000038418",  # REPLACE with actual group ID
    "Orthodontics": "-5048400011",    # REPLACE with actual group ID
    "Restorative & Aesthetic": "-5081959752",  # REPLACE with actual group ID
    "Basic Sciences": "-5026733679"   # REPLACE with actual group ID
}

# Store user class selections
user_classes = {}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send welcome message with class buttons"""
    keyboard = [
        [InlineKeyboardButton("🦷 Prosthodontics", callback_data="class_Prosthodontics")],
        [InlineKeyboardButton("🔵 Orthodontics", callback_data="class_Orthodontics")],
        [InlineKeyboardButton("💎 Restorative & Aesthetic", callback_data="class_Restorative & Aesthetic")],
        [InlineKeyboardButton("🔬 Basic Sciences", callback_data="class_Basic Sciences")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        "🎓 Welcome to Assignment Submission Bot!\n\n"
        "Please select your class:",
        reply_markup=reply_markup
    )

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle class selection"""
    query = update.callback_query
    await query.answer()
    
    class_name = query.data.replace("class_", "")
    user_id = query.from_user.id
    
    # Store user's class
    user_classes[user_id] = class_name
    
    await query.edit_message_text(
        f"✅ You selected: {class_name}\n\n"
        "📎 Now please upload your assignment file:\n"
        "• PDF documents\n"
        "• Word files (.doc, .docx)\n" 
        "• Images (JPG, PNG)\n"
        "• Or any other document"
    )

async def handle_file(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle file uploads and forward to class groups"""
    user_id = update.message.from_user.id
    user_name = update.message.from_user.full_name
    
    if user_id not in user_classes:
        await update.message.reply_text("❌ Please use /start first to select your class.")
        return
    
    class_name = user_classes[user_id]
    group_id = CLASS_GROUPS.get(class_name)
    
    if not group_id:
        await update.message.reply_text("❌ Error: Class group not configured. Please contact your teacher.")
        return
    
    # Get file info
    if update.message.document:
        file_name = update.message.document.file_name
        file_type = "document"
    elif update.message.photo:
        file_name = f"photo_from_{user_name}.jpg"
        file_type = "photo"
    else:
        await update.message.reply_text("❌ Please send a valid file (PDF, Word, Image, etc.)")
        return
    
    try:
        # Create assignments folder
        os.makedirs(f"assignments/{class_name}", exist_ok=True)
        
        # Download file locally
        if update.message.document:
            file = await update.message.document.get_file()
            file_path = f"assignments/{class_name}/{user_id}_{file_name}"
            await file.download_to_drive(file_path)
        elif update.message.photo:
            file = await update.message.photo[-1].get_file()
            file_path = f"assignments/{class_name}/{user_id}_{file_name}"
            await file.download_to_drive(file_path)
        
        # Forward to class group
        caption = f"📬 New Assignment Submission\n\nStudent: {user_name}\nClass: {class_name}\nFile: {file_name}"
        
        if update.message.document:
            await context.bot.send_document(
                chat_id=group_id,
                document=update.message.document.file_id,
                caption=caption
            )
        elif update.message.photo:
            await context.bot.send_photo(
                chat_id=group_id,
                photo=update.message.photo[-1].file_id,
                caption=caption
            )
        
        # Confirm to student
        await update.message.reply_text(
            f"✅ Assignment submitted successfully!\n\n"
            f"📚 Class: {class_name}\n"
            f"📄 File: {file_name}\n"
            f"👤 Student: {user_name}\n\n"
            f"Thank you! Your teacher will review it."
        )
        
        print(f"📬 New assignment: {user_name} -> {class_name} -> {file_name} -> Forwarded to group {group_id}")
        
    except Exception as e:
        logger.error(f"Error processing assignment: {e}")
        await update.message.reply_text("❌ Error submitting assignment. Please try again or contact your teacher.")

async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle text messages"""
    user_id = update.message.from_user.id
    if user_id in user_classes:
        await update.message.reply_text("📎 Please upload your assignment file (PDF, Word, Image, etc.)")
    else:
        await update.message.reply_text("👋 Welcome! Use /start to begin assignment submission.")

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Help command"""
    await update.message.reply_text(
        "📚 Assignment Bot Help:\n\n"
        "/start - Begin submission\n"
        "/help - This message\n\n"
        "How to submit:\n"
        "1. Click /start\n"
        "2. Select your class\n"
        "3. Upload your file\n\n"
        "Your submissions are private! ✅"
    )

async def get_group_id(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Command to get group ID - for setup only"""
    chat_id = update.message.chat_id
    await update.message.reply_text(f"This group ID is: `{chat_id}`", parse_mode='Markdown')

def main():
    """Start the bot"""
    # Create application
    application = Application.builder().token(BOT_TOKEN).build()
    
    # Add handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("getid", get_group_id))  # For getting group IDs
    application.add_handler(CallbackQueryHandler(button_handler))
    application.add_handler(MessageHandler(filters.Document.ALL | filters.PHOTO, handle_file))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
    
    print("🤖 Bot is starting...")
    print("Press Ctrl+C to stop the bot")
    application.run_polling()

if __name__ == '__main__':
    main()