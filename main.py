import telebot
from telebot import types
from telebot import TeleBot
from config import TOKEN
import asyncio

from db import User, Check, Winner
from config import DB_USER, passwd, host, port, database, winner_count
from sqlalchemy import create_engine, select
from sqlalchemy import asc
from sqlalchemy import desc
from sqlalchemy.orm import sessionmaker
import traceback
import datetime
import time
import random


bot = TeleBot(TOKEN)

conn = "mysql+mysqlconnector://{0}:{1}@{2}:{3}/{4}".format(DB_USER, passwd, host, port, database)
engine = create_engine(conn)
session = sessionmaker(bind=engine)


@bot.message_handler(commands=['help', 'start'])
def send_welcome(message):
    s = session()

    user = s.query(User).filter_by(tlg_id=message.from_user.id).first()
    if not user:
        new_user = User(tlg_id=message.from_user.id)
        s.add(new_user)
        bot.send_photo(message.from_user.id, 'https://list-english.ru/img/tables/welcomes.jpg', caption="""\
        Добро пожаловать! 
        """, reply_markup=start_keyboard())
        # await bot.send_message(message.from_user.id, """\
        # Добро пожаловать!
        # """, reply_markup=start_keyboard())
        s.commit()
    else:
        bot.send_photo(message.from_user.id, 'https://list-english.ru/img/tables/welcomes.jpg', caption="""\
                С возвращением!
                """, reply_markup=start_keyboard())

    s.close()


def start_keyboard():
    keyboard_start = types.ReplyKeyboardMarkup(resize_keyboard=True)
    keyboard_start.row(types.KeyboardButton(text='🎊🎊Учавствовать в розыгрыше🎊🎊'))
    return keyboard_start


@bot.message_handler(func=lambda message: message.text == "🎊🎊Учавствовать в розыгрыше🎊🎊")
def take_part(message):

    s = session()
    last_check = s.query(Check.date_add).filter(User.tlg_id == message.from_user.id, User.id == Check.u_id).order_by(desc(Check.id)).first()
    time_now = datetime.datetime.now()
    if last_check:
        if (time_now - last_check[0]).total_seconds()/60/60 > 5:
            bot.send_message(message.from_user.id, """\
                    Введите номер чека
                """, reply_markup=types.ReplyKeyboardRemove())
            s.query(User).filter_by(tlg_id=message.from_user.id).update({"status": 'take_check'})

        else:
            bot.send_message(message.from_user.id, """\
                Вы отправили чек на розыгрыш меньше 5 часов назад, пожалуйста подождите и попробуйте еще раз,
                """, )




    s.commit()
    s.close()


@bot.message_handler(content_types=['text'])
def handle_text(message):
    s = session()
    status = s.query(User.id, User.status).filter_by(tlg_id=message.from_user.id).first()


    if status[1] == 'take_check':
        check = s.query(Check.check_number).filter(Check.check_number == message.text).first()
        if check == None:
            newCheck = Check(u_id=status[0], check_number=message.text)
            s.add(newCheck)
            s.query(User).filter_by(id=status[0]).update({"status": "take_summ"})
            bot.send_message(message.from_user.id, """\
                Введите сумму чека (Если введенная сумма не совпадает с суммой на чеке, то выигрыш аннулируется)
            """)
        else:
            bot.send_message(message.from_user.id, """\
                          Такой чек уже учавствует в розыгрыше, измените номер, попробуйте еще раз
                      """,  reply_markup=start_keyboard())
            s.query(User).filter_by(tlg_id=message.from_user.id).update({"status": ''})


    elif status[1] == 'take_summ':
        if message.text.isdigit():
            try:
                s.query(Check).filter(Check.u_id == status[0], Check.sum == 0).update({"sum": int(message.text)})
                s.flush()
                check = s.query(Check.check_number, Check.sum)\
                    .filter(Check.u_id == status[0])\
                    .order_by(desc(Check.id)).first()

                bot.send_message(message.from_user.id, f"""\
                     Ваш чек № {str(check[0])} на сумму {message.text}₽ добавлен на участие в розыгрыш
                 """, reply_markup=start_keyboard())

                s.query(User).filter_by(tlg_id=message.from_user.id).update({"status": ''})
            except Exception:
                traceback.print_exc()
                bot.send_message(message.from_user.id, f"""\
                                                 Недопустимое значение, попробуйте еще раз
                                             """)
        else:
            bot.send_message(message.from_user.id, f"""\
                                 Недопустимое значение, попробуйте еще раз
                             """)
    else:
        bot.delete_message(message.from_user.id, message.message_id)
        # await bot.send_message(message.from_user.id, f"""\
        #                                  Не понимаю
        #                              """)

    try:
        s.commit()
    except:
        s.rollback()
    finally:
        s.close()



def get_winners():
    s = session()

    d = datetime.datetime.now() - datetime.timedelta(days=1)
    weekAgo = datetime.datetime.now() - datetime.timedelta(days=7)
    last_winners = []

    for winner in s.query(Winner.u_id).filter(Winner.date_add > weekAgo):
        last_winners.append(winner[0])

    checks500 = s.query(Check.id,Check.check_number, Check.u_id, Check.sum).filter(Check.date_add > d, Check.sum<=1000)
    arrChecks500 = get_arrCheks(checks500)

    checks1000 = s.query(Check.id,Check.check_number, Check.u_id, Check.sum).filter(Check.date_add > d, Check.sum > 1000, Check.sum <= 2000)
    arrChecks1000 = get_arrCheks(checks1000)

    checks2000 = s.query(Check.id, Check.check_number, Check.u_id, Check.sum).filter(Check.date_add > d,  Check.sum>2000)
    arrChecks2000 = get_arrCheks(checks2000)


    n=0
    win500 = []
    if arrChecks500 and len(arrChecks500)>0:
        if len(arrChecks500)>3:
            n = 3
        else:
            n = len(arrChecks500)
        win500 = get_winarr(n, arrChecks500, last_winners)
    ost = winner_count - n
    n = 0
    win1000=[]
    if arrChecks1000 and len(arrChecks1000)>0:
        if len(arrChecks1000)>12:
            n = 12
        else:
            n = len(arrChecks1000)
        win1000 = get_winarr(n, arrChecks1000, last_winners)


    ost = ost - n
    win2000=[]
    if arrChecks2000 and len (arrChecks2000)>0:
        if len(arrChecks2000)>=ost:
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


def add_new_winner(arr, s):
    if arr:
        for user in arr:
            new_winner = Winner(u_id=user['c_user'])
            s.add(new_winner)
            winner_tlg_id = s.query(User.tlg_id).filter(User.id == user['c_user']).first()
            send_winner_message(winner_tlg_id, user)

def send_winner_message(tlg_id, user):

    bot.send_photo(tlg_id[0], 'http://cs3.livemaster.ru/zhurnalfoto/0/d/7/150608002810.jpeg', caption=f"""\
            Поздравляем вы выиграли в розыгрыше. Ваш чек №{user['c_number']}  оказался в числе победителей 
            """, reply_markup=start_keyboard())

def get_arrCheks(checks):
    arrChecks = []
    for check in checks:
        c = {
            'c_id': check[0],
            'c_number' : check[1],
            'c_user' : check[2],
            'c_sum':check[3]
        }

        arrChecks.append(c)
    return arrChecks

def get_winarr(n, arr, last_winners):
    win = []
    i = 1
    while i <= n and len(arr)>0:
        w = random.choice(arr)
        if w['c_user'] not in last_winners:
            if w not in win:
                win.append(w)
                i = i + 1
            arr.remove(w)
        else:
            arr.remove(w)
    return win



if __name__ == '__main__':



    while True:
        # print(datetime.datetime.now())
        # get_winners()
        try:
            bot.polling(none_stop=False,interval=1)
        except Exception as E:
            time.sleep(1)



