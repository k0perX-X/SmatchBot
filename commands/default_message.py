from bot_resources import *
from commands import *


def user_position(message: tb.types.Message):
    user = db['users'].find_one({'_id': message.from_user.id})
    print(message.from_user.id)
    if user is not None:
        func = eval(user['current_position'])
        func(message)
    else:
        start_cycle(message.from_user.id)


@bot.message_handler()
def default_message(message: tb.types.Message):
    user_position(message)
