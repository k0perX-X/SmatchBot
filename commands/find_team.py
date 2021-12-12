from bot_resources import *
import commands.main_menu as main_menu


def find_team_start(user_id: int):
    bot.send_message(user_id, "На данный момент функция в разработке")
    main_menu.main_menu_cycle(user_id)
