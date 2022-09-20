from telebot import types
from config import TOKEN
import asyncio
from db import User, Check, Winner
from config import DB_USER, passwd, host, port, database, winner_count
from sqlalchemy import create_engine, select, desc
from sqlalchemy.orm import sessionmaker
import traceback
import datetime
from telebot.async_telebot import AsyncTeleBot

bot = AsyncTeleBot(TOKEN)

conn = "mysql+mysqlconnector://{0}:{1}@{2}:{3}/{4}".format(DB_USER, passwd, host, port, database)
engine = create_engine(conn, pool_recycle=1800)
session = sessionmaker(bind=engine)


@bot.message_handler(commands=['help', 'start'])
async def send_welcome(message):
    s = session()

    user = s.query(User).filter_by(tlg_id=message.from_user.id).first()

    if user is None:
        new_user = User(tlg_id=message.from_user.id)
        s.add(new_user)
        await bot.send_photo(message.from_user.id, 'https://proma-group.ru/rusneft.jpg', caption="""\
        <b>Добро пожаловать в автоматический розыгрыш !</b> 
        """, reply_markup=start_keyboard(), parse_mode='html')
        s.commit()
    else:
        await bot.send_photo(message.from_user.id, 'https://proma-group.ru/rusneft.jpg', caption="""\
              <b>Добро пожаловать в автоматический розыгрыш !</b> 
                """, reply_markup=start_keyboard(), parse_mode='html')

    s.close()




def start_keyboard():
    keyboard_start = types.ReplyKeyboardMarkup(resize_keyboard=True)
    keyboard_start.row(types.KeyboardButton(text="Учавствовать в розыгрыше"))
    return keyboard_start




@bot.message_handler(func=lambda message: message.text == "Учавствовать в розыгрыше")
async def take_part(message):
    print(message)
    s = session()
    last_check = s.query(Check.date_add).filter(User.tlg_id == message.from_user.id, User.id == Check.u_id).order_by(
        desc(Check.id)).first()
    time_now = datetime.datetime.now()

    if last_check:
        if (time_now - last_check[0]).total_seconds() / 60 / 60 > 1:
            await bot.send_message(message.from_user.id, """\
                    Введите номер чека
                """, reply_markup=types.ReplyKeyboardRemove())
            s.query(User).filter_by(tlg_id=message.from_user.id).update({"status": 'take_check'})

        else:
            await bot.send_message(message.from_user.id, """\
                Вы отправили чек на розыгрыш меньше 1 часа назад, пожалуйста подождите и попробуйте еще раз,
                """, )
    else:
        await bot.send_message(message.from_user.id, """\
                           Введите номер чека
                       """, reply_markup=types.ReplyKeyboardRemove())
        s.query(User).filter_by(tlg_id=message.from_user.id).update({"status": 'take_check'})

    s.commit()
    s.close()


@bot.message_handler(content_types=['text'])
async def handle_text(message):
    s = session()
    status = s.query(User.id, User.status).filter_by(tlg_id=message.from_user.id).first()

    try:
        print(message.chat.id, status)

        if status is not None:
            if status[1] == 'take_check':
                if len(message.text) == 4:

                    check = s.query(Check.check_number).filter(Check.check_number == message.text).first()
                    if check == None:
                        newCheck = Check(u_id=status[0], check_number=message.text)
                        s.add(newCheck)
                        s.commit()
                        s.query(User).filter_by(id=status[0]).update({"status": "take_summ"})
                        await bot.send_message(message.from_user.id, """\
                            Введите сумму чека (Если введенная сумма не совпадает с суммой на чеке, то выигрыш аннулируется)
                        """)
                    else:
                        await  bot.send_message(message.from_user.id, """\
                                      Такой чек уже учавствует в розыгрыше, измените номер, попробуйте еще раз
                                  """, reply_markup=start_keyboard())
                        s.query(User).filter_by(tlg_id=message.from_user.id).update({"status": ''})
                else:
                    await  bot.send_message(message.from_user.id, """\
                        Номер чека состоит из четырех цифр""")


            elif status[1] == 'take_summ':
                if message.text.isdigit() and len(message.text) <= 4 and int(message.text) > 0:

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
                        await get_win(message.from_user.id, int(message.text), str(check[0]), status[0], username)

                        s.query(User).filter_by(tlg_id=message.from_user.id).update({"status": ''})
                    except Exception:
                        traceback.print_exc()
                        await  bot.send_message(message.from_user.id, f"""\
                                                         Недопустимое значение, попробуйте еще раз
                                                     """)
                else:
                    await  bot.send_message(message.from_user.id, f"""\
                                         Недопустимое значение, попробуйте еще раз
                                     """)
            else:
                await  bot.delete_message(message.from_user.id, message.message_id)
        else:
            await bot.delete_message(message.from_user.id, message.message_id)
    except:
        traceback.print_exc()

    try:
        s.commit()
    except:
        s.rollback()
    finally:
        s.close()


async def get_win(tlg_id, sum, check_num, u_id, username):
    s = session()
    if sum < 1000:
        ever = 15
        checks = s.query(Check.check_number, Check.sum).filter(Check.sum < 1000,
                                                               Check.date_add >= datetime.date.today()).count()

    elif sum >= 1000 and sum < 2000:
        checks = s.query(Check.check_number, Check.sum).filter(Check.sum >= 1000, Check.sum < 2000,
                                                               Check.date_add >= datetime.date.today()).count()
        ever = 10
    elif sum >= 2000:
        checks = s.query(Check.check_number, Check.sum).filter(Check.sum >= 2000,
                                                               Check.date_add >= datetime.date.today()).count()
        ever = 5

    if checks % ever == 0:
        await  bot.send_photo(tlg_id, 'https://proma-group.ru/rusneft.jpg', caption="""\
    <b>ВЫ ВЫИГРАЛИ 20 ЛИТРОВ!
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
Вы  - получаете дополнительно 10 литров к  выигрышным 20 литрам!

Для получения топлива по Акции не забывайте взять с собой выигрышный чек!
""", reply_markup=start_keyboard(), parse_mode='html')
        new_winner = Winner(u_id=u_id)
        s.add(new_winner)

        await bot.send_message("-1001696174650", f'Выиграл чек номер <b>{check_num}</b> на сумму {sum}',
                               parse_mode='html')  # Русьнефть
        await bot.send_message("-1001159770221", f'Выиграл чек номер <b>{check_num}</b> на сумму {sum}',
                               parse_mode='html')  # Любаж

        await bot.send_message("-1001660063532",
                               f'Выиграл чек номер <b>{check_num}</b> на сумму {sum} пользователь {username}',
                               parse_mode='html')  # Группа АЗС Семеновская
        await bot.send_message("-1001659700171",
                               f'Выиграл чек номер <b>{check_num}</b> на сумму {sum} пользователь {username}',
                               parse_mode='html')  # Группа АЗС Любаж




    else:
        await  bot.send_photo(tlg_id, 'https://proma-group.ru/rusneft.jpg', caption="""\
        <b>Вы НЕ выиграли,</b> не переживайте. Вы ничего не потеряли, а приобрели отличное топливо по хорошей цене! 

По теории вероятности Вы  обязательно выиграете и многократно ! 

Выигрышных чеков больше : 

40 в день! 
1200 в месяц! 
14400 в год!

Играйте и выигрывайте! 
Искренне желаем Вам удачи!
    """, reply_markup=start_keyboard(), parse_mode='html')
        await bot.send_message("-1001660063532",
                               f'Учавствовал чек номер <b>{check_num}</b> на сумму {sum} пользователь @{username}',
                               parse_mode='html')  # Группа АЗС Семеновская
        await bot.send_message("-1001659700171",
                               f'Учавствовал чек номер <b>{check_num}</b> на сумму {sum} пользователь @{username}',
                               parse_mode='html')  # Группа АЗС Любаж
    s.commit()
    s.close()
    return


if __name__ == '__main__':
    asyncio.run(bot.polling(non_stop=True, timeout=40))



