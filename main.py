import telebot
from telebot import types
from openai import OpenAI
import requests
from PIL import Image
import io
import ssl
from requests.adapters import HTTPAdapter
from urllib3.poolmanager import PoolManager
from huggingface_hub import InferenceClient
import time
import os
import random

state = 0

# Initialize the Telegram bot
bot = telebot.TeleBot('8066998361:AAFxn8okbnM6DnM_tD3JsahBA9ymH7N5ES4')


# Create an SSL context and set the SSL/TLS version
class SSLAdapter(HTTPAdapter):

    def __init__(self, ssl_context=None, **kwargs):
        self.ssl_context = ssl_context
        super().__init__(**kwargs)

    def init_poolmanager(self, *args, **kwargs):
        context = self.ssl_context or ssl.create_default_context()
        kwargs['ssl_context'] = context
        return super().init_poolmanager(*args, **kwargs)


# Create an SSL context and set SSL/TLS parameters
context = ssl.create_default_context()
context.set_ciphers('DEFAULT@SECLEVEL=1')
context.options |= ssl.OP_NO_TLSv1_3

# Create a session to manage connection settings
session = requests.Session()

# Mount the custom adapter for HTTPS requests
adapter = SSLAdapter(ssl_context=context)
session.mount('https://', adapter)

# Monkey-patch the requests library used by telebot
import telebot.apihelper

telebot.apihelper.SESSION = session  # type: ignore

# Define your bot API URL
url = "https://api.telegram.org/bot8066998361:AAFxn8okbnM6DnM_tD3JsahBA9ymH7N5ES4/getMe"

# Send the request using the session with the custom adapter and SSL context
response = session.get(url)

# Print the response text to verify the result
print(response.text)

HF_API_KEY = "Your hugging face token"
API_URL = "https://api-inference.huggingface.co/models/black-forest-labs/FLUX.1-dev"
headers = {"Authorization": f"Bearer {HF_API_KEY}"}

API_URL2 = "https://api-inference.huggingface.co/models/facebook/musicgen-small"
headers2 = {"Authorization": f"Bearer {HF_API_KEY}"}

client = OpenAI(
    base_url="https://router.huggingface.co/v1",
    api_key=HF_API_KEY,
)

client2 = InferenceClient(
    provider="hf-inference",
    api_key=HF_API_KEY,
)


@bot.message_handler(commands=['option'])
def option(message):
    markup = types.InlineKeyboardMarkup()
    chat_button = types.InlineKeyboardButton("Chat", callback_data="chat")
    image_button = types.InlineKeyboardButton("Image", callback_data="image")
    summarize_button = types.InlineKeyboardButton("Summarize",
                                                  callback_data="summarize")
    markup.add(chat_button, image_button, summarize_button)
    bot.send_message(chat_id=message.chat.id,
                     text="Choose an option:",
                     reply_markup=markup)


@bot.callback_query_handler(func=lambda call: True)
def handle_user_choice(call):
    if call.data == "chat":
        chat(call.message)
    elif call.data == "image":
        image(call.message)
    elif call.data == "summarize":
        summarize(call.message)


@bot.message_handler(commands=['chat'])
def chat(message):
    global state
    bot.reply_to(
        message,
        "You can now chat with the bot. Type your message and press enter to send it."
    )
    state = 1


@bot.message_handler(commands=['image'])
def image(message):
    global state
    bot.reply_to(
        message,
        "You can now generate an image with this bot. Type your message and press enter to send it"
    )
    state = 2


@bot.message_handler(commands=['stop'])
def stop(message):
    global state
    bot.reply_to(message, "See you next time!")
    state = 0


@bot.message_handler(commands=['start'])
def start(message):
    global state
    bot.reply_to(
        message,
        "🎉 Welcome to Sayargyi Bot! 🎉\n\nHi there! 👋 I'm your personal assistant, here to make your experience fun and creative. 🤖✨\n\nYou can:\n\n🗨️ Chat with me anytime you want!\n🎨 Generate Images to bring your ideas to life!\n Summarize lengthy texts to insightful notes \nJust choose what you'd like to do, and let's get started! 🚀"
    )

    # Create custom keyboard with shortcut buttons
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    chat_btn = types.KeyboardButton('💬 Chat')
    image_btn = types.KeyboardButton('🖼️ Image')
    summarize_btn = types.KeyboardButton(' summarize')
    help_btn = types.KeyboardButton('❓ Help')
    markup.add(chat_btn, image_btn, summarize_btn, help_btn)

    bot.send_message(chat_id=message.chat.id,
                     text="Use these shortcuts for quick access:",
                     reply_markup=markup)

    option(message)


@bot.message_handler(commands=['summarize'])
def summarize(message):
    global state
    bot.reply_to(
        message,
        "You can now summarize texts with this bot. Type your message and press enter to send it"
    )
    state = 3


@bot.message_handler()
def handle_message(message):
    global state
    if state == 1:
        messages = [{"role": "user", "content": message.text}]

        try:

            completion = client.chat.completions.create(
                model="deepseek-ai/DeepSeek-V3.2-Exp:novita",
                messages=messages,  # type: ignore
                max_tokens=500)

            # Check if choices exist and are not empty
            if hasattr(completion, 'choices') and completion.choices:
                print(f"Number of choices: {len(completion.choices)}")

                response = completion.choices[0].message

                bot.reply_to(
                    message, response.content if hasattr(response, 'content')
                    and response.content else "No response generated")
            else:

                bot.reply_to(message, "No response generated from the model")

        except Exception as e:

            bot.reply_to(message,
                         f"An error occurred: {type(e).__name__}: {str(e)}")
    elif state == 2:
        prompt = message.text
        bot.send_message(chat_id=message.chat.id, text="I am thinking....")
        bot.send_message(chat_id=message.chat.id,
                         text="and DON'T TOUCH ANYTHING")
        try:
            image = query_image({"inputs": prompt})
            image_bytes = io.BytesIO()
            image.save(image_bytes, format="JPEG")
            image_bytes.seek(0)
            bot.send_photo(chat_id=message.chat.id,
                           photo=image_bytes,
                           caption=message.text)
        except Exception as e:
            bot.send_message(chat_id=message.chat.id,
                             text=f"An error occurred: {e}")
    elif state == 3:

        prompt = message.text
        bot.send_message(chat_id=message.chat.id, text="I am thinking....")
        bot.send_message(chat_id=message.chat.id,
                         text="and DON'T TOUCH ANYTHING")

        try:
            result = client2.summarization(
                message.text,
                model="Falconsai/text_summarization",
            )

            # Extract summary text properly
            summary_text = None

            if hasattr(result, 'summary_text'):
                summary_text = result.summary_text
            elif isinstance(result, dict) and 'summary_text' in result:
                summary_text = result['summary_text']
            elif isinstance(result, list) and len(result) > 0:
                first_item = result[0]
                if hasattr(first_item, 'summary_text'):
                    summary_text = first_item.summary_text
                elif isinstance(first_item,
                                dict) and 'summary_text' in first_item:
                    summary_text = first_item['summary_text']

            if summary_text and summary_text.strip():
                bot.reply_to(message, summary_text)
            else:
                bot.reply_to(message, "No summary generated or empty response")

        except Exception as e:
            bot.send_message(chat_id=message.chat.id,
                             text=f"An error occurred: {e}")

    else:
        bot.reply_to(
            message,
            "Invalid command. Please use /chat, /image, /summarize, or /option to observe the commands"
        )


# Start polling and handle potential errors
while True:
    try:
        bot.polling(none_stop=True)
    except Exception as e:
        print(f"Error: {e}")
        time.sleep(10)  # Wait for 10 seconds before trying again
