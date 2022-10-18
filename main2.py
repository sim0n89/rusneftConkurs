from telebot import types

import keyboard
from config import TOKEN, ADMINS
import asyncio
from db import User, Check, Winner, Votes, UserVote
from config import DB_USER, passwd, host, port, database, winner_count
from sqlalchemy import create_engine, select, desc
from sqlalchemy.orm import sessionmaker
import traceback
import datetime
from functions import  *
from telebot.async_telebot import AsyncTeleBot
import telebot
import time


bot = telebot.TeleBot(TOKEN)
WINTEXT = """\
            <b>ВЫ ВЫИГРАЛИ 10 ЛИТРОВ!
              ПОЗДРАВЛЯЕМ!</b>

        Выигрыш можно забрать СРАЗУ или в течение 96 часов (4 суток) с момента покупки топлива (исчисляется согласно времени, указанному на чеке) по адресам 
        АЗС «РУСЬНЕФТЬ»:
        Курск, ул Семеновская 64 
        или
        Курская область, Фатежский р-он, 
        с. В.Любаж,
        ул. Комсомольская 12 «б».

        Так же, пригласив друга, Вы дополнительно получаете 10 литров топлива бесплатно.
        При условии, что друг должен заправить свою машину по банковской карте платёжной системы МИР до полного бака (но не менее, чем на  20 литров).

        Ни Ваш друг, ни Вы ничего не теряете. 
        Друг -заправляет машину и получает возможность также участвовать в нашей Акции. 
        Вы  - получаете дополнительно 10 литров к  выигрышным 10 литрам!

        Для получения топлива по Акции не забывайте взять с собой выигрышный чек!
        """
LOSETEXT = """\
                <b>Вы НЕ выиграли,</b> не переживайте. Вы ничего не потеряли, а приобрели отличное топливо по хорошей цене! 

        По теории вероятности Вы  обязательно выиграете и многократно ! 

        Выигрышных чеков больше : 

        40 в день! 
        1200 в месяц! 
        14400 в год!

        Играйте и выигрывайте! 
        Искренне желаем Вам удачи!
            """

conn = "mysql+mysqlconnector://{0}:{1}@{2}:{3}/{4}?unix_socket=/var/run/mysqld/mysqld.sock".format(DB_USER, passwd,
                                                                                                   host, port, database)
engine = create_engine(conn, pool_recycle=1800, pool_pre_ping=True)
session = sessionmaker(engine)


@bot.message_handler(commands=['help', 'start'])
def send_welcome(message):
    s = session()
    bot.send_message('-1001784043663', "hello")
    user = s.query(User).filter_by(tlg_id=message.from_user.id).first()
    if message.from_user.id in ADMINS:
        board = keyboard.start_admin_keyboard()
    else:
        board = keyboard.start_keyboard()
    if user is None:
        new_user = User(tlg_id=message.from_user.id)
        s.add(new_user)
        bot.send_photo(message.from_user.id, 'https://proma-group.ru/rusneft.jpg', caption="""\
        <b>Добро пожаловать в автоматический розыгрыш !</b> 
        """, reply_markup=board, parse_mode='html')
        s.commit()
    else:
        bot.send_photo(message.from_user.id, 'https://proma-group.ru/rusneft.jpg', caption="""\
              <b>Добро пожаловать в автоматический розыгрыш !</b> 
                """, reply_markup=board, parse_mode='html')

    s.close()


@bot.message_handler(func=lambda message: message.text == "Создать опрос")
def take_part(message):
    s = session()
    s.query(User).filter_by(tlg_id=message.from_user.id).update({"status": 'make_vote'})
    bot.send_message(message.from_user.id, "Введите тему опроса")
    s.commit()
    s.close()


@bot.message_handler(func=lambda message: message.text == "Учавствовать в розыгрыше")
def take_part(message):
    s = session()
    last_check = s.query(Check.date_add).filter(User.tlg_id == message.from_user.id, User.id == Check.u_id).order_by(
        desc(Check.id)).first()
    time_now = datetime.datetime.now()

    if last_check:
        if (time_now - last_check[
            0]).total_seconds() / 60 / 60 > 1 or message.chat.id == 5319159831 or message.chat.id == 5305975198 or message.chat.id == 53275976:
            bot.send_message(message.from_user.id, """\
                    Введите номер чека
                """, reply_markup=types.ReplyKeyboardRemove())
            s.query(User).filter_by(tlg_id=message.from_user.id).update({"status": 'take_check'})

        else:
            bot.send_message(message.from_user.id, """\
                Вы отправили чек на розыгрыш меньше 1 часа назад, пожалуйста подождите и попробуйте еще раз,
                """, )
    else:
        bot.send_message(message.from_user.id, """\
                           Введите номер чека
                       """, reply_markup=types.ReplyKeyboardRemove())
        s.query(User).filter_by(tlg_id=message.from_user.id).update({"status": 'take_check'})

    s.commit()
    s.close()



@bot.callback_query_handler(func=lambda c:True)
def callback_inline(call):
    print(call)
    if call.data == "send_semen":
        vote = makeVoteToChat()

        bot.send_message('-1001784043663', vote["message"], reply_markup=vote['keyboard'])
        bot.edit_message_text(chat_id=call.from_user.id, text="Опрос отправлен", message_id=call.message.id)
    if call.data == "send_lubaj":
        vote = makeVoteToChat()
        bot.send_message('-1001696174650', vote["message"], reply_markup=vote['keyboard'])
        bot.edit_message_text(chat_id=call.from_user.id, text="Опрос отправлен", message_id=call.message.id)


    if "quest" in call.data:
        user_status = bot.get_chat_member(call.message.chat.id, call.from_user.id)

        if user_status.status!="left" and call.from_user.is_bot==False:

            if check_uservote(call.from_user.id, call.message.chat.id, call.message.id, call.from_user):
                bot.answer_callback_query(callback_query_id=call.id, show_alert=False, text="Голос принят")
                keyboard = editVoteKeyboard(call.data, call.message.json['reply_markup']['inline_keyboard'])
                bot.edit_message_text(call.message.text, call.message.chat.id, call.message.id, reply_markup=keyboard)
            else:
                bot.answer_callback_query(callback_query_id=call.id, show_alert=False, text="Вы уже учавствовали")
        else:
            bot.answer_callback_query(callback_query_id=call.id, show_alert=False, text="Для участия в голосовании Вам необходимо подписаться")


@bot.message_handler(content_types=['text'])
def handle_text(message):
    s = session()

    status = s.query(User.id, User.status).filter_by(tlg_id=message.from_user.id).first()

    try:
        print(message.chat.id, status)

        if status is not None:
            if status[1] == 'take_check':
                if len(message.text) == 4 or len(message.text) == 5:

                    check = s.query(Check.check_number).filter(Check.check_number == message.text).first()
                    if check == None:
                        newCheck = Check(u_id=status[0], check_number=message.text, date_add=datetime.datetime.now())
                        s.add(newCheck)
                        s.commit()
                        s.query(User).filter_by(id=status[0]).update({"status": "take_summ"})
                        bot.send_message(message.from_user.id, """\
                            Введите сумму чека (Если введенная сумма не совпадает с суммой на чеке, то выигрыш аннулируется)
                        """)
                    else:
                        bot.send_message(message.from_user.id, """\
                                      Такой чек уже существует, или попробуйте ещё раз или добавьте "0" к цифрам чека, чтобы было кратно 4 цифрам или 5 цифрам.
                                  """, reply_markup=keyboard.start_keyboard())
                        s.query(User).filter_by(tlg_id=message.from_user.id).update({"status": ''})
                else:
                    bot.send_message(message.from_user.id, """\
                        Добавьте нули чтобы было 4 или 5 цифр""")


            elif status[1] == 'take_summ':
                if message.text.isdigit() and len(message.text) <= 5 and int(message.text) > 0:

                    try:
                        s.query(Check).filter(Check.u_id == status[0], Check.sum == 0).update(
                            {"sum": int(message.text)})
                        s.flush()
                        check = s.query(Check.check_number, Check.sum) \
                            .filter(Check.u_id == status[0]) \
                            .order_by(desc(Check.id)).first()

                        username = f"@{message.from_user.username}"
                        if message.contact is not None:
                            print(message.contact.phone_number)
                        if message.from_user.username is None:
                            username = f'chat_id = {message.from_user.id}'
                        else:
                            username = f"@{message.from_user.username}"
                        if message.contact is not None:
                            print(message.contact.phone_number)
                            # username = username + ' телефон '
                        get_win(message.from_user.id, int(message.text), str(check[0]), status[0], username)

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

            elif status[1] == "make_vote":
                newVote = Votes(theme = message.text)
                s.add(newVote)
                s.commit()
                s.query(User).filter_by(id=status[0]).update({"status": "quest1"})
                bot.send_message(message.from_user.id, """\
                                            Введите первый вариант ответа
                                        """)
            elif status[1] == "quest1":
                update_statusUserVote(status[0],'quest2', "quest1", message.text)
                bot.send_message(message.from_user.id, """\
                                            Введите второй вариант ответа
                                        """)

            elif status[1] == "quest2":
                update_statusUserVote(status[0], 'quest3', "quest2", message.text)
                bot.send_message(message.from_user.id, """\
                                                       Введите третий вариант ответа
                                                   """)
            elif status[1] == "quest3":
                update_statusUserVote(status[0], 'quest4', "quest3", message.text)
                bot.send_message(message.from_user.id, """\
                                                       Введите четвертый вариант ответа
                                                   """)
            elif status[1] == "quest4":
                update_statusUserVote(status[0], 'quest5', "quest4", message.text)
                bot.send_message(message.from_user.id, """\
                                                       Введите пятый вариант ответа
                                                   """)
            elif status[1] == "quest5":
                update_statusUserVote(status[0], 'quest6', "quest5", message.text)
                bot.send_message(message.from_user.id, """\
                                                       Введите шестой вариант ответа
                                                   """)

            elif status[1] == "quest6":
                update_statusUserVote(status[0], 'quest7', "quest6", message.text)
                bot.send_message(message.from_user.id, """\
                                                       Введите седьмой вариант ответа
                                                   """)

            elif status[1] == "quest7":
                update_statusUserVote(status[0], 'quest8', "quest7", message.text)
                bot.send_message(message.from_user.id, """\
                                                       Введите восьмой вариант ответа
                                                   """)

            elif status[1] == "quest8":
                update_statusUserVote(status[0], 'quest9', "quest8", message.text)
                bot.send_message(message.from_user.id, """\
                                                       Введите девятый вариант ответа
                                                   """)
            elif status[1] == "quest9":
                update_statusUserVote(status[0], 'send_to_chat', "quest9", message.text)
                bot.send_message(message.from_user.id, """\
                                                       В какой чат отправить?
                                                   """, reply_markup=keyboard.sendChatKeyboard())

        else:
            bot.delete_message(message.from_user.id, message.message_id)
    except:
        traceback.print_exc()




    try:
        s.commit()
    except:
        s.rollback()
    finally:
        s.close()


def get_win(tlg_id, summ, check_num, u_id, username):
    s = session()
    try:

        if summ < 1000:
            ever = 13
            checks = s.query(Check.check_number, Check.sum).filter(Check.sum < 1000).count()
            bot.send_message("-1001783876284", f'{checks}й чек на сумму до 1000', parse_mode='html')

        elif summ >= 1000 and summ < 2000:
            ever = 9
            checks = s.query(Check.check_number, Check.sum).filter(Check.sum >= 1000, Check.sum < 2000).count()
            bot.send_message("-1001783876284", f'{checks}й чек на сумму от 1000 до 2000', parse_mode='html')

        elif summ >= 2000:
            ever = 5
            checks = s.query(Check.check_number, Check.sum).filter(Check.sum >= 2000).count()
            bot.send_message("-1001783876284", f'{checks}й чек на сумму от 2000', parse_mode='html')

        print(checks, checks % ever)
        ost = checks % ever
        if checks > 0:
            if ost == 0:
                bot.send_photo(tlg_id, 'https://proma-group.ru/rusneft.jpg', caption=WINTEXT,
                                      reply_markup=keyboard.start_keyboard(), parse_mode='html')
                bot.send_message("-1001696174650",
                                       f'Выиграл 10 литров!!! Чек номер <b>{check_num}</b> заправка была на сумму {summ} руб',
                                       parse_mode='html')  # Русьнефть
                bot.send_message("-1001159770221",
                                       f'Выиграл 10 литров!!! Чек номер <b>{check_num}</b> заправка была на сумму {summ} руб',
                                       parse_mode='html')  # Любаж
                bot.send_message("-1001660063532",
                                       f'Выиграл чек номер <b>{check_num}</b> заправка была на сумму  {summ} руб пользователь {username}',
                                       parse_mode='html')  # Группа АЗС Семеновская
                bot.send_message("-1001659700171",
                                       f'Выиграл чек номер <b>{check_num}</b> заправка была на сумму  {summ} руб пользователь {username}',
                                       parse_mode='html')  # Группа АЗС Любаж
                bot.send_message("-1001783876284",
                                       f'Выиграл чек номер <b>{check_num}</b> заправка была на сумму  {summ} руб пользователь @{username}',
                                       parse_mode='html')  # ЧЕКИ
                new_winner = Winner(u_id=u_id)
                s.add(new_winner)
                s.commit()
            else:
                 bot.send_photo(tlg_id, 'https://proma-group.ru/rusneft.jpg', caption=LOSETEXT,
                                      reply_markup=keyboard.start_keyboard(), parse_mode='html')
                 bot.send_message("-1001783876284",
                                       f'Участвовал чек номер <b>{check_num}</b> заправка была на сумму  {summ} руб пользователь {username}',
                                       parse_mode='html')  # ЧЕКИ
                # await bot.send_message("-1001659700171",
                #                       f'Участвовал чек номер <b>{check_num}</b> заправка была на сумму  {sum} руб пользователь @{username}',
                #                       parse_mode='html')  # Группа АЗС Любаж
    except:
        traceback.print_exc()
    s.commit()
    s.close()
    return



if __name__ == '__main__':
    bot.infinity_polling()



