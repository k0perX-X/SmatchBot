from bot_resoses import *

consent_to_reset_keyboard = None
consent_to_policy = None
consent_name = None


@bot.message_handler(commands=['start'])
def start_command(message):
    """Функция команды start"""
    if len([r for r in db['users'].find({"_id": message.from_user.id})]) == 1:
        # если у человек зарегистрирован в боте спрашиваем разрешение на сброс
        bot.send_message(message.from_user.id, language['Start']['restart'],
                         reply_markup=consent_to_reset_keyboard)
    else:
        start_cycle(message.from_user.id)


@bot.callback_query_handler(func=lambda call: call.data == "consent_to_reset_keyboard//yes")
def callback_worker(call):
    """если разрешил сброс"""
    bot.edit_message_reply_markup(call.message.chat.id, call.message.id)
    start_cycle(call.from_user.id)


@bot.callback_query_handler(func=lambda call: call.data == "consent_to_reset_keyboard//no")
def callback_worker(call):
    """если запретил сброс"""
    bot.edit_message_reply_markup(call.message.chat.id, call.message.id)
    start_cycle(call.from_user.id)


def start_cycle(id):
    """Запуск цикла функции start"""
    bot.send_message(id, language['Start']['message'])
    bot.send_message(id, language['Start']['policy'], reply_markup=consent_to_policy)


@bot.callback_query_handler(func=lambda call: call.data == "consent_to_policy//yes")
def callback_worker(call):
    """если согласен с политикой"""
    bot.edit_message_reply_markup(call.message.chat.id, call.message.id)
    bot.send_message(call.from_user.id, language['Start']['get_name'])
    bot.register_next_step_handler_by_chat_id(call.from_user.id, get_name)
    if len([r for r in db['users'].find({"_id": call.from_user.id})]) == 0:
        db['users'].insert_one({
            "_id": call.from_user.id
        })


def get_name(message):
    """Уточнение правильности имени"""
    bot.send_message(message.from_user.id, language['Start']['consent_get_name'][0:-1] +
                     message.text + language['Start']['consent_get_name'][-1], reply_markup=consent_name)


@bot.callback_query_handler(func=lambda call: call.data == "consent_name//no")
def callback_worker(call):
    """имя не верное"""
    bot.edit_message_reply_markup(call.message.chat.id, call.message.id)
    bot.send_message(call.from_user.id, language['Start']['repeat_get_name'])
    bot.register_next_step_handler_by_chat_id(call.from_user.id, get_name)


@bot.callback_query_handler(func=lambda call: call.data == "consent_name//yes")
def callback_worker(call):
    """имя верное"""
    bot.edit_message_reply_markup(call.message.chat.id, call.message.id)
    # todo


def keyboards_declaration():
    global consent_to_reset_keyboard
    global consent_to_policy
    global consent_name
    consent_to_reset_keyboard = tb.types.InlineKeyboardMarkup(
        [
            [
                tb.types.InlineKeyboardButton(text=language['Start']['yes'],
                                              callback_data='consent_to_reset_keyboard//yes'),
                tb.types.InlineKeyboardButton(text=language['Start']['no'],
                                              callback_data='consent_to_reset_keyboard//no')
            ]
        ])
    consent_to_policy = tb.types.InlineKeyboardMarkup(
        [
            [
                tb.types.InlineKeyboardButton(text=language['Start']['policy_yes'],
                                              callback_data='consent_to_policy//yes')
            ]
        ])
    consent_name = tb.types.InlineKeyboardMarkup(
        [
            [
                tb.types.InlineKeyboardButton(text=language['Start']['yes'],
                                              callback_data='consent_name//yes'),
                tb.types.InlineKeyboardButton(text=language['Start']['no'],
                                              callback_data='consent_name//no')
            ]
        ])


keyboards_declaration()
