import logging
import asyncio
import json
import os
import yaml

from yad2scrapper import YadScrap
from aiogram import Bot, Dispatcher, executor, types
import time

with open("config.yml", "r") as fin:
    config = yaml.load(fin.read(), Loader=yaml.FullLoader)

API_TOKEN = config['telegram_token']

# Configure logging
logging.basicConfig(level=logging.INFO)

# Initialize bot and dispatcher
bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot)

users = {}


@dp.message_handler(commands=['start', 'help'])
async def send_welcome(message: types.Message):
    """
    This handler will be called when user sends `/start` or `/help` command
    """
    await message.reply(
        """
Hi I'm a Yad2 tracker, I will help You to find your next home 🏠
Please type the following command to to start tracking:
/reg <paste here your url> (withot the "<" and ">")
        """
        )

@dp.message_handler(commands=['hello'])
async def reply_name(message: types.Message):
    """
    This handler will be called when user sends `/start` or `/help` command
    """
    await message.reply(f"Hi {message.text.split('/hello')[1]}")

@dp.message_handler(commands=['reg'])
async def register(message: types.Message):
    global users
    user_id = str(message.from_user.id)

    msg_args = message.text.split('/reg')
    if len(msg_args) < 2:
        await message.reply(f"Hi {message.from_user.username}, please send yad2 url, like this: '/reg url'")
        return
    url = msg_args[1].strip()
    # check if url is valid
    if str(user_id) not in users:
        users[user_id] = {
            "task": None,
            "url": url
        }
    else:
        users[user_id]["task"].cancel()
        users[user_id]["task"] = None
        users[user_id]["url"] = url

    with open('users.json', 'w') as fout:
        fout.write(json.dumps(users, default=lambda o: ''))
    
    users[user_id]["task"] = asyncio.create_task(sender_loop(user_id, url))
    await message.reply(f"Hi {message.from_user.username}", disable_web_page_preview=True)
    logging.info(f'{message.from_user.username} is registered')
    logging.info(f'passed url is {url}')

@dp.message_handler(commands=['unreg'])
async def unregister(message: types.Message):
    global users
    user_id = str(message.from_user.id)
    if user_id in users:
        users[user_id]["task"].cancel()
        users.pop(user_id, None)
    
    with open('users.json', 'w') as fout:
        fout.write(json.dumps(users, default=lambda o: ''))


    logging.info(f'{message.from_user.username} is unregistered')

    await message.reply(f"You successfully unregistered")

async def sender_loop(user_id, url, init=False):
    try:
        loop = asyncio.get_event_loop()
        yadscrap = await loop.run_in_executor(None, YadScrap, url)
    except Exception as e:
        await bot.send_message(user_id, "please send yad2 url, like this: /reg url")
        logging.error(f"exception occurred during yadscrap init {e}")
        return
    if not init:
        await bot.send_message(user_id, "start watching for changes", disable_web_page_preview=True)
    while True:
        print("before sleep")
        start = time.time()
        await asyncio.sleep(600)
        print(f"after sleep {time.time() - start}")
        loop = asyncio.get_event_loop()
        try:
           news = await loop.run_in_executor(None, yadscrap.check_for_news)
        except Exception as e:
            news = None
            logging.error(f'exception occurred during fetching news {e}')

        if news:
            for new in news.values():
                try:
                    message = f"""
{new['reason']}
Address {new['address']}
Price {new['price']}
Area {new['area']}
{new['url']}
"""
                except Exception as e:
                    logging.exception(f"exception ocurred during parsing the message {e}")
                await bot.send_message(user_id, message, disable_web_page_preview=True)
                if new['img']:
                    try:
                        await bot.send_photo(user_id, photo=new['img'])
                    except Exception as e:
                        logging.exception(f"exception during send photo {e}")

@dp.message_handler(commands=['init'])
async def startup(message: types.Message):
    global users
    if os.path.exists('users.json'):
        with open('users.json', 'r') as fin:
            users = json.loads(fin.read())
    for user_id in users:
        users[user_id]["task"] = asyncio.create_task(sender_loop(user_id, users[user_id]['url'], True))
        logging.info(f'user id {user_id}, registered during logging')

if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)
    


