from telebot import types
from config import TOKEN
import asyncio
from db import User, Check, Winner
import datetime
from config import DB_USER, passwd, host, port, database, winner_count
from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker
conn = "mysql+mysqlconnector://{0}:{1}@{2}:{3}/{4}".format(DB_USER, passwd, host, port, database)
engine = create_engine(conn)
session = sessionmaker(bind=engine)
import random
from telebot.async_telebot import AsyncTeleBot
bot = AsyncTeleBot(TOKEN)




def get_winners():
    s = session()
    d = datetime.datetime.now() - datetime.timedelta(days=1)
    weekAgo = datetime.datetime.now() - datetime.timedelta(days=7)
    last_winners = []
    for winner in s.query(Winner.u_id).filter(Winner.date_add > weekAgo):
        last_winners.append(winner[0])



    checks500 = s.query(Check.id, Check.check_number, Check.u_id, Check.sum).filter(Check.date_add > d,
                                                                                    Check.sum <= 1000, Check.sum>=500)

    arrChecks500 = get_arrCheks(checks500)

    checks1000 = s.query(Check.id, Check.check_number, Check.u_id, Check.sum).filter(Check.date_add > d,
                                                                                     Check.sum > 1000,
                                                                                     Check.sum <= 2000)
    arrChecks1000 = get_arrCheks(checks1000)

    checks2000 = s.query(Check.id, Check.check_number, Check.u_id, Check.sum).filter(Check.date_add > d,
                                                                                     Check.sum > 2000)
    arrChecks2000 = get_arrCheks(checks2000)

    n = 0
    win500 = []
    if arrChecks500 and len(arrChecks500) > 0:
        if len(arrChecks500) > 4:
            n = 4
        else:
            n = len(arrChecks500)
        win500 = get_winarr(n, arrChecks500, last_winners)
    ost = winner_count - n
    n = 0
    win1000 = []
    if arrChecks1000 and len(arrChecks1000) > 0:
        if len(arrChecks1000) > 12:
            n = 12
        else:
            n = len(arrChecks1000)
        win1000 = get_winarr(n, arrChecks1000, last_winners)

    ost = ost - n
    win2000 = []
    if arrChecks2000 and len(arrChecks2000) > 0:
        if len(arrChecks2000) >= ost:
            n = ost
        else:
            n = len(arrChecks2000)
        win2000 = get_winarr(n, arrChecks2000, last_winners)

    add_new_winner(win500, s)
    add_new_winner(win1000, s)
    add_new_winner(win2000, s)
    print('Конкурс проведен')
    s.commit()
    s.close()


def get_winarr(n, arr, last_winners):
    win = []
    i = 1
    while i <= n and len(arr) > 0:
        w = random.choice(arr)
        if w['c_user'] not in last_winners:
            if w not in win:
                win.append(w)
                i = i + 1
            arr.remove(w)
        else:
            arr.remove(w)
    return win


def start_keyboard():
    keyboard_start = types.ReplyKeyboardMarkup(resize_keyboard=True)
    keyboard_start.row(types.KeyboardButton(text="Учавствовать в розыгрыше"))
    return keyboard_start


def add_new_winner(arr, s):
    if arr:
        for user in arr:
            new_winner = Winner(u_id=user['c_user'])
            s.add(new_winner)
            winner_tlg_id = s.query(User.tlg_id).filter(User.id == user['c_user']).first()
            send_winner_message(winner_tlg_id, user)
            s.commit()



def send_winner_message(tlg_id, user):
    print (tlg_id)
    # await bot.send_photo(tlg_id[0], 'http://cs3.livemaster.ru/zhurnalfoto/0/d/7/150608002810.jpeg', caption=f"""\
    #         Поздравляем вы выиграли в розыгрыше. Ваш чек №{user['c_number']}  оказался в числе победителей
    #         """, reply_markup=start_keyboard())


def get_arrCheks(checks):
    arrChecks = []
    for check in checks:
        c = {
            'c_id': check[0],
            'c_number': check[1],
            'c_user': check[2],
            'c_sum': check[3]
        }

        arrChecks.append(c)
    return arrChecks


if __name__ == '__main__':
    get_winners()