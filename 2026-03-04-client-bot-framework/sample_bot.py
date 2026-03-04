from bot_framework import Bot

API_KEY = "test-api-key"

bot = Bot(api_key=API_KEY)

@bot.command("/start")
def start_handler(data):
    return "Welcome! Type /help to see available commands."

@bot.command("/help")
def help_handler(data):
    return "Commands available: /start, /help"

if __name__ == "__main__":
    bot.run()