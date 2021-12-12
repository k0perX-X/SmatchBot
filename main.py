from bot_resources import *
import traceback
from commands import *
from backend import *
from typing import Any, Callable, List, Optional, Union


def users_start_position(user_id: Optional[int] = None):
    if user_id is not None:
        users = db['users'].find({'_id': user_id})
    else:
        users = db['users'].find({})
    for user in users:
        try:
            bot.register_next_step_handler_by_chat_id(user_id, eval(user['current_position']))
        except Exception as e:
            logging.error(f'users_start_position - {traceback.format_exc()}')


if __name__ == '__main__':
    users_start_position()
    bot.infinity_polling()

