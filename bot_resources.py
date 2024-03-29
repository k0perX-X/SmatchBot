import telebot as tb
import configparser
import pymongo as pm
import logging
from geopy.geocoders import Nominatim

geolocator = Nominatim(user_agent="SmatchBot")

logging.basicConfig(filename="logs/logging.log", level=logging.INFO)

language = configparser.ConfigParser()
language.read("resources/language.ini", encoding="utf8")
config = configparser.ConfigParser()
config.read("resources/settings.ini")

bot = tb.TeleBot(config["Telegram"]['token'], parse_mode='MARKDOWN')

client = pm.MongoClient(config["MongoDB"]['server'], int(config["MongoDB"]['port']))
db = client[config['MongoDB']['db']]

ReplyKeyboardRemove = tb.types.ReplyKeyboardRemove(selective=False)

print('Bot loaded')
