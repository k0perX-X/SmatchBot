from bot_resoses import *
from spellchecker import SpellChecker
import datetime

months_checker = SpellChecker(local_dictionary="resources/empty.json", distance=4)
months_checker.word_frequency.load_text_file("resources/months.ini")
months_name = {'январь': 1, 'февраль': 2, 'март': 3, 'апрель': 4, 'май': 5, 'июнь': 6, 'июль': 7, 'август': 8,
               'сентябрь': 9, 'октябрь': 10, 'ноябрь': 11, 'декабрь': 12}
months_number = {1: 'Января', 2: 'Февраля', 3: 'Марта', 4: 'Апреля', 5: 'Мая', 6: 'Июня', 7: 'Июля', 8: 'Августа',
                 9: 'Сентября', 10: 'Октября', 11: 'Ноября', 12: 'Декабря'}

consent_to_reset_keyboard = None
consent_to_policy = None
consent_name = None
consent_date_of_birth = None
select_sex = None
consent_sex = {}

selected_sports = {}
kinds_of_sports = [i for i in language['Sports']]


# todo если не закончил регистрацию запрос через время на продолжение


@bot.message_handler(commands=['start'])
def start_command(message):
    """Функция команды start"""
    if len([r for r in db['users'].find({"_id": message.from_user.id})]) == 1:
        # если у человек зарегистрирован в боте спрашиваем разрешение на сброс
        bot.send_message(message.from_user.id, language['Start']['restart'],
                         reply_markup=consent_to_reset_keyboard)
    else:
        start_cycle(message.from_user.id)


@bot.callback_query_handler(func=lambda call: call.data == "consent_to_reset_keyboard//no")
def reset_canceled(call):
    """если запретил сброс"""
    bot.edit_message_reply_markup(call.message.chat.id, call.message.id)
    start_cycle(call.from_user.id)


@bot.callback_query_handler(func=lambda call: call.data == "consent_to_reset_keyboard//yes")
def reset_applied(call):
    """если разрешил сброс"""
    bot.edit_message_reply_markup(call.message.chat.id, call.message.id)
    db['users'].delete_one({'_id': call.from_user.id})
    start_cycle(call.from_user.id)


def start_cycle(id):
    """Запуск цикла функции start"""
    bot.send_message(id, language['Start']['message'])
    bot.send_message(id, language['Start']['policy'], reply_markup=consent_to_policy)


@bot.callback_query_handler(func=lambda call: call.data == "consent_to_policy//yes")
def policy_applied(call):
    """если согласен с политикой"""
    bot.edit_message_reply_markup(call.message.chat.id, call.message.id)
    bot.send_message(call.from_user.id, language['Start']['get_name'])
    bot.register_next_step_handler_by_chat_id(call.from_user.id, get_name)
    try:
        db['registration'].insert_one({
            "_id": call.from_user.id
        })
    except pm.errors.DuplicateKeyError:
        pass


def get_name(message):
    """Уточнение правильности имени"""
    bot.send_message(message.from_user.id, language['Start']['consent_get_name'].replace('&&', message.text),
                     reply_markup=consent_name)
    db['registration'].update_one({'_id': message.from_user.id}, {'$set': {
        'name': message.text
    }})


@bot.callback_query_handler(func=lambda call: call.data == "consent_name//no")
def wrong_name(call):
    """имя не верное"""
    bot.edit_message_reply_markup(call.message.chat.id, call.message.id)
    bot.send_message(call.from_user.id, language['Start']['repeat_get_name'])
    bot.register_next_step_handler_by_chat_id(call.from_user.id, get_name)


@bot.callback_query_handler(func=lambda call: call.data == "consent_name//yes")
def correct_name(call):
    """имя верное"""
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
    # проверка на 18 лет
    today = datetime.date.today()
    if date_of_birth > datetime.date(today.year - 18, today.month, today.day):
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
    """Распознана дата но пользователю нет 18 лет"""
    bot.send_message(message.from_user.id, language['Start']['repeat_18_get_date_of_birth'])
    bot.register_next_step_handler_by_chat_id(message.from_user.id, get_date_of_birth)


@bot.callback_query_handler(func=lambda call: call.data == "consent_date_of_birth//no")
def wrong_date_of_birth_call(call: tb.types.CallbackQuery):
    """пользователь ответил, что распознано не верно"""
    bot.edit_message_reply_markup(call.message.chat.id, call.message.id)
    bot.send_message(call.from_user.id, language['Start']['repeat_get_date_of_birth'])
    bot.register_next_step_handler_by_chat_id(call.from_user.id, get_date_of_birth)


@bot.callback_query_handler(func=lambda call: call.data == "consent_date_of_birth//yes")
def applied_date_of_birth(call: tb.types.CallbackQuery):
    """пользователь утвердил дату рождения"""
    bot.edit_message_reply_markup(call.message.chat.id, call.message.id)
    bot.send_message(call.from_user.id, language['Start']['select_sex'],
                     reply_markup=select_sex)


@bot.callback_query_handler(func=lambda call: call.data[0:10] == "select_sex")
def consent_sex_func(call: tb.types.CallbackQuery):
    """запрос на утверждение пола"""
    bot.edit_message_text(language['Start']['select_sex'] + '\n' +
                          language['Start']['consent_sex'].replace('&&', language['Start'][call.data[12:]]),
                          call.message.chat.id, call.message.id, reply_markup=consent_sex[call.data[12:]])


@bot.callback_query_handler(func=lambda call: call.data[0:11] == "consent_sex")
def apply_sex(call: tb.types.CallbackQuery):
    """утверждение пола"""
    data = call.data.split('//')
    if data[1] != data[2]:
        bot.edit_message_text(language['Start']['select_sex'] + '\n' +
                              language['Start']['consent_sex'].replace('&&', language['Start'][data[2]]),
                              call.message.chat.id, call.message.id, reply_markup=consent_sex[data[2]])
    else:
        bot.edit_message_text(language['Start']['selected_sex'].replace('&&', language['Start'][data[2]]),
                              call.message.chat.id, call.message.id)
        bot.send_message(call.from_user.id, language['Start']['sport_select'],
                         reply_markup=sport_keyboard(call.from_user.id))


def sport_keyboard(id: int) -> tb.types.InlineKeyboardMarkup:
    """Создание клавиатуры для выбора спорта"""
    if id not in selected_sports:
        selected_sports[id] = {}
        selected_sports[id]['page'] = 0
        selected_sports[id]['sports'] = []
    user = selected_sports[id]
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
def chose_sport(call: tb.types.CallbackQuery):
    """Выбор спорта"""
    if call.from_user.id in selected_sports:
        sport = call.data[17:]
        match sport:
            case 'left':
                if selected_sports[call.from_user.id]['page'] > 0:
                    selected_sports[call.from_user.id]['page'] -= 1
            case 'right':
                selected_sports[call.from_user.id]['page'] += 1
            case 'other':
                # todo
                pass
            case 'apply':
                # todo
                pass
            case _:
                if sport not in selected_sports[call.from_user.id]['sports']:
                    selected_sports[call.from_user.id]['sports'].append(sport)
                else:
                    selected_sports[call.from_user.id]['sports'].remove(sport)
    bot.edit_message_text(language['Start']['sport_select'], call.message.chat.id, call.message.id,
                          reply_markup=sport_keyboard(call.from_user.id))


def keyboards_declaration():
    global consent_to_reset_keyboard
    global consent_to_policy
    global consent_name
    global consent_date_of_birth
    global select_sex
    global consent_sex
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
    for i in ['sex_male', 'sex_female', 'sex_non_binary']:
        consent_sex[i] = tb.types.InlineKeyboardMarkup(
            [
                [
                    tb.types.InlineKeyboardButton(text=language['Start']['sex_male'],
                                                  callback_data=f'consent_sex//{i}//sex_male'),
                    tb.types.InlineKeyboardButton(text=language['Start']['sex_female'],
                                                  callback_data=f'consent_sex//{i}//sex_female')
                ],
                [
                    tb.types.InlineKeyboardButton(text=language['Start']['sex_non_binary'],
                                                  callback_data=f'consent_sex//{i}//sex_non_binary'),
                ]
            ])


keyboards_declaration()
