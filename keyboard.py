from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
from telebot import  types

def gen_markup():
    keyboard = InlineKeyboardMarkup()
    btnfirst = InlineKeyboardButton(str("👍") + "0", callback_data="cb_yes")
    btnSecond = InlineKeyboardButton(str("👎") + "0", callback_data="cb_no")
    keyboard.add(btnfirst, btnSecond)
    return keyboard


def start_keyboard():
    keyboard_start = types.ReplyKeyboardMarkup(resize_keyboard=True)
    keyboard_start.row(types.KeyboardButton(text="Учавствовать в розыгрыше"))
    return keyboard_start


def start_admin_keyboard():
    keyboard_start = types.ReplyKeyboardMarkup(resize_keyboard=True)
    keyboard_start.row(types.KeyboardButton(text="Учавствовать в розыгрыше"))
    keyboard_start.row(types.KeyboardButton(text="Создать опрос"))
    return keyboard_start

def sendChatKeyboard():
    keyboard = InlineKeyboardMarkup()
    btnfirst = InlineKeyboardButton("Руснефть Семеновская", callback_data="send_semen")
    btnSecond = InlineKeyboardButton("Руснефть любаж", callback_data="send_lubaj")
    keyboard.add(btnfirst, btnSecond)
    return keyboard