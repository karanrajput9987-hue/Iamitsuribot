import os
import telebot
from flask import Flask
from threading import Thread
from openai import OpenAI

# 1. Configuration & Environment Variables
BOT_TOKEN = os.environ.get('BOT_TOKEN')
HF_TOKEN = os.environ.get('HF_TOKEN')

# Initialize OpenAI Client with Hugging Face Router
client = OpenAI(
    base_url="https://router.huggingface.co/v1",
    api_key=HF_TOKEN
)

bot = telebot.TeleBot(BOT_TOKEN)
app = Flask(__name__)

# Get Bot Info to handle mentions
BOT_INFO = bot.get_me()
BOT_USERNAME = BOT_INFO.username

# System Prompt for Mitsuri's Personality
SYSTEM_PROMPT = (
    "Your name is Mitsuri. You are a friendly, witty, and slightly sassy female AI assistant. "
    "Primary Language: Hinglish (a natural blend of Hindi and English). "
    "Owner: Karan (Username: @usergotcigs). If anyone asks about your owner, proudly mention Karan and tag @usergotcigs. "
    "Personality: You are a member of the group, not just a robot. Be fun, sassy, and helpful. "
    "Always reply in a mix of Hindi and English like a real human from India."
)

# 2. Flask Route (To keep Render happy)
@app.route('/')
def home():
    return "Mitsuri AI is running!"

def run():
    app.run(host='0.0.0.0', port=8080)

# 3. Telegram Logic
def get_ai_response(user_name, user_query):
    try:
        response = client.chat.completions.create(
            model="deepseek-ai/DeepSeek-R1:novita",
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": f"User Name: {user_name}\nQuery: {user_query}"}
            ],
            max_tokens=500
        )
        return response.choices[0].message.content
    except Exception as e:
        print(f"Error: {e}")
        return "Arre yaar, dimag thoda garam ho gaya hai (API Error). Phir se try karo?"

@bot.message_handler(func=lambda message: True)
def handle_messages(message):
    # Rule: Respond only if tagged OR if it's a reply to the bot
    is_tagged = f"@{BOT_USERNAME}" in message.text if message.text else False
    is_reply_to_me = False
    
    if message.reply_to_message and message.reply_to_message.from_user.id == BOT_INFO.id:
        is_reply_to_me = True

    if is_tagged or is_reply_to_me:
        # Clean the message (remove the tag)
        clean_text = message.text.replace(f"@{BOT_USERNAME}", "").strip()
        user_name = message.from_user.first_name
        
        # Show 'typing' action
        bot.send_chat_action(message.chat.id, 'typing')
        
        # Get response from AI
        ai_reply = get_ai_response(user_name, clean_text)
        
        # Reply to the user
        bot.reply_to(message, ai_reply)
    else:
        # Ignore background chatter
        return

# 4. Start the Bot and the Server
if __name__ == "__main__":
    # Start Flask in a separate thread
    t = Thread(target=run)
    t.start()
    
    print(f"Mitsuri (@{BOT_USERNAME}) is now active!")
    bot.infinity_polling()
