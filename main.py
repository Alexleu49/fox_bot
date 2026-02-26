import telebot
import json
import os
import schedule
import threading
import time
import random
from dotenv import load_dotenv

load_dotenv()

# Команды:
# /store
# /rewards
# /stats
# /my_stats
# /reward
# /pet
# /hug
# /start

# Настройки
pet_delay = 3600  # 1 час 
hug_delay = 7200  # 2 часа 
CHANNEL_ID = '@Fox_stat'
ADMIN_ID = 1382475644
TOKEN = os.getenv('BOT_TOKEN')

DATA_FILE = 'stats.json'
bot = telebot.TeleBot(TOKEN)

def load_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    else:
        return {"global": {"pet":0, "hug":0, "coin":0}, "users": {}}

def save_data(data):
    with open(DATA_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

def check_user(data, user_id):
    if user_id not in data['users']:
        data['users'][user_id] = {"my_pet": 0, "my_hug": 0, "last_pet": 0, "last_hug": 0, "achievement":[]}
        save_data(data)
    return data

@bot.message_handler(commands=['start'], chat_types=['private'])
def send_welcome(message):
    bot.reply_to(message, "Привет, это небольшой бот от небольшого лиси, веселитесь) Фырь-фырь^^")

@bot.message_handler(commands=['pet'], chat_types=['private'])
def pet_handler(message):
    data = load_data()
    user_id = str(message.from_user.id)
    data = check_user(data, user_id)
    
    current_time = time.time()
    last_action = data['users'][user_id].get('last_pet', 0)
    
    if current_time - last_action < pet_delay:
        remaining = int((pet_delay - (current_time - last_action)) // 60)
        bot.reply_to(message, f"Лисик уже заглажен! Попробуй через {remaining} мин. 🦊")
        return

    luck = random.randint(1, 100)
    reward = 10 if luck == 1 else (5 if 2 <= luck <= 6 else (1 if 7 <= luck <= 16 else 0))

    data['global']['pet'] += 1
    data['users'][user_id]['my_pet'] += 1
    data['users'][user_id]['last_pet'] = current_time 
    data['global']['coin'] += reward
    save_data(data)

    response = (f"Ты погладил лисика! Фырь-Фырь^^ \n"
                f"Всего поглаживаний: {data['global']['pet']}\n"
                f"Твоих поглаживаний: {data['users'][user_id]['my_pet']}")
    bot.reply_to(message, response)

@bot.message_handler(commands=['hug'], chat_types=['private'])
def hug_handler(message):
    data = load_data()
    user_id = str(message.from_user.id)
    data = check_user(data, user_id)
    
    current_time = time.time()
    last_action = data['users'][user_id].get('last_hug', 0)
    
    if current_time - last_action < hug_delay:
        remaining = int((hug_delay - (current_time - last_action)) // 60)
        bot.reply_to(message, f"Лисик сейчас не хочет обниматься. Приходи через {remaining // 60} ч. {remaining % 60} мин. 🫂")
        return

    luck = random.randint(1, 100)
    reward = 10 if 1 <= luck <= 3 else (5 if 4 <= luck <= 11 else (1 if 11 <= luck <= 26 else 0))

    data['global']['hug'] += 1
    data['users'][user_id]['my_hug'] += 1
    data['users'][user_id]['last_hug'] = current_time 
    save_data(data)

    response = (f"Ты обнял(-а) лисика! Фырь-Фырь^^ \n"
                f"Всего объятий: {data['global']['hug']}\n"
                f"Твоих объятий: {data['users'][user_id]['my_hug']}")
    bot.reply_to(message, response)

@bot.message_handler(commands=['stats'])
def global_stats(message):
    data = load_data()
    total = data['global']
    text = (f"🦊 Ваш любимый фуррёнок\n\n"
            f"Имя: Алекс\n"
            f"Вид: Лис (поглощение Puro)\n\n"
            f"Погладили: {total['pet']} раз\n"
            f"Обняли: {total['hug']} раз\n\n"
            f"Лисев на общем балансе: {total['coin']} 🦊\n"
            f"Бот: @Fox_stat_bot")
    bot.reply_to(message, text)

@bot.message_handler(commands=['my_stats'])
def local_stats(message):
    data = load_data()
    user_id = str(message.from_user.id)
    data = check_user(data, user_id)
    user_stats = data['users'][user_id]
    
    text = (f"Вы погладили: {user_stats['my_pet']} раз\n"
            f"Вы обняли: {user_stats['my_hug']} раз\n\n"
            f"Лисев на общем балансе: {data['global']['coin']} 🦊\n"
            f"Бот: @Fox_stat_bot")
    bot.reply_to(message, text)

@bot.message_handler(commands=['reward'])
def reward_user(message):
    if message.from_user.id != ADMIN_ID:
        bot.reply_to(message, "Команду может использовать только сам лисик!")
        return
    data = load_data()
    target_id = None
    achievement_text = ""

    if message.reply_to_message:
        target_id = str(message.reply_to_message.from_user.id)
        parts = message.text.split(maxsplit=1)
        achievement_text = parts[1] if len(parts) > 1 else "Особая заслуга"
    else:
        parts = message.text.split(maxsplit=2)
        if len(parts) < 3:
            bot.reply_to(message, "Ответь командой на сообщение или укажи id пользователя")
            return
        target_id = parts[1]
        achievement_text = parts[2]

    data = check_user(data, target_id)
    print('ачивка:', achievement_text)
    data['users'][target_id]['achievement'].append(achievement_text)
    save_data(data)

    bot.reply_to(message, f"Достижение «{achievement_text}» выдано пользователю!")

@bot.message_handler(commands=['rewards'])
def show_rewards(message):
    data = load_data()
    user_id = None
    
    if message.reply_to_message:
        user_id = str(message.reply_to_message.from_user.id)
    else:
        user_id = str(message.from_user.id)
    data = check_user(data, user_id)
    
    rewards = data['users'][user_id].get('achievement', [])
    if not rewards:
        bot.reply_to(message, "У тебя пока нет наград")
    else:
        reward_list = "\n".join([f"{a}" for a in rewards])
        text = f"Достижения:\n\n{reward_list}"
        bot.reply_to(message, text)
    

# Функция для рассылки в канал
def send_daily_stats():
    try:
        data = load_data()
        global_data = data['global']
        text = (f"📊 Ежедневная статистика Алекса:\n\n"
                f"🦊 Общих поглаживаний: {global_data['pet']}\n"
                f"🫂 Общих объятий: {global_data['hug']}\n"
                f"💰 Лисев на общем балансе: {global_data['coin']} 🦊")
        bot.send_message(CHANNEL_ID, text)
    except Exception as e:
        print(f"Ошибка при рассылке: {e}")

def run_scheduler():
    schedule.every().day.at("15:00").do(send_daily_stats)
    while True:
        schedule.run_pending()
        time.sleep(15)

threading.Thread(target=run_scheduler, daemon=True).start()

print("Бот запущен...")
bot.infinity_polling()
