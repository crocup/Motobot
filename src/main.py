import hashlib
import json
import logging
import os
import configparser
from peewee import DoesNotExist
from src.model import Bike, database
import requests
from telegram import (ReplyKeyboardRemove)
from telegram.ext import (Updater, CommandHandler, MessageHandler, Filters,
                          ConversationHandler)
from bs4 import BeautifulSoup


# Инициализация БД
class DatabaseBike:
    def __init__(self):
        database.init(os.path.normpath(os.path.join(os.path.dirname(__file__), 'Bike_db.sqlite')))


logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)
logger = logging.getLogger(__name__)
MOTO, MOTOR, LINK = range(3)
# Чтение конфиг-файлов
with open(os.path.normpath(os.path.join(os.path.dirname(__file__), 'brand_av.json')), "r") as read_file:
    data = json.load(read_file)
config = configparser.ConfigParser()
config.read(os.path.normpath(os.path.join(os.path.dirname(__file__), 'config.ini')))


def start(update, context):
    """ Запуск бота """
    update.message.reply_text(
        'Привет! Я помогу найти тебе мотоцикл на сайте moto.av.by '
        'Ответь на вопросы и я найду подходящие объявления.'
        'Если хочешь меня остановить, отправь /cancel \n\n'
        'Напиши какую модель ты хочешь? (Например: Honda CB)')
    return MOTO


def motor(update, context):
    """ Установка параметров (модели мотоцикла) """
    global model_dict
    model_dict = {}
    user = update.message.from_user
    model_dict['user'] = user['id']
    model = str(update.message.text).lower().split()
    model_dict['user_brand'] = model[0]
    model_dict['user_model'] = model[1]
    update.message.reply_text("Теперь какой обьем мотоцикла хочешь?")
    return MOTOR


def search_m(update, context):
    """ Установка параметров (обьем мотоцикла) """
    user = update.message.from_user
    choose = str(update.message.text)
    if not choose.isdigit():
        update.message.reply_text("Извини, не могу понять тебя. Попробуй еще раз")
        return MOTOR
    model_dict['user_motor'] = str(update.message.text)
    update.message.reply_text("Отлично! Нажми /save и motobot будет искать объявления!")
    return LINK


def check_update(context):
    """ Отправка обьявлений в бот """
    volume_from = int(model_dict['user_motor']) - 10
    volume_to = int(model_dict['user_motor']) + 10
    href_link_av = f"https://moto.av.by/bike?brand_id={data['brand'][model_dict['user_brand']]}&model_id={data[model_dict['user_brand']][model_dict['user_model']]}" \
                   f"&currency=USD&engine_volume_from={str(volume_from)}&engine_volume_to={str(volume_to)}"
    lnk = parsing_av(link=href_link_av)
    lnk_array = list(set(lnk))
    for i in lnk_array:
        context.bot.send_message(chat_id=context.job.context, text=i)


def parsing_av(link):
    """ Поиск новых обьявлений и добавление в БД"""
    href_moto = []
    r = requests.get(link)
    soup = BeautifulSoup(r.text, "lxml").find('div', class_='listing')
    listing_item_main = soup.find_all('div', class_='listing-item-wrap')
    for i in listing_item_main:
        hr = i.find('a', href=True)
        price = i.find('small').text
        find_company = str(hr['href']).find("company")
        if find_company != -1:
            continue
        else:
            hash_user = hashlib.md5(str(model_dict['user']).encode())
            str_hash = f"link:{hr['href']} price:{price}"
            hash_link = hashlib.md5(str_hash.encode())
            try:
                Bike.get(Bike.link_hash == hash_link.hexdigest())
            except DoesNotExist:
                Bike.create(user_uid=hash_user.hexdigest(),
                            name_bike=model_dict['user_brand'],
                            link_bike=hr['href'],
                            link_hash=hash_link.hexdigest())
                href_moto.append(hr['href'])
    return href_moto


def cancel(update, context):
    """ Остановка бота """
    job = context.chat_data['job']
    job.schedule_removal()
    del context.chat_data['job']
    update.message.reply_text('Хорошего дня!',
                              reply_markup=ReplyKeyboardRemove())
    return ConversationHandler.END


def set_timer(update, context):
    """ Установка таймера для переодической проверки обьявлений (каждые 60 сек.) """
    chat_id = update.message.chat_id
    try:
        new_job = context.job_queue.run_repeating(check_update, 60, first=0, context=chat_id)
        context.chat_data['job'] = new_job
    except (IndexError, ValueError) as e:
        logger.error(e)


def main():
    updater = Updater(config["Telegram"]["TOKEN"], use_context=True)
    dp = updater.dispatcher
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start)],
        states={
            MOTO: [MessageHandler(Filters.text & ~Filters.command, motor)],
            MOTOR: [MessageHandler(Filters.text & ~Filters.command, search_m)],
            LINK: [CommandHandler('save', set_timer)],
        },
        fallbacks=[CommandHandler('cancel', cancel)]
    )
    dp.add_handler(conv_handler)
    updater.start_polling()
    updater.idle()
    database.close()


if __name__ == '__main__':
    try:
        main()
    except Exception as e:
        logger.error(e)
        exit(0)
