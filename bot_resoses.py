import telebot as tb
import configparser
import pymongo as pm

language = configparser.ConfigParser()
language.read("language.ini", encoding="utf8")
config = configparser.ConfigParser()
config.read("settings.ini")

bot = tb.TeleBot(config["Telegram"]['token'], parse_mode='MARKDOWN')
client = pm.MongoClient(config["MongoDB"]['server'], int(config["MongoDB"]['port']))
db = client[config['MongoDB']['db']]
