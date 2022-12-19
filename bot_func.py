from db_client import db
from itertools import groupby
from operator import itemgetter


def generate_message(button):
    msg = ''
    if button['size'] or button['price'] != None:
        msg += f'<b>Блюдо: {button["name"]}\n</b>'
    if button['size'] != None:
        msg += f'<b>Размер порции: {button["size"]}\n\n</b>'
    msg += button['to_print'] + '\n'

    if button['price'] != None:
        msg += '\n\n'
        msg += f'<b>Цена: {button["price"]} BYN</b>'

    return msg


def top_button_date(date):
    data = db.button_date(date)
    msg = f'Топ 3 кнопки за {date}: \n\n'
    if len(data) < 1:
        msg += 'Данных нет'
    else:
        for i in data:
            msg += f'{i[0]} {i[1]} клик(ов)\n'
    return msg


def top_user_date(date):
    data = db.user_date(date)
    msg = f'Топ 3 кнопки за {date}: \n\n'
    if len(data)<1:
        msg += 'Данных нет'
    else:
        for i in data:
            msg += f'{i[0]} {i[1]} клик(ов)\n'
    return msg

def top_button_click():
    msg = ''
    for k,v in groupby(db.button_top(),key=itemgetter('name')):
        msg +=f'<b>{str(k)}</b>\n\n'
        for r in v:
            msg +=r['button_name']+':  ' +str(r['cnt'])+' клик(ов) '+'\n'
        msg+= '\n'
    return msg

def top_user_chapter():
    msg = ''
    for k, v in groupby(db.user_top(), key=itemgetter('name')):
        msg += f'<b>{str(k)}</b>\n\n'
        for r in v:
            msg += r['user_name'] + ':  ' + str(r['cnt']) + ' клик(ов) ' + '\n'
        msg += '\n'
    return msg





