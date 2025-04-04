import telebot
from telebot import types
from openai import OpenAI
import requests
from PIL import Image
import io
import ssl
from requests.adapters import HTTPAdapter
from urllib3.poolmanager import PoolManager
import time

state = 0

# Initialize the Telegram bot
bot = telebot.TeleBot('Your telegram bot token')


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

telebot.apihelper.SESSION = session

# Define your bot API URL
url = "https://api.telegram.org/bot<Your telegram bot token>/getMe"

# Send the request using the session with the custom adapter and SSL context
response = session.get(url)

# Print the response text to verify the result
print(response.text)

HF_API_KEY = "Your hugging face token"
API_URL = "https://api-inference.huggingface.co/models/black-forest-labs/FLUX.1-dev"
headers = {"Authorization": f"Bearer {HF_API_KEY}"}

API_URL2 = "https://api-inference.huggingface.co/models/facebook/musicgen-small"
headers2 = {"Authorization": f"Bearer {HF_API_KEY}"}


def query_musicgen(prompt):
    response = requests.post(API_URL2,
                             headers=headers2,
                             json={"inputs": prompt})
    if response.status_code == 200:
        return response.content  # Return the raw audio bytes
    else:
        raise Exception(f"Error {response.status_code}: {response.json()}")


def query_image(payload):
    try:
        response = requests.post(API_URL,
                                 headers=headers,
                                 json=payload,
                                 timeout=500)
        response.raise_for_status()  # Raise an exception for HTTP errors
        return Image.open(io.BytesIO(response.content))
    except requests.exceptions.RequestException as e:
        raise Exception(f"Request error: {e}")
    except Exception as e:
        raise Exception(f"Image processing error: {e}")


# Initialize the OpenAI client with Hugging Face's Inference API
client = OpenAI(base_url="https://api-inference.huggingface.co/v1/",
                api_key=HF_API_KEY)


@bot.message_handler(commands=['option'])
def option(message):
    markup = types.InlineKeyboardMarkup()
    chat_button = types.InlineKeyboardButton("Chat", callback_data="chat")
    image_button = types.InlineKeyboardButton("Image", callback_data="image")
    music_button = types.InlineKeyboardButton("Music", callback_data="music")
    markup.add(chat_button, image_button, music_button)
    bot.send_message(chat_id=message.chat.id,
                     text="Choose an option:",
                     reply_markup=markup)


@bot.callback_query_handler(func=lambda call: True)
def handle_user_choice(call):
    if call.data == "chat":
        chat(call.message)
    elif call.data == "image":
        image(call.message)
    elif call.data == "music":
        music(call.message)


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
        "You can now generate image with this bot. Type your message and press enter to send it"
    )
    state = 2


@bot.message_handler(commands=['stop'])
def stop(message):
    global state
    bot.reply_to(message, "See you next time!")
    state = 0


@bot.message_handler(commands=['start'])
def start(message):
    globalfrome
    bot.reply_to(
        message,
        "🎉 Welcome to Sayargyi Bot! 🎉\n\nHi there! 👋 I'm your personal assistant, here to make your experience fun and creative. 🤖✨\n\nYou can:\n\n🗨️ Chat with me anytime you want!\n🎨 Generate Images to bring your ideas to life!\n🎶 Generate Music to add some rhythm to your day! 🎧🎶\nJust choose what you'd like to do, and let's get started! 🚀"
    )

    # Create custom keyboard with shortcut buttons
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    chat_btn = types.KeyboardButton('💬 Chat')
    image_btn = types.KeyboardButton('🖼️ Image')
    music_btn = types.KeyboardButton('🎵 Music')
    help_btn = types.KeyboardButton('❓ Help')
    markup.add(chat_btn, image_btn, music_btn, help_btn)

    bot.send_message(chat_id=message.chat.id,
                     text="Use these shortcuts for quick access:",
                     reply_markup=markup)

    option(message)


@bot.message_handler(commands=['music'])
def music(message):
    global state
    bot.reply_to(
        message,
        "You can now generate music with this bot. Type your message and press enter to send it"
    )
    state = 3


@bot.message_handler()
def handle_message(message):
    global state
    if state == 1:
        messages = [{"role": "user", "content": message.text}]
        try:
            completion = client.chat.completions.create(
                model="Qwen/Qwen2.5-Coder-32B-Instruct",
                messages=messages,
                max_tokens=500)
            response = completion.choices[0].message.content
            bot.reply_to(message, response)
        except Exception as e:
            bot.reply_to(message, f"An error occurred: {e}")
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
            audio_bytes = query_musicgen(prompt)
            audio_path = "./generated_music.wav"
            with open(audio_path, "wb") as audio_file:
                audio_file.write(audio_bytes)
            with open(audio_path, "rb") as audio_file:
                bot.send_audio(chat_id=message.chat.id,
                               audio=audio_file,
                               caption=message.text)
        except Exception as e:
            bot.send_message(chat_id=message.chat.id,
                             text=f"An error occurred: {e}")
    else:
        bot.reply_to(
            message,
            "Invalid command. Please use /chat, /image, /music, or /option to observe the commands"
        )


# Start polling and handle potential errors
while True:
    try:
        bot.polling(none_stop=True)
    except Exception as e:
        print(f"Error: {e}")
        time.sleep(10)  # Wait for 10 seconds before trying again
