from bot_resources import *
import traceback
import geopy
import commands.main_menu as main_menu
import backend.search_partner as search_partner
from math import pi, cos, sin

locations = {}
max_rows_select_search_range = int(config['Find partner']['max_rows_select_search_range'])
max_rows_select_age = int(config['Find partner']['max_rows_select_age'])


def find_partner_start(user_id: int):
    bot.send_message(user_id, language['Find partner']['suggestion_find_partner'],
                     reply_markup=location_suggestion_keyboard)
    db['users'].update_one({'_id': user_id}, {'$set': {
        'current_position': 'find_partner_location'
    }})
    bot.register_next_step_handler_by_chat_id(user_id, find_partner_location)


def find_partner_location(message: tb.types.Message):
    if message.content_type == 'location':
        try:
            location = geolocator.reverse(f'{message.location.latitude}, {message.location.longitude}')
            bot.send_message(message.from_user.id, language['Find partner']['suggestion_location']
                             .replace('&&', location.address), reply_markup=confirmation_location)
            locations[message.from_user.id] = {
                'latitude': location.latitude,
                'longitude': location.longitude,
                'latitude_cos': cos(location.latitude * pi / 180.0),
                'latitude_sin': sin(location.latitude * pi / 180.0),
                'longitude_rad': location.longitude * pi / 180.0
            }
        except Exception as e:
            logging.error(f'find_partner_location - {traceback.format_exc()}')
            bot.send_message(message.from_user.id, language['Find partner']['error'],
                             reply_markup=ReplyKeyboardRemove)
            bot.send_message(message.from_user.id, language['Find partner']['repeat_suggestion_find_partner'],
                             reply_markup=location_suggestion_keyboard)
            bot.register_next_step_handler_by_chat_id(message.from_user.id, find_partner_location)
    elif message.content_type == 'text':
        try:
            location: geopy.location.Location = geolocator.geocode(message.text)
            bot.send_location(message.from_user.id, location.latitude, location.longitude,
                              reply_markup=ReplyKeyboardRemove)
            bot.send_message(message.from_user.id, language['Find partner']['suggestion_location']
                             .replace('&&', location.address), reply_markup=confirmation_location)
            locations[message.from_user.id] = {
                'latitude': location.latitude,
                'longitude': location.longitude,
                'latitude_cos': cos(location.latitude * pi / 180.0),
                'latitude_sin': sin(location.latitude * pi / 180.0),
                'longitude_rad': location.longitude * pi / 180.0
            }
        except Exception as e:
            logging.error(f'find_partner_location - {traceback.format_exc()}')
            bot.send_message(message.from_user.id, language['Find partner']['error'],
                             reply_markup=ReplyKeyboardRemove)
            bot.send_message(message.from_user.id, language['Find partner']['repeat_suggestion_find_partner'],
                             reply_markup=location_suggestion_keyboard)
            bot.register_next_step_handler_by_chat_id(message.from_user.id, find_partner_location)
    else:
        bot.send_message(message.from_user.id, language['Find partner']['repeat_suggestion_find_partner'],
                         reply_markup=location_suggestion_keyboard)
        bot.register_next_step_handler_by_chat_id(message.from_user.id, find_partner_location)


@bot.callback_query_handler(func=lambda call: call.data == "confirmation_location//no")
def wrong_confirmation_location(call: tb.types.CallbackQuery):
    """Пользователь ответил, что не утверждает отмену регистрации"""
    bot.edit_message_reply_markup(call.message.chat.id, call.message.id)
    bot.send_message(call.message.chat.id, language['Find partner']['suggestion_find_partner'],
                     reply_markup=location_suggestion_keyboard)
    bot.register_next_step_handler_by_chat_id(call.message.chat.id, find_partner_location)


@bot.callback_query_handler(func=lambda call: call.data == "confirmation_location//yes")
def applied_confirmation_location(call: tb.types.CallbackQuery):
    """Пользователь утвердил отмену регистрации """
    bot.edit_message_reply_markup(call.message.chat.id, call.message.id)
    suggestion_search_range(call.from_user.id)


def suggestion_search_range(user_id: int):
    bot.send_message(user_id, language['Find partner']['suggestion_search_range'],
                     reply_markup=select_search_range['first'])


@bot.callback_query_handler(func=lambda call: call.data[0:19] == "select_search_range")
def apply_search_range(call: tb.types.CallbackQuery):
    """Утверждение радиуса поиска"""
    data = call.data.split('//')
    if data[1] != data[2]:
        bot.edit_message_text(language['Find partner']['suggestion_search_range'] + '\n' +
                              language['Find partner']['confirmation_search_range']
                              .replace('&&', language['Search ranges'][data[2]]),
                              call.message.chat.id, call.message.id, reply_markup=select_search_range[data[2]])
    else:
        bot.edit_message_text(language['Find partner']['selected_search_range']
                              .replace('&&', language['Search ranges'][data[2]]), call.message.chat.id, call.message.id)
        try:
            locations[call.from_user.id]['range'] = float(data[2])
            suggestion_age(call.from_user.id)
        except Exception as e:
            bot.send_message(call.from_user.id, language['Find partner']['error'],
                             reply_markup=ReplyKeyboardRemove)
            logging.error(f'apply_search_range - {traceback.format_exc()}')
            find_partner_start(call.from_user.id)


def suggestion_age(user_id: int):
    bot.send_message(user_id, language['Find partner']['suggestion_age'],
                     reply_markup=select_age['first'])


@bot.callback_query_handler(func=lambda call: call.data[0:10] == "select_age")
def apply_age(call: tb.types.CallbackQuery):
    """Утверждение радиуса поиска"""
    data = call.data.split('//')
    if data[1] != data[2]:
        bot.edit_message_text(language['Find partner']['suggestion_age'] + '\n' +
                              language['Find partner']['confirmation_age']
                              .replace('&&', language['Search ranges'][data[2]]),
                              call.message.chat.id, call.message.id, reply_markup=select_age[data[2]])
    else:
        bot.edit_message_text(language['Find partner']['selected_age']
                              .replace('&&', language['Search ranges'][data[2]]), call.message.chat.id, call.message.id)
        try:
            location = locations[call.from_user.id]
            location['age'] = float(data[2])
            del locations[call.from_user.id]
            # db['users'].update_one({'_id': call.from_user.id}, {'$push': {
            #     'locations': location
            # }})
            db['users'].update_one({'_id': call.from_user.id}, {'$set': {
                'locations': [location]
            }})
            # db['users'].update_one({'_id': call.from_user.id}, {'$set': location})
            start_search(call.from_user.id)
        except Exception as e:
            bot.send_message(call.from_user.id, language['Find partner']['error'],
                             reply_markup=ReplyKeyboardRemove)
            logging.error(f'apply_age - {traceback.format_exc()}')
            find_partner_start(call.from_user.id)


def start_search(user_id: int):
    bot.send_message(user_id, language['Find partner']['start_search'])
    search_partner.search(user_id)
    main_menu.main_menu_cycle(user_id)


confirmation_location = tb.types.InlineKeyboardMarkup(
    [
        [
            tb.types.InlineKeyboardButton(text=language['Find partner']['yes'],
                                          callback_data='confirmation_location//yes'),
            tb.types.InlineKeyboardButton(text=language['Find partner']['no'],
                                          callback_data='confirmation_location//no')
        ]
    ])
select_search_range = {
    key: tb.types.InlineKeyboardMarkup([
        list(map(lambda x:
                 tb.types.InlineKeyboardButton(text=language['Find partner']['selected'] + language['Search ranges'][x],
                                               callback_data=f'select_search_range//{key}//{x}')
                 if key == x else
                 tb.types.InlineKeyboardButton(text=language['Search ranges'][x],
                                               callback_data=f'select_search_range//{key}//{x}'),
                 list(dict(language['Search ranges']).keys())[i: i + max_rows_select_search_range]))
        for i in range(0, len(language['Search ranges']), max_rows_select_search_range)
    ])
    for key in dict(language['Search ranges'])
}
select_search_range['first'] = tb.types.InlineKeyboardMarkup([
    list(map(lambda x:
             tb.types.InlineKeyboardButton(text=language['Search ranges'][x],
                                           callback_data=f'select_search_range//first//{x}'),
             list(dict(language['Search ranges']).keys())[i: i + max_rows_select_search_range]))
    for i in range(0, len(language['Search ranges']), max_rows_select_search_range)
])
select_age = {
    key: tb.types.InlineKeyboardMarkup([
        list(map(lambda x:
                 tb.types.InlineKeyboardButton(
                     text=language['Find partner']['selected'] + language['Age suggestion'][x],
                     callback_data=f'select_age//{key}//{x}')
                 if key == x else
                 tb.types.InlineKeyboardButton(text=language['Age suggestion'][x],
                                               callback_data=f'select_age//{key}//{x}'),
                 list(dict(language['Age suggestion']).keys())[i: i + max_rows_select_age]))
        for i in range(0, len(language['Age suggestion']), max_rows_select_age)
    ])
    for key in dict(language['Age suggestion'])
}
select_age['first'] = tb.types.InlineKeyboardMarkup([
    list(map(lambda x:
             tb.types.InlineKeyboardButton(text=language['Age suggestion'][x],
                                           callback_data=f'select_age//first//{x}'),
             list(dict(language['Age suggestion']).keys())[i: i + max_rows_select_age]))
    for i in range(0, len(language['Age suggestion']), max_rows_select_age)
])

location_suggestion_keyboard = tb.types.ReplyKeyboardMarkup(one_time_keyboard=True)
location_suggestion_keyboard.row(
    tb.types.KeyboardButton(language['Find partner']['location_suggestion'], request_location=True),
)
