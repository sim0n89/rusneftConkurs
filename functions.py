
from db import User, Votes, UserVote
from config import DB_USER, passwd, host, port, database
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import datetime
from telebot import  types

conn = "mysql+mysqlconnector://{0}:{1}@{2}:{3}/{4}?unix_socket=/var/run/mysqld/mysqld.sock".format(DB_USER, passwd,
                                                                                                   host, port, database)
engine = create_engine(conn, pool_recycle=1800, pool_pre_ping=True)
session = sessionmaker(engine)

def update_statusUserVote(user_id, user_status, vote_pole, vote_text):
    s = session()
    vote = s.query(Votes).order_by(Votes.id.desc()).first()
    s.query(Votes).filter_by(id=vote.id).update({vote_pole: str(vote_text)})
    s.commit()
    s.query(User).filter_by(id=user_id).update({"status": user_status})
    s.commit()
    s.close()


def makeVoteToChat():
    s = session()
    vote = s.query(Votes).order_by(Votes.id.desc()).first()
    keyboard = types.InlineKeyboardMarkup()

    btnfirst = types.InlineKeyboardButton(str(vote.quest1) + "\xa0(0)", callback_data="quest1")
    btndec2 = types.InlineKeyboardButton(str(vote.quest2) + "\xa0(0)", callback_data="quest2")
    btndec3 = types.InlineKeyboardButton(str(vote.quest3) + "\xa0(0)", callback_data="quest3")
    btndec4 = types.InlineKeyboardButton(str(vote.quest4) + "\xa0(0)", callback_data="quest4")
    btndec5 = types.InlineKeyboardButton(str(vote.quest5) + "\xa0(0)", callback_data="quest5")
    btndec6 = types.InlineKeyboardButton(str(vote.quest6) + "\xa0(0)", callback_data="quest6")
    btndec7 = types.InlineKeyboardButton(str(vote.quest7) + "\xa0(0)", callback_data="quest7")
    btndec8 = types.InlineKeyboardButton(str(vote.quest8) + "\xa0(0)", callback_data="quest8")
    btndec9 = types.InlineKeyboardButton(str(vote.quest9) + "\xa0(0)", callback_data="quest9")
    # btndec10 = types.InlineKeyboardButton(str(vote.quest6) + "\xa0(0)", callback_data="quest10")
    keyboard.add(btnfirst,btndec2, btndec3, btndec4, btndec5, btndec6, btndec7, btndec8, btndec9)
    vote = {'message': vote.theme, 'keyboard': keyboard}
    return vote


def editVoteKeyboard(question, json):
    keyboard = types.InlineKeyboardMarkup()
    btns = []
    for line in json:
        for button in line:

            if question in button['callback_data']:
                splitted = button['text'].split('\xa0')
                summ = int(splitted[-1].replace("(", '').replace(")", '')) + 1
                button["text"] = button['text'] = splitted[0] + "\xa0" + "(" + str(summ) + ")"
            btns.append(button)
    btn0 = types.InlineKeyboardButton(str(btns[0]['text']), callback_data=str(btns[0]["callback_data"]))
    btn1 = types.InlineKeyboardButton(str(btns[1]['text']), callback_data=str(btns[1]["callback_data"]))
    btn2 = types.InlineKeyboardButton(str(btns[2]['text']), callback_data=str(btns[2]["callback_data"]))
    btn3 = types.InlineKeyboardButton(str(btns[3]['text']), callback_data=str(btns[3]["callback_data"]))
    btn4 = types.InlineKeyboardButton(str(btns[4]['text']), callback_data=str(btns[4]["callback_data"]))
    btn5 = types.InlineKeyboardButton(str(btns[5]['text']), callback_data=str(btns[5]["callback_data"]))
    btn6 = types.InlineKeyboardButton(str(btns[6]['text']), callback_data=str(btns[6]["callback_data"]))
    btn7 = types.InlineKeyboardButton(str(btns[7]['text']), callback_data=str(btns[7]["callback_data"]))
    btn8 = types.InlineKeyboardButton(str(btns[8]['text']), callback_data=str(btns[8]["callback_data"]))

    keyboard.add(btn0, btn1, btn2, btn3, btn4, btn5, btn6, btn7, btn8)
    return keyboard

def check_uservote(user, chat, msg, from_user):
    s = session()
    print(type(str()))
    count = s.query(UserVote).filter_by(tg_id=user, chat_id=chat, message_id=msg).count()
    if count == 0:
        newVote = UserVote(tg_id=user, chat_id=chat, message_id=msg, from_user=str(from_user),date_add=datetime.datetime.now())
        s.add(newVote)
        s.commit()
        s.close()
        return True

    else:
        s.close()
        return False


