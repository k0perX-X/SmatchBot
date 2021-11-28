import telebot as tb
import configparser
import pymongo as pm
import logging

logging.basicConfig(filename="sample.log", level=logging.INFO)

language = configparser.ConfigParser()
language.read("resources/language.ini", encoding="utf8")
config = configparser.ConfigParser()
config.read("resources/settings.ini")

bot = tb.TeleBot(config["Telegram"]['token'], parse_mode='MARKDOWN')
client = pm.MongoClient(config["MongoDB"]['server'], int(config["MongoDB"]['port']))
db = client[config['MongoDB']['db']]
