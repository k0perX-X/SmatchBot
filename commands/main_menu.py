from bot_resources import *
import commands.find_partner as find_partner
import commands.find_team as find_team
import commands.settings as settings
from typing import Any, Callable, List, Optional, Union


def main_menu_cycle(user_id: int):
    bot.send_message(user_id, language['Main menu']['suggestion_main_menu'], reply_markup=main_keyboard,
                     disable_notification=True)
    db['users'].update_one({'_id': user_id}, {'$set': {
        'current_position': 'main_menu_case'
    }})
    bot.register_next_step_handler_by_chat_id(user_id, main_menu_case)


def main_menu_case(message: tb.types.Message):
    if message.text == language['Main menu']['find_partner']:
        find_partner.find_partner_start(message.from_user.id)
    elif message.text == language['Main menu']['find_team']:
        find_team.find_team_start(message.from_user.id)
    elif message.text == language['Main menu']['settings']:
        settings.settings_start(message.from_user.id)
    else:
        main_menu_cycle(message.from_user.id)


main_keyboard = tb.types.ReplyKeyboardMarkup(one_time_keyboard=True)
main_keyboard.row(
    tb.types.KeyboardButton(language['Main menu']['find_partner']),
    tb.types.KeyboardButton(language['Main menu']['find_team'])
)
main_keyboard.row(
    tb.types.KeyboardButton(language['Main menu']['settings'])
)
