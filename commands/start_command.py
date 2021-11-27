from bot_resoses import *


@bot.message_handler(commands=['start'])
def start_command(message):

    if len(db['users'].find({"_id": message.from_user.id})) == 1:
        # если у человек зарегистрирован в боте спрашиваем разрешение на сброс
        bot.send_message(message.from_user.id, language['Russian']['start_message'],
                         reply_markup=tb.types.InlineKeyboardMarkup())
    else:
        start_cycle(message)
    return True


def start_cycle(message):
    # todo
    bot.send_message(message.from_user.id, language['Russian']['start_message'])
    db['users'].insert_one({
        "_id": message.from_user.id,

    })
