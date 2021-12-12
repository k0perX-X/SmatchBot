from bot_resources import *
from spellchecker import SpellChecker
import datetime
from typing import Any, Callable, List, Optional, Union
import commands.main_menu as main_menu

months_checker = SpellChecker(local_dictionary="resources/empty.json", distance=4)
months_checker.word_frequency.load_text_file("resources/months.ini")
months_name = {'январь': 1, 'февраль': 2, 'март': 3, 'апрель': 4, 'май': 5, 'июнь': 6, 'июль': 7, 'август': 8,
               'сентябрь': 9, 'октябрь': 10, 'ноябрь': 11, 'декабрь': 12}
months_number = {1: 'Января', 2: 'Февраля', 3: 'Марта', 4: 'Апреля', 5: 'Мая', 6: 'Июня', 7: 'Июля', 8: 'Августа',
                 9: 'Сентября', 10: 'Октября', 11: 'Ноября', 12: 'Декабря'}

selected_sports = {}
kinds_of_sports = [i for i in language['Sports']]
selected_sports_professionalism = {}

about_user_decs_list = {}


# todo если не закончил регистрацию запрос через время на продолжение


@bot.message_handler(func= lambda message: message.text[0:6] == '/start')
def start_command(message: tb.types.Message):
    """Функция команды start"""
    user = db['users'].find_one({"_id": message.from_user.id})
    if user is not None:
        # если у человек зарегистрирован в боте спрашиваем разрешение на сброс
        bot.send_message(message.from_user.id, language['Start']['restart_alert'],
                         reply_markup=ReplyKeyboardRemove)
        bot.send_message(message.from_user.id, language['Start']['restart'],
                         reply_markup=consent_to_reset_keyboard)
    else:
        start_cycle(message.from_user.id)


@bot.callback_query_handler(func=lambda call: call.data == "consent_to_reset_keyboard//no")
def reset_canceled(call: tb.types.CallbackQuery):
    """Если запретил сброс"""
    bot.edit_message_reply_markup(call.message.chat.id, call.message.id)
    main_menu.main_menu_cycle(call.from_user.id)


@bot.callback_query_handler(func=lambda call: call.data == "consent_to_reset_keyboard//yes")
def reset_applied(call: tb.types.CallbackQuery):
    """Если разрешил сброс"""
    bot.edit_message_reply_markup(call.message.chat.id, call.message.id)
    db['users'].delete_one({'_id': call.from_user.id})
    start_cycle(call.from_user.id)


def start_cycle(from_user_id):
    """Запуск цикла функции start"""
    bot.send_message(from_user_id, language['Start']['message'], reply_markup=ReplyKeyboardRemove)
    bot.send_message(from_user_id, language['Start']['policy'], reply_markup=consent_to_policy,
                     disable_web_page_preview=True)


@bot.callback_query_handler(func=lambda call: call.data == "consent_to_policy//yes")
def policy_applied(call: tb.types.CallbackQuery):
    """Если согласен с политикой"""
    bot.edit_message_reply_markup(call.message.chat.id, call.message.id)
    start_start(call.from_user.id)


def start_start(user_id: int):
    """Запуск настройки регистрации"""
    bot.send_message(user_id, language['Start']['get_name'], reply_markup=ReplyKeyboardRemove)
    bot.register_next_step_handler_by_chat_id(user_id, get_name)
    try:
        db['registration'].insert_one({
            "_id": user_id,
            "time_of_start_registration": datetime.datetime.now()
        })
    except pm.errors.DuplicateKeyError:
        db['registration'].update_one({'_id': user_id}, {'$set': {
            "time_of_start_registration": datetime.datetime.now()
        }})


def get_name(message: tb.types.Message):
    """Уточнение правильности имени"""
    bot.send_message(message.from_user.id, language['Start']['consent_get_name'].replace('&&', message.text),
                     reply_markup=consent_name)
    db['registration'].update_one({'_id': message.from_user.id}, {'$set': {
        'name': message.text
    }})


@bot.callback_query_handler(func=lambda call: call.data == "consent_name//no")
def wrong_name(call: tb.types.CallbackQuery):
    """Имя не верное"""
    bot.edit_message_reply_markup(call.message.chat.id, call.message.id)
    bot.send_message(call.from_user.id, language['Start']['repeat_get_name'])
    bot.register_next_step_handler_by_chat_id(call.from_user.id, get_name)


@bot.callback_query_handler(func=lambda call: call.data == "consent_name//yes")
def correct_name(call: tb.types.CallbackQuery):
    """Имя верное"""
    bot.edit_message_reply_markup(call.message.chat.id, call.message.id)
    bot.send_message(call.from_user.id, language['Start']['get_date_of_birth'])
    bot.register_next_step_handler_by_chat_id(call.from_user.id, get_date_of_birth)


def get_date_of_birth(message: tb.types.Message):
    """Уточнение правильности даты"""
    split_text = sum(map(lambda x: x.split('.'), message.text.split()), [])
    if len(split_text) < 3:
        wrong_date_of_birth_program(message)
        return
    # день
    if split_text[0].isnumeric():
        day = int(split_text[0])
    else:
        wrong_date_of_birth_program(message)
        return
    # месяц
    month = months_checker.correction(split_text[1].lower())
    if month.isnumeric():
        month = int(month)
    elif month in months_name.keys():
        month = months_name[month]
    else:
        wrong_date_of_birth_program(message)
        return
    # год
    if split_text[2].isnumeric():
        year = int(split_text[2])
    else:
        wrong_date_of_birth_program(message)
        return
    try:
        date_of_birth = datetime.date(year, month, day)
    except ValueError:
        wrong_date_of_birth_program(message)
        return
    # проверка на 16 лет
    today = datetime.date.today()
    if date_of_birth > datetime.date(today.year - 16, today.month, today.day):
        wrong_date_of_birth_program_18(message)
        return
    # && - день ^^ - месяц &^ - год
    # Утверждение пользователем
    bot.send_message(message.from_user.id, language['Start']['consent_date_of_birth']
                     .replace('&&', str(date_of_birth.day))
                     .replace('^^', months_number[date_of_birth.month])
                     .replace('&^', str(date_of_birth.year)),
                     reply_markup=consent_date_of_birth)
    db['registration'].update_one({'_id': message.from_user.id}, {'$set': {
        'date_of_birth': datetime.datetime.combine(date_of_birth, datetime.datetime.min.time())
    }})


def wrong_date_of_birth_program(message: tb.types.Message):
    """Дата рождения не распознана"""
    bot.send_message(message.from_user.id, language['Start']['repeat_program_get_date_of_birth'])
    bot.register_next_step_handler_by_chat_id(message.from_user.id, get_date_of_birth)


def wrong_date_of_birth_program_18(message: tb.types.Message):
    """Распознана дата, но пользователю нет 16 лет"""
    bot.send_message(message.from_user.id, language['Start']['repeat_16_get_date_of_birth'])
    bot.register_next_step_handler_by_chat_id(message.from_user.id, get_date_of_birth)


@bot.callback_query_handler(func=lambda call: call.data == "consent_date_of_birth//no")
def wrong_date_of_birth_call(call: tb.types.CallbackQuery):
    """Пользователь ответил, что распознано неверно"""
    bot.edit_message_reply_markup(call.message.chat.id, call.message.id)
    bot.send_message(call.from_user.id, language['Start']['repeat_get_date_of_birth'])
    bot.register_next_step_handler_by_chat_id(call.from_user.id, get_date_of_birth)


@bot.callback_query_handler(func=lambda call: call.data == "consent_date_of_birth//yes")
def applied_date_of_birth(call: tb.types.CallbackQuery):
    """Пользователь утвердил дату рождения"""
    bot.edit_message_reply_markup(call.message.chat.id, call.message.id)
    bot.send_message(call.from_user.id, language['Start']['select_sex'],
                     reply_markup=select_sex)


@bot.callback_query_handler(func=lambda call: call.data[0:10] == "select_sex")
def consent_sex_func(call: tb.types.CallbackQuery):
    """Запрос на утверждение пола"""
    bot.edit_message_text(language['Start']['select_sex'] + '\n' +
                          language['Start']['consent_sex'].replace('&&', language['Start'][call.data[12:]]),
                          call.message.chat.id, call.message.id, reply_markup=consent_sex[call.data[12:]])


@bot.callback_query_handler(func=lambda call: call.data[0:11] == "consent_sex")
def apply_sex(call: tb.types.CallbackQuery):
    """Утверждение пола"""
    data = call.data.split('//')
    if data[1] != data[2]:
        bot.edit_message_text(language['Start']['select_sex'] + '\n' +
                              language['Start']['consent_sex'].replace('&&', language['Start'][data[2]]),
                              call.message.chat.id, call.message.id, reply_markup=consent_sex[data[2]])
    else:
        bot.edit_message_text(language['Start']['selected_sex'].replace('&&', language['Start'][data[2]]),
                              call.message.chat.id, call.message.id)
        db['registration'].update_one({'_id': call.from_user.id}, {'$set': {
            'sex': data[1]
        }})
        bot.send_message(call.from_user.id, language['Start']['sport_select'],
                         reply_markup=sport_keyboard(call.from_user.id))


def sport_keyboard(from_user_id: int) -> tb.types.InlineKeyboardMarkup:
    """Создание клавиатуры для выбора спорта"""
    if from_user_id not in selected_sports:
        selected_sports[from_user_id] = {}
        selected_sports[from_user_id]['page'] = 0
        selected_sports[from_user_id]['sports'] = []
        selected_sports[from_user_id]['other'] = []
    user = selected_sports[from_user_id]
    rows = int(config['Sports']['number_of_sports_row'])
    columns = int(config['Sports']['number_of_sports_columns'])
    mas = []
    for i in range(rows):
        if (rows * columns * user['page'] + i * columns) < len(kinds_of_sports):
            mas.append([])
            for j in range(columns):
                if (rows * columns * user['page'] + i * columns + j) < len(kinds_of_sports):
                    sport = kinds_of_sports[rows * columns * user['page'] + j * i * user['page'] + i * columns + j]
                    if sport not in user['sports']:
                        mas[i].append(tb.types.InlineKeyboardButton(
                            text=language['Sports'][sport],
                            callback_data=f"sports_keyboard//{sport}"))
                    else:
                        mas[i].append(tb.types.InlineKeyboardButton(
                            text=language['Start']['selected'] + language['Sports'][sport][1:],
                            callback_data=f"sports_keyboard//{sport}"))
                else:
                    break
        else:
            break
    if user['page'] == 0:
        mas.append([tb.types.InlineKeyboardButton(text=language['Start']['right'],
                                                  callback_data='sports_keyboard//right')])
    elif rows * columns * (user['page'] + 1) > len(kinds_of_sports) - 1:
        mas.append([tb.types.InlineKeyboardButton(text=language['Start']['left'],
                                                  callback_data='sports_keyboard//left')])
    else:
        mas.append([tb.types.InlineKeyboardButton(text=language['Start']['left'],
                                                  callback_data='sports_keyboard//left'),
                    tb.types.InlineKeyboardButton(text=language['Start']['right'],
                                                  callback_data='sports_keyboard//right')])
    mas.append([tb.types.InlineKeyboardButton(text=language['Start']['sport_apply'],
                                              callback_data='sports_keyboard//apply')])
    return tb.types.InlineKeyboardMarkup(mas)


@bot.callback_query_handler(func=lambda call: call.data[0:15] == "sports_keyboard")
def chose_sport(call: Optional[tb.types.CallbackQuery] = None):
    """Выбор спорта"""
    if call.from_user.id in selected_sports and call.data[0:15] == "sports_keyboard":
        sport = call.data[17:]
        match sport:
            case 'left':
                if selected_sports[call.from_user.id]['page'] > 0:
                    selected_sports[call.from_user.id]['page'] -= 1
                bot.edit_message_text(language['Start']['sport_select'], call.message.chat.id, call.message.id,
                                      reply_markup=sport_keyboard(call.from_user.id))
            case 'right':
                selected_sports[call.from_user.id]['page'] += 1
                bot.edit_message_text(language['Start']['sport_select'], call.message.chat.id, call.message.id,
                                      reply_markup=sport_keyboard(call.from_user.id))
            case 'other':
                other_sports(call)
            case 'apply':
                if len(selected_sports[call.from_user.id]['sports']) + \
                        len(selected_sports[call.from_user.id]['sports']) > 0:
                    applied_kinds_of_sports(call)
                else:
                    bot.send_message(call.from_user.id, language['Start']['sport_apply_on_null_sports'])
            case _:
                if sport not in selected_sports[call.from_user.id]['sports']:
                    selected_sports[call.from_user.id]['sports'].append(sport)
                else:
                    selected_sports[call.from_user.id]['sports'].remove(sport)
                bot.edit_message_text(language['Start']['sport_select'], call.message.chat.id, call.message.id,
                                      reply_markup=sport_keyboard(call.from_user.id))
    else:
        bot.edit_message_text(language['Start']['sport_select'], call.message.chat.id, call.message.id,
                              reply_markup=sport_keyboard(call.from_user.id))


def other_sports(call: tb.types.CallbackQuery):
    """Обработка других видов спорта"""
    bot.edit_message_reply_markup(call.message.chat.id, call.message.id)
    if call.from_user.id not in selected_sports:
        chose_sport(call)
    else:
        if len(selected_sports[call.from_user.id]['other']) == 0:
            mes = bot.send_message(call.from_user.id, language['Start']['other_sports'],
                                   reply_markup=consent_cancel_other)
            bot.register_next_step_handler_by_chat_id(call.from_user.id, other_sports_next_step, mes)
        else:
            bot.send_message(call.from_user.id, language['Start']['repeat_other_sports']
                             .replace('&&', ', '.join(selected_sports[call.from_user.id]['other'])),
                             reply_markup=consent_repeat_cancel_other)


@bot.callback_query_handler(func=lambda call: call.data == "consent_cancel_other//cancel")
def cancel_other_sports(call: tb.types.CallbackQuery):
    """Пользователь ответил, что распознано не верно"""
    bot.edit_message_reply_markup(call.message.chat.id, call.message.id)
    if call.from_user.id not in selected_sports:
        chose_sport(call)
    else:
        bot.send_message(call.from_user.id, language['Start']['sport_select'],
                         reply_markup=sport_keyboard(call.from_user.id))


@bot.callback_query_handler(func=lambda call: call.data == "consent_repeat_cancel_other//no")
def wrong_repeat_other_sports(call: tb.types.CallbackQuery):
    """Пользователь ответил, что не хочет изменять"""
    cancel_other_sports(call)


@bot.callback_query_handler(func=lambda call: call.data == "consent_repeat_cancel_other//yes")
def applied_repeat_other_sports(call: tb.types.CallbackQuery):
    """Пользователь утвердил что хочет изменить"""
    if call.from_user.id not in selected_sports:
        bot.edit_message_reply_markup(call.message.chat.id, call.message.id)
        chose_sport(call)
    else:
        selected_sports[call.from_user.id]['other'] = []
        other_sports(call)


def other_sports_next_step(message: tb.types.Message, consent_message: tb.types.Message):
    """Обработка ответа на другие виды спорта"""
    bot.edit_message_reply_markup(consent_message.chat.id, consent_message.id)
    data = list(map(lambda x: x.capitalize(),
                    sum(map(lambda x: x.split(','), message.text.replace('\n', '').split(', ')), [])))
    bot.send_message(message.chat.id, language['Start']['consent_other_sports']
                     .replace('&&', '\n*' + '*,\n*'.join(data) + '*'),
                     reply_markup=consent_other_sports)
    selected_sports[message.from_user.id]['other'] = data


@bot.callback_query_handler(func=lambda call: call.data == "consent_other_sports//no")
def wrong_other_sports(call: tb.types.CallbackQuery):
    """Пользователь ответил, что распознано неверно"""
    if call.from_user.id not in selected_sports:
        bot.edit_message_reply_markup(call.message.chat.id, call.message.id)
        chose_sport(call)
    else:
        selected_sports[call.from_user.id]['other'] = []
        other_sports(call)


@bot.callback_query_handler(func=lambda call: call.data == "consent_other_sports//yes")
def applied_other_sports(call: tb.types.CallbackQuery):
    """Пользователь утвердил другие виды спорта"""
    bot.edit_message_reply_markup(call.message.chat.id, call.message.id)
    bot.send_message(call.from_user.id, language['Start']['sport_select'],
                     reply_markup=sport_keyboard(call.from_user.id))


def applied_kinds_of_sports(call: tb.types.CallbackQuery):
    """Подтверждение выбора"""
    bot.edit_message_reply_markup(call.message.chat.id, call.message.id)
    user = selected_sports[call.from_user.id]
    sports = [*map(lambda x: language['Sports'][x][1:], user['sports']), *user['other']]
    bot.edit_message_text(language['Start']['applied_kinds_of_sports'].replace('&&', ', '.join(sports)),
                          call.message.chat.id, call.message.id, reply_markup=consent_applied_kinds_of_sports)


@bot.callback_query_handler(func=lambda call: call.data == "consent_applied_kinds_of_sports//no")
def wrong_kinds_of_sports(call: tb.types.CallbackQuery):
    """Пользователь ответил, что распознано неверно"""
    bot.edit_message_reply_markup(call.message.chat.id, call.message.id)
    chose_sport(call)


@bot.callback_query_handler(func=lambda call: call.data == "consent_applied_kinds_of_sports//yes")
def applied_kinds_of_sports_consent(call: tb.types.CallbackQuery):
    """Пользователь утвердил виды спорта"""
    bot.edit_message_reply_markup(call.message.chat.id, call.message.id)
    if call.from_user.id not in selected_sports:
        chose_sport(call)
    else:
        bot.send_message(call.from_user.id, language['Start']['levels_of_professionalism_suggestion'])
        selected_sports_professionalism[call.from_user.id] = {}
        user = selected_sports_professionalism[call.from_user.id]
        user['sports'] = {i: 0 for i in selected_sports[call.from_user.id]['sports']}
        user['other'] = {i: 0 for i in selected_sports[call.from_user.id]['other']}
        user['number_of_sport'] = 0
        user['messages'] = []
        del selected_sports[call.from_user.id]
        levels_of_professionalism(call)


def levels_of_professionalism(call: tb.types.CallbackQuery):
    """Определение уровня профессионализма (отправка сообщения со спортом)"""
    user = selected_sports_professionalism[call.from_user.id]
    number_of_sport = user['number_of_sport']
    if number_of_sport < len(user['sports']):
        sport = list(user['sports'].keys())[number_of_sport]
        user['messages'].append(bot.send_message(call.from_user.id, language['Start']['levels_of_professionalism']
                                                 .replace('&&', language['Sports'][sport]),
                                                 reply_markup=levels_of_professionalism_keyboard(sport,
                                                                                                 number_of_sport)).id)
    elif number_of_sport < len(user['sports']) + len(user['other']):
        sport = list(user['other'].keys())[number_of_sport - len(user['sports'])]
        user['messages'].append(bot.send_message(call.from_user.id, language['Start']['levels_of_professionalism']
                                                 .replace('&&', sport),
                                                 reply_markup=levels_of_professionalism_keyboard(sport,
                                                                                                 number_of_sport)).id)
    else:
        bot.send_message(call.from_user.id, language['Start']['consent_levels_of_professionalism'],
                         reply_markup=consent_levels_of_professionalism)


@bot.callback_query_handler(func=lambda call: call.data[:34] == "levels_of_professionalism_keyboard")
def levels_of_professionalism_call(call):
    """Выбор уровня профессионализма"""
    data: List[str] = call.data.split('//')
    user = selected_sports_professionalism[call.from_user.id]
    number_of_sport = int(data[2])
    selected = int(data[3])
    bot.edit_message_reply_markup(call.message.chat.id, call.message.id,
                                  reply_markup=levels_of_professionalism_keyboard(data[1], data[2], selected))
    if number_of_sport < len(user['sports']):
        user['sports'][data[1]] = selected
    else:
        user['other'][data[1]] = selected
    if user['number_of_sport'] == number_of_sport:
        user['number_of_sport'] += 1
        levels_of_professionalism(call)


@bot.callback_query_handler(func=lambda call: call.data == "consent_levels_of_professionalism//yes")
def applied_consent_levels_of_professionalism(call: tb.types.CallbackQuery):
    """Подтверждены уровни профессионализма"""
    about_user(call)
    bot.edit_message_reply_markup(call.message.chat.id, call.message.id)
    for mes_id in selected_sports_professionalism[call.from_user.id]['messages']:
        bot.edit_message_reply_markup(call.message.chat.id, mes_id)
    user = selected_sports_professionalism[call.from_user.id]
    db['registration'].update_one({'_id': call.from_user.id}, {'$set': {
        'kinds_of_sports': user['sports'],
        'other_kinds_of_sports': {i.lower(): j for i, j in user['other'].items()}
    }})
    del selected_sports_professionalism[call.from_user.id]


def about_user(call: tb.types.CallbackQuery):
    """Запрос на ввод информации "о себе" """
    bot.send_message(call.from_user.id, language['Start']['about_user'])
    bot.register_next_step_handler_by_chat_id(call.from_user.id, about_user_consent)


def about_user_consent(message: tb.types.Message, sent_mes=None):
    """Утверждение введенного "о себе" """
    if sent_mes is None:
        if len(message.text) > 255:
            sent_mes = bot.send_message(message.from_user.id, language['Start']['about_user_consent_too_long'])
        else:
            sent_mes = bot.send_message(message.from_user.id, language['Start']['about_user_consent']
                                        .replace('&&', message.text), reply_markup=consent_about_user)
            db['registration'].update_one({'_id': message.from_user.id}, {'$set': {
                'about': message.text
            }})
    else:
        if len(message.text) > 255:
            bot.edit_message_text(language['Start']['about_user_consent_too_long'], sent_mes.chat.id, sent_mes.id)
        else:
            bot.edit_message_text(language['Start']['about_user_consent'].replace('&&', message.text),
                                  sent_mes.chat.id, sent_mes.id, reply_markup=consent_about_user)
            db['registration'].update_one({'_id': message.from_user.id}, {'$set': {
                'about': message.text
            }})

    # функция определения изменения сообщения
    @bot.edited_message_handler(func=lambda mes: mes.id == message.id and mes.from_user.id == message.from_user.id)
    def message_edited_func(mes):
        about_user_consent(mes, sent_mes=sent_mes)
        for el in bot.message_handlers:
            if el['function'] == message_sent_func:
                bot.message_handlers.remove(el)
                break
        for el in bot.edited_message_handlers:
            if el['function'] == message_edited_func:
                bot.edited_message_handlers.remove(el)
                break

    # функция определения отправки нового сообщения
    @bot.message_handler(func=lambda mes: mes.from_user.id == message.from_user.id)
    def message_sent_func(mes):
        try:
            bot.edit_message_reply_markup(sent_mes.chat.id, sent_mes.id)
        except tb.apihelper.ApiTelegramException:
            pass
        about_user_consent(mes)
        for el in bot.message_handlers:
            if el['function'] == message_sent_func:
                bot.message_handlers.remove(el)
                break
        for el in bot.edited_message_handlers:
            if el['function'] == message_edited_func:
                bot.edited_message_handlers.remove(el)
                break

    chat_id = message.chat.id
    if chat_id not in about_user_decs_list:
        about_user_decs_list[chat_id] = {}
    about_user_decs_list[chat_id]['sent'] = message_sent_func
    about_user_decs_list[chat_id]['edited'] = message_edited_func


@bot.callback_query_handler(func=lambda call: call.data == "consent_about_user//no")
def wrong_about_user_consent(call: tb.types.CallbackQuery):
    """Пользователь ответил, что не верно"""
    bot.edit_message_reply_markup(call.message.chat.id, call.message.id)
    bot.send_message(call.from_user.id, language['Start']['about_user_consent_wrong'])


@bot.callback_query_handler(func=lambda call: call.data == "consent_about_user//yes")
def applied_about_user_consent(call: tb.types.CallbackQuery):
    """Пользователь утвердил "о себе" """
    chat_id = call.message.chat.id
    bot.edit_message_reply_markup(chat_id, call.message.id)
    message_sent_func = about_user_decs_list[chat_id]['sent']
    message_edited_func = about_user_decs_list[chat_id]['edited']
    for el in bot.message_handlers:
        if el['function'] == message_sent_func:
            bot.message_handlers.remove(el)
            break
    for el in bot.edited_message_handlers:
        if el['function'] == message_edited_func:
            bot.edited_message_handlers.remove(el)
            break
    del about_user_decs_list[chat_id]
    consent_registration(call)


def consent_registration(call: tb.types.CallbackQuery):
    user = db['users'].find_one({'_id': call.from_user.id})
    if user is None:
        bot.send_message(call.from_user.id, language['Start']['consent_registration'],
                         reply_markup=consent_registration_keyboard)
    else:
        user_data = db['registration'].find_one_and_delete({'_id': call.from_user.id})
        for key, value in user_data.items():
            user[key] = value
        user['settings_updated'].append(datetime.datetime.now())
        user['current_position'] = 'main_menu_case'
        db['users'].find_one_and_replace({'_id': call.from_user.id}, user)
        main_menu.main_menu_cycle(call.from_user.id)


@bot.callback_query_handler(func=lambda call: call.data == "consent_registration_keyboard//no")
def wrong_consent_registration(call: tb.types.CallbackQuery):
    """Пользователь ответил, что не утверждает регистрацию"""
    bot.edit_message_reply_markup(call.message.chat.id, call.message.id)
    bot.send_message(call.from_user.id, language['Start']['wrong_consent_registration'],
                     reply_markup=wrong_consent_registration_keyboard)


@bot.callback_query_handler(func=lambda call: call.data == "wrong_consent_registration//no")
def wrong_consent_registration(call: tb.types.CallbackQuery):
    """Пользователь ответил, что не утверждает отмену регистрации"""
    bot.edit_message_reply_markup(call.message.chat.id, call.message.id)
    consent_registration(call)


@bot.callback_query_handler(func=lambda call: call.data == "wrong_consent_registration//yes")
def applied_about_user_consent(call: tb.types.CallbackQuery):
    """Пользователь утвердил отмену регистрации """
    bot.edit_message_reply_markup(call.message.chat.id, call.message.id)
    start_cycle(call.from_user.id)


@bot.callback_query_handler(func=lambda call: call.data == "consent_registration_keyboard//yes")
def applied_about_user_consent(call: tb.types.CallbackQuery):
    """Пользователь утвердил регистрацию """
    chat_id = call.message.chat.id
    bot.edit_message_reply_markup(chat_id, call.message.id)
    user_data = db['registration'].find_one_and_delete({'_id': call.from_user.id})
    user_data['settings_updated'] = [datetime.datetime.now()]
    user_data['matches'] = {}
    user_data['current_position'] = 'main_menu_case'
    db['users'].insert_one(user_data)
    main_menu.main_menu_cycle(call.from_user.id)


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
consent_date_of_birth = tb.types.InlineKeyboardMarkup(
    [
        [
            tb.types.InlineKeyboardButton(text=language['Start']['yes'],
                                          callback_data='consent_date_of_birth//yes'),
            tb.types.InlineKeyboardButton(text=language['Start']['no'],
                                          callback_data='consent_date_of_birth//no')
        ]
    ])
select_sex = tb.types.InlineKeyboardMarkup(
    [
        [
            tb.types.InlineKeyboardButton(text=language['Start']['sex_male'],
                                          callback_data='select_sex//sex_male'),
            tb.types.InlineKeyboardButton(text=language['Start']['sex_female'],
                                          callback_data='select_sex//sex_female')
        ],
        [
            tb.types.InlineKeyboardButton(text=language['Start']['sex_non_binary'],
                                          callback_data='select_sex//sex_non_binary'),
        ]
    ])
consent_sex = {
    'sex_male': tb.types.InlineKeyboardMarkup(
        [
            [
                tb.types.InlineKeyboardButton(text=language['Start']['selected'] + language['Start']['sex_male'],
                                              callback_data=f'consent_sex//sex_male//sex_male'),
                tb.types.InlineKeyboardButton(text=language['Start']['sex_female'],
                                              callback_data=f'consent_sex//sex_male//sex_female')
            ],
            [
                tb.types.InlineKeyboardButton(text=language['Start']['sex_non_binary'],
                                              callback_data=f'consent_sex//sex_male//sex_non_binary'),
            ]
        ]),
    'sex_female': tb.types.InlineKeyboardMarkup(
        [
            [
                tb.types.InlineKeyboardButton(text=language['Start']['sex_male'],
                                              callback_data=f'consent_sex//sex_female//sex_male'),
                tb.types.InlineKeyboardButton(text=language['Start']['selected'] + language['Start']['sex_female'],
                                              callback_data=f'consent_sex//sex_female//sex_female')
            ],
            [
                tb.types.InlineKeyboardButton(text=language['Start']['sex_non_binary'],
                                              callback_data=f'consent_sex//sex_female//sex_non_binary'),
            ]
        ]),
    'sex_non_binary': tb.types.InlineKeyboardMarkup(
        [
            [
                tb.types.InlineKeyboardButton(text=language['Start']['sex_male'],
                                              callback_data=f'consent_sex//sex_non_binary//sex_male'),
                tb.types.InlineKeyboardButton(text=language['Start']['sex_female'],
                                              callback_data=f'consent_sex//sex_non_binary//sex_female')
            ],
            [
                tb.types.InlineKeyboardButton(text=language['Start']['selected'] + language['Start']['sex_non_binary'],
                                              callback_data=f'consent_sex//sex_non_binary//sex_non_binary'),
            ]
        ])
}
consent_other_sports = tb.types.InlineKeyboardMarkup(
    [
        [
            tb.types.InlineKeyboardButton(text=language['Start']['yes'],
                                          callback_data='consent_other_sports//yes'),
            tb.types.InlineKeyboardButton(text=language['Start']['no'],
                                          callback_data='consent_other_sports//no')
        ]
    ])
consent_cancel_other = tb.types.InlineKeyboardMarkup(
    [
        [
            tb.types.InlineKeyboardButton(text=language['Start']['cancel'],
                                          callback_data='consent_cancel_other//cancel')
        ]
    ])
consent_repeat_cancel_other = tb.types.InlineKeyboardMarkup(
    [
        [
            tb.types.InlineKeyboardButton(text=language['Start']['yes'],
                                          callback_data='consent_repeat_cancel_other//yes'),
            tb.types.InlineKeyboardButton(text=language['Start']['no'],
                                          callback_data='consent_repeat_cancel_other//no')
        ]
    ])
consent_applied_kinds_of_sports = tb.types.InlineKeyboardMarkup(
    [
        [
            tb.types.InlineKeyboardButton(text=language['Start']['yes'],
                                          callback_data='consent_applied_kinds_of_sports//yes'),
            tb.types.InlineKeyboardButton(text=language['Start']['no'],
                                          callback_data='consent_applied_kinds_of_sports//no')
        ]
    ])
consent_about_user = tb.types.InlineKeyboardMarkup(
    [
        [
            tb.types.InlineKeyboardButton(text=language['Start']['yes'],
                                          callback_data='consent_about_user//yes'),
            tb.types.InlineKeyboardButton(text=language['Start']['no'],
                                          callback_data='consent_about_user//no')
        ]
    ])
consent_levels_of_professionalism = tb.types.InlineKeyboardMarkup(
    [
        [
            tb.types.InlineKeyboardButton(text=language['Start']['yes'],
                                          callback_data='consent_levels_of_professionalism//yes')
        ]
    ])
consent_registration_keyboard = tb.types.InlineKeyboardMarkup(
    [
        [
            tb.types.InlineKeyboardButton(text=language['Start']['yes'],
                                          callback_data='consent_registration_keyboard//yes'),
            tb.types.InlineKeyboardButton(text=language['Start']['no'],
                                          callback_data='consent_registration_keyboard//no')
        ]
    ])
wrong_consent_registration_keyboard = tb.types.InlineKeyboardMarkup(
    [
        [
            tb.types.InlineKeyboardButton(text=language['Start']['yes'],
                                          callback_data='wrong_consent_registration_keyboard//yes'),
            tb.types.InlineKeyboardButton(text=language['Start']['no'],
                                          callback_data='wrong_consent_registration_keyboard//no')
        ]
    ])


def levels_of_professionalism_keyboard(sport: str, number_of_sport: Union[int, str], selected: Optional[int] = None):
    if selected is None:
        return tb.types.InlineKeyboardMarkup(
            [
                [
                    tb.types.InlineKeyboardButton(text=str(i),
                                                  callback_data=f'levels_of_professionalism_keyboard//{sport}'
                                                                f'//{number_of_sport}//{i}')
                    for i in range(int(config['Sports']['min_levels_of_professionalism']),
                                   int(config['Sports']['max_levels_of_professionalism']) + 1)
                ]
            ])
    else:
        return tb.types.InlineKeyboardMarkup(
            [
                [
                    tb.types.InlineKeyboardButton(text=str(i),
                                                  callback_data=f'levels_of_professionalism_keyboard//{sport}'
                                                                f'//{number_of_sport}//{i}//{selected}')
                    if i != selected else
                    tb.types.InlineKeyboardButton(text=language['Start']['selected'],
                                                  callback_data=f'levels_of_professionalism_keyboard//{sport}'
                                                                f'//{number_of_sport}//{i}//{selected}')
                    for i in range(int(config['Sports']['min_levels_of_professionalism']),
                                   int(config['Sports']['max_levels_of_professionalism']) + 1)
                ]
            ])
