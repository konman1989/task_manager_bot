
from telebot import TeleBot, types

bot = TeleBot('926931469:AAH7VzaTMd-2wJ_AQClwyA9o42kXcC2r0Ck')


def build_keyboard(*args, row_width=2):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True,
                                       row_width=row_width)
    markup.add(*args)
    return markup


def build_inline_keyboard(items, hidden_items, call_back_data):
    keyboard = types.InlineKeyboardMarkup()

    for i in range(len(items)):
        keyboard.add(
            types.InlineKeyboardButton(
                items[i],
                callback_data=f'{call_back_data}_{items[i]}_{hidden_items[i]}')
        )

    return keyboard





