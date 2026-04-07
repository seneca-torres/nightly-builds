import os
import yaml
import logging
from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application, 
    CommandHandler, 
    CallbackQueryHandler, 
    ContextTypes,
)

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', 
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Audit log file
AUDIT_LOG = os.path.expanduser('~/.clawdbot/quick_reply_audit.log')

def log_interaction(user_id: int, username: str, action: str, template: str):
    """Log all button interactions for audit purposes."""
    log_entry = f"{datetime.now().isoformat()} | User: {user_id} (@{username}) | Template: {template} | Action: {action}\n"
    with open(AUDIT_LOG, 'a') as f:
        f.write(log_entry)

def load_templates(config_path='config.yaml'):
    """Load reply templates from YAML config."""
    with open(config_path, 'r') as f:
        return yaml.safe_load(f)

def create_keyboard(template_name: str, templates: dict):
    """Create inline keyboard for a given template."""
    template = templates.get(template_name, {})
    
    if template.get('type') == 'inline_keyboard':
        keyboard = [
            [InlineKeyboardButton(btn['text'], callback_data=f"{template_name}_{btn['action']}") 
             for btn in template.get('buttons', [])]
        ]
        return InlineKeyboardMarkup(keyboard)
    
    return None

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send a message with available quick reply templates."""
    templates = load_templates()
    message = "Available Quick Reply Templates:\n"
    for template_name in templates.keys():
        message += f"- /quick_{template_name}\n"
    
    await update.message.reply_text(message)

async def quick_template(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Generate quick reply keyboard for a template."""
    template_name = context.args[0] if context.args else None
    
    if not template_name:
        await update.message.reply_text("Please specify a template name.")
        return
    
    templates = load_templates()
    keyboard = create_keyboard(template_name, templates)
    
    if keyboard:
        await update.message.reply_text(f"Quick Replies for {template_name}:", reply_markup=keyboard)
    else:
        await update.message.reply_text(f"No keyboard found for template {template_name}")

async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle button callback queries."""
    query = update.callback_query
    await query.answer()
    
    # Split the callback data to get template and action
    template_name, action = query.data.split('_', 1)
    
    # Log the interaction
    user = query.from_user
    log_interaction(user.id, user.username or 'unknown', action, template_name)
    
    # Provide feedback based on the action
    feedback_messages = {
        'approve_task': "Task approved ✅",
        'reject_task': "Task rejected ❌",
        'snooze_task': "Task snoozed ⏰"
    }
    
    # Edit the original message to show the selected action
    await query.edit_message_text(
        text=f"Selected: {feedback_messages.get(action, 'Action processed')}"
    )

def main():
    """Main function to run the Telegram bot."""
    # Load bot token from env or config file
    BOT_TOKEN = os.environ.get('TELEGRAM_BOT_TOKEN')
    if not BOT_TOKEN:
        logger.error("No Telegram Bot Token found. Set TELEGRAM_BOT_TOKEN environment variable.")
        return
    
    # Create the Application and pass it your bot's token
    application = Application.builder().token(BOT_TOKEN).build()
    
    # Register handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("quick", quick_template))
    application.add_handler(CallbackQueryHandler(button_callback))
    
    # Start the bot
    logger.info("Quick Reply Bot starting...")
    application.run_polling(drop_pending_updates=True)

if __name__ == '__main__':
    main()