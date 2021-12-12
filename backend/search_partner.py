from threading import Thread
from bot_resources import *
from typing import Any, Callable, List, Optional, Union
import traceback
import datetime

spread_of_professionalism = int(config['Search partner']['spread_of_professionalism'])
sports = dict(language['Sports'])


class Searcher(Thread):
    def __init__(self, user_id: int):
        super().__init__()
        self.user_id = user_id

    def run(self):
        user = db['users'].find_one({'_id': self.user_id})
        users = list(db['users'].aggregate([
            {'$match': {'_id': {'$ne': user['_id']}}},
            {
                '$project': {
                    'locations': '$locations',
                    'finder_locations': user['locations'],
                    'finder_date_of_birth': user['date_of_birth'],
                    'partner_date_of_birth': '$date_of_birth',
                    'kinds_of_sports': '$kinds_of_sports',
                    'other_kinds_of_sports': '$other_kinds_of_sports'
                }
            }, {
                '$unwind': '$finder_locations'
            }, {
                '$unwind': '$locations'
            }, {
                '$project': {
                    'range': {
                        '$add': [
                            {
                                '$multiply': [
                                    '$finder_locations.latitude_sin',
                                    '$locations.latitude_sin'
                                ]
                            },
                            {
                                '$multiply': [
                                    '$finder_locations.latitude_cos',
                                    '$locations.latitude_cos',
                                    {
                                        '$cos': {
                                            '$subtract': [
                                                '$finder_locations.longitude_rad',
                                                '$locations.longitude_rad'
                                            ]
                                        }
                                    }
                                ]
                            }
                        ]
                    },
                    'partner_range': '$locations.range',
                    'finder_range': '$finder_locations.range',
                    'finder_date_of_birth': '$finder_date_of_birth',
                    'partner_date_of_birth': '$partner_date_of_birth',
                    'kinds_of_sports': '$kinds_of_sports',
                    'other_kinds_of_sports': '$other_kinds_of_sports',
                    'finder_age': '$finder_locations.age',
                    'partner_age': '$locations.age',
                }
            }, {
                '$project': {
                    'range': {
                        '$cond': {
                            'if': {'$gte': ['$range', 1]},
                            'then': 0,
                            'else': {
                                '$multiply': [
                                    6371,
                                    {'$acos': '$range'}
                                ]
                            }
                        }
                    },
                    'year_date_diff': {
                        '$abs': {
                            '$dateDiff': {
                                'startDate': '$finder_date_of_birth',
                                'endDate': '$partner_date_of_birth',
                                'unit': 'year'
                            }
                        }},
                    'partner_range': '$partner_range',
                    'finder_range': '$finder_range',
                    'kinds_of_sports': '$kinds_of_sports',
                    'other_kinds_of_sports': '$other_kinds_of_sports',
                    'partner_age': '$partner_age',
                    'finder_age': '$finder_age'
                }
            }, {
                "$redact": {
                    "$cond": {
                        'if': {
                            '$and': [
                                {"$lte": ['$year_date_diff', "$partner_age"]},
                                {"$lte": ['$year_date_diff', "$finder_range"]},
                                {"$lte": ["$range", "$partner_range"]},
                                {"$lte": ["$range", "$finder_range"]}
                            ]
                        },
                        'then': "$$KEEP",
                        'else': "$$PRUNE"
                    }
                }
            }, {
                '$group': {
                    '_id': "$_id",
                    'kinds_of_sports': {'$first': '$kinds_of_sports'},
                    'other_kinds_of_sports': {'$first': '$other_kinds_of_sports'},
                    'range': {'$min': '$range'}
                }
            }, {
                "$project": {
                    "kinds_of_sports_array": {
                        "$objectToArray": '$kinds_of_sports'
                    },
                    'other_kinds_of_sports_array': {
                        "$objectToArray": '$other_kinds_of_sports'
                    },
                    'range': '$range',
                }
            }, {
                "$project": {
                    'range': '$range',
                    'array': {
                        '$setUnion': ["$kinds_of_sports_array", '$other_kinds_of_sports_array']
                    },
                    'finder_array': [
                        *[
                            {'k': k, 'v': v} for k, v in user['kinds_of_sports'].items()
                        ], *[
                            {'k': k, 'v': v} for k, v in user['other_kinds_of_sports'].items()
                        ]
                    ]
                }
            }, {
                '$unwind': '$array'
            }, {
                '$unwind': '$finder_array'
            }, {
                "$redact": {
                    "$cond": {
                        'if': {
                            '$eq': [
                                '$array.k',
                                '$finder_array.k'
                            ]
                        },
                        'then': "$$KEEP",
                        'else': "$$PRUNE"
                    }
                }
            }, {
                "$redact": {
                    "$cond": {
                        'if': {
                            '$lte': [
                                {'$abs': {
                                    '$subtract': [
                                        '$array.v',
                                        '$finder_array.v'
                                    ]
                                }},
                                spread_of_professionalism
                            ]
                        },
                        'then': "$$KEEP",
                        'else': "$$PRUNE"
                    }
                }
            }, {
                '$group': {
                    '_id': '$_id',
                    'kinds_of_sports_array': {
                        '$push': '$array'
                    },
                    'range': {
                        '$first': '$range'
                    }
                }
            },
        ], allowDiskUse=True))
        found(self.user_id, users)


def search(user_id: int):
    thread = Searcher(user_id)
    thread.start()


def found(finder_id: int, users: List[dict]):
    try:
        for dict_found_user in users:
            finder_user = db['users'].find_one({'_id': finder_id})
            found_user = db['users'].find_one({'_id': dict_found_user['_id']})
            if str(finder_user['_id']) in found_user['matches'].keys() or \
                    str(found_user['_id']) in finder_user['matches'].keys():
                continue
            today = datetime.date.today()
            if dict_found_user['range'] < 1:
                users_range = f"{int(dict_found_user['range'] * 100)} {language['Search partner']['m']}"
            elif dict_found_user['range'] < 10:
                users_range = f"{round(dict_found_user['range'] * 100) / 100} {language['Search partner']['kg']}"
            else:
                users_range = f"{round(dict_found_user['range'] * 10) / 10} {language['Search partner']['kg']}"
            born = finder_user['date_of_birth']
            bot.send_message(found_user['_id'], language['Search partner']['pitch']
                             .replace('&name&', finder_user['name'])
                             .replace('&years_old&', str(today.year - born.year -
                                                         ((today.month, today.day) < (born.month, born.day))))
                             .replace('&about&', finder_user['about'])
                             .replace('&sports&',
                                      ', '.join([sports[el['k']] if el['k'] in sports else el['k'].capitalize()
                                                 for el in dict_found_user['kinds_of_sports_array']]))
                             .replace('&range&', users_range),
                             reply_markup=pitch_inline_keyboard(found_user['_id'], finder_user['_id']))
            born = found_user['date_of_birth']
            bot.send_message(finder_user['_id'], language['Search partner']['pitch']
                             .replace('&name&', found_user['name'])
                             .replace('&years_old&', str(today.year - born.year -
                                                         ((today.month, today.day) < (born.month, born.day))))
                             .replace('&about&', found_user['about'])
                             .replace('&sports&',
                                      ', '.join([sports[el['k']] if el['k'] in sports else el['k'].capitalize()
                                                 for el in dict_found_user['kinds_of_sports_array']]))
                             .replace('&range&', users_range),
                             reply_markup=pitch_inline_keyboard(finder_user['_id'], found_user['_id']))
            db['users'].update_one({'_id': finder_user['_id']}, {
                '$set': {
                    f"matches.{found_user['_id']}": False
                }
            })
            db['users'].update_one({'_id': found_user['_id']}, {
                '$set': {
                    f"matches.{finder_user['_id']}": False
                }
            })
            break
    except Exception as e:
        logging.error(f'users_start_position - {traceback.format_exc()}')


@bot.callback_query_handler(func=lambda call: call.data[0:26] == "pitch_inline_keyboard//yes")
def yes_pitch_inline_keyboard(call: tb.types.CallbackQuery):
    bot.edit_message_reply_markup(call.message.chat.id, call.message.id)
    split = call.data.split('//')
    user2 = db['users'].find_one({'_id': int(split[3])})
    user1 = db['users'].find_one_and_update({'_id': call.from_user.id}, {
        '$set': {
            f"matches.{split[3]}": True
        }
    })
    if user2['matches'][str(call.from_user.id)]:
        today = datetime.date.today()
        born = user1['date_of_birth']
        bot.send_message(user2['_id'], language['Search partner']['match']
                         .replace('&name&', user1['name'])
                         .replace('&years_old&', str(today.year - born.year -
                                                     ((today.month, today.day) < (born.month, born.day))))
                         .replace('&about&', user1['about']),
                         reply_markup=match_inline_keyboard(user1['_id']))
        born = user2['date_of_birth']
        bot.send_message(user1['_id'], language['Search partner']['match']
                         .replace('&name&', user2['name'])
                         .replace('&years_old&', str(today.year - born.year -
                                                     ((today.month, today.day) < (born.month, born.day))))
                         .replace('&about&', user2['about']),
                         reply_markup=match_inline_keyboard(user2['_id']))


@bot.callback_query_handler(func=lambda call: call.data[0:25] == "pitch_inline_keyboard//no")
def no_pitch_inline_keyboard(call: tb.types.CallbackQuery):
    bot.edit_message_reply_markup(call.message.chat.id, call.message.id)
    search(call.from_user.id)


def pitch_inline_keyboard(id1: int, id2: int):
    return tb.types.InlineKeyboardMarkup(
        [
            [
                tb.types.InlineKeyboardButton(text=language['Search partner']['yes'],
                                              callback_data=f'pitch_inline_keyboard//yes//{id1}//{id2}'),
                tb.types.InlineKeyboardButton(text=language['Search partner']['no'],
                                              callback_data=f'pitch_inline_keyboard//no//{id1}//{id2}')
            ]
        ])


def match_inline_keyboard(user_id: int):
    return tb.types.InlineKeyboardMarkup(
        [
            [
                tb.types.InlineKeyboardButton(text=language['Search partner']['match_inline'],
                                              url=f'tg://user?id={user_id}')
            ]
        ])
