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


class DatabaseUser:
    def __init__(self):
        database.init(os.path.normpath(os.path.join(os.path.dirname(__file__), 'Bike_db.sqlite')))


# Enable logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)

logger = logging.getLogger(__name__)

MOTO, MOTOR, LINK = range(3)

with open(os.path.normpath(os.path.join(os.path.dirname(__file__), 'brand_av.json')), "r") as read_file:
    data = json.load(read_file)
config = configparser.ConfigParser()
config.read(os.path.normpath(os.path.join(os.path.dirname(__file__), 'config.ini')))


def start(update, context):
    """

    :param update:
    :param context:
    :return:
    """
    update.message.reply_text(
        'Привет! Я помогу найти тебе мотоцикл в РБ. '
        'Ответь на вопросы и я найду подходящие объявления.'
        'Если хочешь меня остановить, отправь /cancel \n\n'
        'Напиши какую модель ты хочешь? (Например: Honda CB)')
    return MOTO


def motor(update, context):
    """

    :param update:
    :param context:
    :return:
    """
    global model_dict
    model_dict = {}
    user = update.message.from_user
    model_dict['user'] = user['id']
    model = str(update.message.text).lower().split()
    model_dict['user_brand'] = model[0]
    model_dict['user_model'] = model[1]
    update.message.reply_text("Теперь напиши какой обьем мотоцикла хочешь?")
    return MOTOR


def search_m(update, context):
    """

    :param update:
    :param context:
    :return:
    """
    user = update.message.from_user
    model_dict['user_motor'] = str(update.message.text)
    update.message.reply_text("Отлично! Чтобы проверить объявления, нажми /search")
    return LINK


def check_update(update, context):
    href_link_av = f"https://moto.av.by/bike?brand_id={data['brand'][model_dict['user_brand']]}&model_id={data[model_dict['user_brand']][model_dict['user_model']]}" \
                   f"&currency=USD&engine_volume_from={model_dict['user_motor']}&engine_volume_to={model_dict['user_motor']}"
    lnk = parsing_av(link=href_link_av)
    lnk_array = list(set(lnk))
    for i in lnk_array:
        update.message.reply_text(i)


def parsing_av(link):
    """

    :param link:
    :return:
    """
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
                href_moto.append("Новых объявлений нет")
            except DoesNotExist:
                Bike.create(user_uid=hash_user.hexdigest(),
                            name_bike=model_dict['user_brand'],
                            link_bike=hr['href'],
                            link_hash=hash_link.hexdigest())
                href_moto.append(hr['href'])
    return href_moto


def cancel(update, context):
    """

    :param update:
    :param context:
    :return:
    """
    user = update.message.from_user
    update.message.reply_text('Хорошего дня!',
                              reply_markup=ReplyKeyboardRemove())
    return ConversationHandler.END


def main():
    """

    :return:
    """
    updater = Updater(config["Telegram"]["TOKEN"], use_context=True)
    dp = updater.dispatcher
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start)],
        states={
            MOTO: [MessageHandler(Filters.text & ~Filters.command, motor)],
            MOTOR: [MessageHandler(Filters.text & ~Filters.command, search_m)],
            LINK: [CommandHandler('search', check_update)],
        },
        fallbacks=[CommandHandler('cancel', cancel)]
    )
    dp.add_handler(conv_handler)
    # Start the Bot
    updater.start_polling()
    updater.idle()
    database.close()


if __name__ == '__main__':
    try:
        main()
    except Exception as e:
        logger.error(e)
        exit(0)
