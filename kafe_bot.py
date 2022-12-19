import telebot
from telebot import types
from time import sleep
from telebot import custom_filters
from telebot.handler_backends import State, StatesGroup
from telebot.storage import StateMemoryStorage
from datetime import datetime
from config import TOKEN, IS_ADMIN
from db_client import db
from bot_func import generate_message, top_button_date, top_user_date, top_button_click, top_user_chapter

state_storage = StateMemoryStorage()
bot = telebot.TeleBot(TOKEN, state_storage=state_storage)
bot.add_custom_filter(custom_filters.StateFilter(bot))


class MyStates(StatesGroup):
    button_date = State()
    user_date = State()


def get_keyboard(key):
    keyboard = types.InlineKeyboardMarkup()
    buttons = db.get_keyboard(key)
    for button in buttons:
        keyboard.add(types.InlineKeyboardButton(button['name'], callback_data=button['button_id']))
    return keyboard


@bot.message_handler(commands=['start'])
def start(message):
    if message.from_user.id not in db.check_user():
        db.enroll_user(message.from_user.id, message.from_user.username, message.from_user.full_name)
    if message.from_user.id in IS_ADMIN:
        bot.send_message(message.chat.id, f'Привет Admin', reply_markup=get_keyboard(0))
    else:
        bot.send_message(message.chat.id, f'Привет {message.from_user.full_name}', reply_markup=get_keyboard(0))


@bot.callback_query_handler(func=lambda call: True)
def common_button(call):
    button = db.get_button(call.data)[0]
    if button['is_rec']:
        db.enroll_click(call.from_user.id, button['name'], button['chapter_id'])
    bot.send_message(
        chat_id=call.message.chat.id,
        text=generate_message(button),
        reply_markup=get_keyboard(button['next_chapter']),
        parse_mode='html'
    )

@bot.message_handler(commands=['admin'])
def admin(message):
    if message.from_user.id in IS_ADMIN:
        user_markup = telebot.types.ReplyKeyboardMarkup(True,True,True)
        user_markup.row('/butt_top_click', '/user_top_click')
        user_markup.row('/butt_top_date', '/user_top_date',)
        bot.send_message(message.from_user.id, 'Меню администратора', reply_markup=user_markup)
    else:
        bot.send_message(message.chat.id, text='Вы не являетесь администратором!')

@bot.message_handler(commands=['butt_top_click'])
def butt_top(message):
    return bot.send_message(
        message.chat.id,
        text=top_button_click(),
        parse_mode='html'
    )

@bot.message_handler(commands=['user_top_click'])
def butt_top(message):
    return bot.send_message(
        message.chat.id,
        text=top_user_chapter(),
        parse_mode='html'
    )

@bot.message_handler(commands=['butt_top_date'])
def butt_date(message):
    if message.from_user.id in IS_ADMIN:
        bot.set_state(message.from_user.id, MyStates.button_date, message.chat.id)
        bot.send_message(
            message.chat.id,
            text='Введите дату в формате ДД-ММ-ГГГГ '
        )

    else:
        bot.send_message(message.chat.id, text='Вы не являетесь администратором!')


@bot.message_handler(state=MyStates.button_date)
def get_butt_date(message):
    inp = message.text
    try:
        date = bool(datetime.strptime(inp, "%d-%m-%Y"))
    except ValueError:
        date = False

    if not date:
        bot.send_message(message.chat.id, 'Введите корректную дату!')
        return
    bot.send_message(
        chat_id=message.chat.id,
        text=top_button_date(inp),
        parse_mode='html'
    )
    bot.delete_state(message.from_user.id, message.chat.id)


@bot.message_handler(commands=['user_top_date'])
def user_date(message):
    if message.from_user.id in IS_ADMIN:
        bot.set_state(message.from_user.id, MyStates.user_date, message.chat.id)
        bot.send_message(
            message.chat.id,
            text='Введите дату в формате ДД-ММ-ГГГГ '
        )

    else:
        bot.send_message(message.chat.id, text='Вы не являетесь администратором!')


@bot.message_handler(state=MyStates.user_date)
def get_user_date(message):
    inp = message.text
    try:
        date = bool(datetime.strptime(inp, "%d-%m-%Y"))
    except ValueError:
        date = False

    if not date:
        bot.send_message(message.chat.id, 'Введите корректную дату!')
        return
    bot.send_message(
        chat_id=message.chat.id,
        text=top_user_date(inp),
        parse_mode='html'
    )
    bot.delete_state(message.from_user.id, message.chat.id)


@bot.message_handler(content_types=['text'])
def get_message(message):
    db.save_message(message.from_user.id, message.text)
    return bot.reply_to(message, 'Информация принята к сведению')


while True:
    try:
        bot.polling(none_stop=True, interval=0)
    except Exception as _ex:
        print(_ex)
        sleep(15)
