import requests, os, datetime, time, logging, dotenv, argparse, json, traceback
import telebot as tb
from bs4 import BeautifulSoup
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
from typing import Literal

# local files
import logger, exception_handler
from logger import log
from db import database
from exception_handler import BotExceptionHandler
import kitis_api as api

# arguments
# init argument parser
arg_parser = argparse.ArgumentParser(
    prog='bot.py',
    description='Bot for parsing and viewing Kitis groups schedule in telegram bot'
)

# add arguments to parser
arg_parser.add_argument('-c', '--colored', action='store_true', help='enable colored output in logs')
arg_parser.add_argument('-t', '--token', help='token of your telegram bot')
arg_parser.add_argument('-n', '--notifications', help='get error notifications to https://ntfy.sh/[NTFY_TOPIC]', metavar='NTFY_TOPIC')
# arg_parser.add_argument('-f', '--config', help='path to config file') # to-do

# parse arguments and do somenthing with them
args = arg_parser.parse_args()

# load config
# use default config file
if os.path.exists('config.json'):
    with open("config.json", 'r') as f:
        cfg = json.load(f)
    # init logger
    logger.init_logger("log.log", args.colored, args.notifications)
# create new config file
else:
    conf_default = {
        # IMPORTANT
        # log colors use ANSI escape codes 
        # but i don't know how to put these codes in JSON
        # so, for example, instead of \x1b[30m it will be 30
        # first color is background, second is foreground
        # colors split by .
        "colors": {
            "ok":           "42.30",
            "info":         "47.30",
            "fail":         "41",
            "warn":         "43.30",
            "trash":        "90"
        },
        "links": {
            "base":         "http://94.72.18.202:8083/",
            "index":        "http://94.72.18.202:8083/index.htm",
            "s_group":      "http://94.72.18.202:8083/cg.htm",
            "s_lecturer":   "http://94.72.18.202:8083/cp.htm",
            "s_room":       "http://94.72.18.202:8083/ca.htm",
            "r_group":      "http://94.72.18.202:8083/vg.htm",
            "r_lecturer":   "http://94.72.18.202:8083/vp.htm"
        },
        "admins": [""]
    }
    with open('config.json', 'w', encoding='utf-8') as f:
        json.dump(conf_default, f, indent=4)
    cfg = conf_default
    # init logger
    logger.init_logger("log.log", args.colored, args.notifications)
    log("warn", "Config.json not found! creating new config file and using it for now")

# load .env file if present
dotenv.load_dotenv()
# get token from argument if present
if args.token:
    TOKEN = args.token
# get token from .env file if present
elif os.getenv('TOKEN'):
    TOKEN = os.getenv('TOKEN')
# no token given -> abort
else:
    log("fail", "No token given, aborting...")
    exit(1)
# initialize bot
try:
    exception_handler.set_token(TOKEN)
    bot = tb.TeleBot(TOKEN, exception_handler=BotExceptionHandler())
except Exception as e:
    log("fail", f"Can't initialize bot: {e}, aborting...")
    exit(1)

# Connecting to database
db = database('db.db')

# bells for monday
bells_monday = {
    '1 Пара':'8:30-9:00 / 15:20-15:50',
    '2 Пара':'9:10-10:30',
    '3 Пара':'10:40-12:00',
    '4 Пара':'12:20-13:40',
    '5 Пара':'13:50-15:10',
    '6 Пара':'16:00-17:20',
    '7 Пара':'17:30-18:50'
}
# bells for all other days (Tue, Wed, Thu, Fri, Sat)
bells = {
    '1 Пара':'8:30-10:00',
    '2 Пара':'10:10-11:40',
    '3 Пара':'12:10-13:40',
    '4 Пара':'13:50-15:20',
    '5 Пара':'15:30-17:00',
    '6 Пара':'17:10-18:40',
    '7 Пара':'18:50-20:20'
}
# links_group contains links to group schedules
log("trash", "Initializing api...")
api.init_api()

log("trash", "Getting links...")
links_group     = api.get_source_links("s_group")
links_lecturer  = api.get_source_links("s_lecturer")
links_room      = api.get_source_links("s_room")

# generate schedule message based on api info
def gen_message_schedule(source_type: Literal["group", "lecturer", "room"], source: str) -> str:
    data = api.get_schedule(source_type, source)
    # generate schedule by group
    if source_type == "group":
        msg = f"Расписание группы <b>{data["head"]}</b>\n"
        for date, info in data["days"].items():
            if info["weekday"] == "Воскресенье": break
            
            msg += f"\n--------------------------\n\n{date} - <b>{info["weekday"]}</b>\n\n"
            for lesson in info["lessons"]:
                msg += f"<u>{lesson["number"]} Пара</u> - <i>{lesson["bells"]}</i> - {lesson["name"]} {f"({lesson["subgroup"]})" if lesson["subgroup"] != "0" and not "Иностранный язык" in lesson["name"] else ""} - <i>{lesson["room"]}</i>\n"
    
    # by lecturer
    elif source_type == "lecturer":
        msg = f"Расписание преподавателя <b>{data["head"]}</b>\n"
        for date, info in data["days"].items():
            if info["weekday"] == "Воскресенье": break
            
            msg += f"\n--------------------------\n\n{date} - <b>{info["weekday"]}</b>\n\n"
            for lesson in info["lessons"]:
                msg += f"<u>{lesson["number"]} Пара</u> - <i>{lesson["bells"]}</i> - <b>{lesson["group"]}</b> - {lesson["name"]} - <i>{lesson["room"]}</i>\n"
    
    # by room
    elif source_type == "room":
        msg = f"Расписание аудитории <b>{data["head"]}</b>\n"
        for date, info in data["days"].items():
            if info["weekday"] == "Воскресенье": break
            
            msg += f"\n--------------------------\n\n{date} - <b>{info["weekday"]}</b>\n\n"
            for lesson in info["lessons"]:
                msg += f"<u>{lesson["number"]} Пара</u> - <i>{lesson["bells"]}</i> - {lesson["lecturer"]} - <b>{lesson["group"]}</b> - {lesson["name"]}\n"
    
    msg += f"\n--------------------------\n<i>{data["update_time"]}</i>"
    return msg

# generate markup for schedule source
def gm_schedule_sourcetype():
    markup = InlineKeyboardMarkup()
    markup.row_width = 3
    markup.add(
        InlineKeyboardButton("Группы", callback_data="group"),
        InlineKeyboardButton("Преподаватели", callback_data="lecturer"),
        InlineKeyboardButton("Аудитории", callback_data="room")
    )
    return markup
kb_source_schedule = gm_schedule_sourcetype()

# generate markup keyboard for group selection
def gm_schedule_source(source_type: Literal["group", "lecturer", "room"]):
    markup = InlineKeyboardMarkup()
    markup.row_width = 3
    if source_type == "group":      keys = list(links_group.keys())
    if source_type == "lecturer":   keys = list(links_lecturer.keys())
    if source_type == "room":       keys = list(links_room.keys())
    IKB_list = list()

    for n in range(len(keys)):
        IKB_list.append(InlineKeyboardButton(keys[n], callback_data=keys[n]))
    
    markup.add(*IKB_list)
    return markup
kb_schedule = gm_schedule_source("group")

# check spam for certain commands
def is_spam(prev_use_time: float, cooldown: float):
    return (time.time() - prev_use_time) < cooldown

def is_spam_or_ungroupped(uid: int):
    cooldown = 3
    # check group
    if not db.get_value(uid, "user_group"):
        log("warn", f"{uid} did not set a group!")
        bot.send_message(uid, "Сначала выберите группу! - /group")
        return True
    # check spam
    elif time.time() - db.get_value(uid, "last_schedule_request_time") < cooldown:
        log("warn", f"{uid} is too fast!")
        bot.send_message(uid, "Вы слишком часто запрашиваете расписание! Подождите немного и попробуйте снова...")
        return True
    return False

# check user
def checkUser(uid : str, uname : str):
    # check if user already exists
    if db.user_exists(uid):
        if db.get_value(uid, 'username') != uname:
            db.update_value(uid, 'username', uname)
            log("trash", f"Updated {uid} username: {uname}")
    # otherwise add new user to database
    else:
        db.add_user(uid, uname)
        log("info", f"Added {uid} ({uname}) to database")

# Start message command
@bot.message_handler(commands=['start'])
def start(message):
    log("info", f"/start - {message.chat.id} ({message.chat.username})")
    bot.send_message(message.chat.id, 'Привет, это бот для просмотра расписания КИТиС!\nДля начала выбери свою группу с помощью команды /group, а после этого используй команду /schedule, чтобы посмотреть расписание выбранной группы!')
    # check user
    checkUser(message.chat.id, message.chat.username)


def send_schedule(uid: int, source_type: Literal["group", "lecturer", "room"], source: str) -> None:
    mes = bot.send_message(uid, parse_mode="HTML",
        text="Получение данных...\n\n<i>Это может занять некоторое время. Если вы это читаете, скорее всего бот восстанавливает соединение с сайтом...\n...а может что-то пошло не так :)</i>")
    text = gen_message_schedule(source_type, source)
    if text:
        log("ok", f"Sent schedule - {uid}")
        bot.edit_message_text(text, uid, message_id=mes.id, parse_mode="HTML")
        db.update_value(uid, "last_schedule_request_time", time.time())
    else:
        log("fail", f"Did not sent schedule - {uid}")
        bot.edit_message_text("Не удалось получить расписание! Попробуйте позже...", uid, mes.id, parse_mode="HTML")
    return
# Schedule command
@bot.message_handler(commands=["schedule"])
def bot_schedule(message) -> None:
    uid = message.chat.id
    uname = message.chat.username
    checkUser(uid, uname)
    log("info", f"/schedule - {uid} ({uname})")
    if is_spam_or_ungroupped(uid):
        return
    
    send_schedule(uid, "group", db.get_value(uid, "user_group"))
    return

# get schedule by source type - group, lecturer or room
@bot.message_handler(commands=["scheduleby"])
def bot_scheduleby(message) -> None:
    uid = message.chat.id
    uname = message.chat.username
    checkUser(uid, uname)
    log("info", f"/scheduleby - {uid} ({uname})")
    if is_spam_or_ungroupped(uid):
        return

    bot.send_message(uid, "Выберите источник расписания:", reply_markup=kb_source_schedule)
    return

# Group pickup command
@bot.message_handler(commands=['group'])
def group_pickup(message):
    # check user
    checkUser(message.chat.id, message.chat.username)

    log("info", f"/group - {message.chat.id} ({message.chat.username}, {db.get_value(message.chat.id, 'id')})")
    bot.send_message(message.chat.id, 'Выберите свою группу:', reply_markup=kb_schedule)

# Callback query handler (buttons in bot messages)
@bot.callback_query_handler(func=lambda call: True)
def callback_query(call):
    uid = call.message.chat.id
    uname = call.message.chat.username
    cd = call.data

    cq_action = ''
    if   "Выберите свою группу:" in call.message.text:          cq_action = "group_pickup"
    elif "Выберите источник расписания:" in call.message.text:  cq_action = "scheduleby_typeSelect"
    elif "Выберите группу:" in call.message.text:               cq_action = "scheduleby_group"
    elif "Выберите преподавателя:" in call.message.text:        cq_action = "scheduleby_lecturer"
    elif "Выберите аудиторию:" in call.message.text:            cq_action = "scheduleby_room"
    
    # scheduleby source type selected
    if cq_action == "scheduleby_typeSelect":
        bot.delete_message(uid, call.message.id)
        if cd == "group":
            bot.send_message(uid, "Выберите группу:", reply_markup=gm_schedule_source("group"))
        elif cd == "lecturer":
            bot.send_message(uid, "Выберите преподавателя:", reply_markup=gm_schedule_source("lecturer"))
        elif cd == "room":
            bot.send_message(uid, "Выберите аудиторию:", reply_markup=gm_schedule_source("room"))
        return
    # get schedule by group
    elif "scheduleby" in cq_action:
        bot.delete_message(uid, call.message.id)
        source_type = cq_action.split("_")[1]
        send_schedule(uid, source_type, cd)
    
    # Group pickup request
    elif cq_action == 'group_pickup':
        # check if using commands too fast (spamming)
        if is_spam(db.get_value(call.message.chat.id, 'last_group_request_time'), 3):
            log("warn", f"Too many requests from {call.message.chat.id}! ({call.message.chat.username}, {db.get_value(call.message.chat.id, 'id')})")
            bot.send_message(call.message.chat.id, 'Вы слишком часто меняете группу! Подождите немного...')
            # Closing callback query (Unfreezing buttons)
            bot.answer_callback_query(call.id)
            return
        db.update_value(call.message.chat.id, 'last_group_request_time', time.time())
        db.update_value(call.message.chat.id, 'user_group', call.data)
        bot.send_message(call.message.chat.id, f'Вы выбрали группу {db.get_value(call.message.chat.id, 'user_group')}!')
        # Closing callback query (Unfreezing buttons)
        bot.answer_callback_query(call.id)
        # check if user has group
        if db.user_has_group(call.message.chat.id):
            log("ok", f"Set {db.get_value(call.message.chat.id, 'user_group')} group for {call.message.chat.id} ({call.message.chat.username}, {db.get_value(call.message.chat.id, 'id')})")
        # why the fuck it did not set a group :sob:
        else:
            log("fail", f"What the actual fuck happened (group for {call.message.chat.id} is not set after trying to set it) ({call.message.chat.username}, {db.get_value(call.message.chat.id, 'id')})")
    
    # Callback query is empty wtf
    elif cq_action == '':
        bot.answer_callback_query(call.id)
        bot.send_message(call.message.chat.id, 'Не могу выполнить запрос!')
        log("fail", f"Empty callback query action from {call.message.chat.id} ({call.message.chat.username}, {db.get_value(call.message.chat.id, 'id')})")
    # Unknown callback query action (you are cooked up)
    else:
        log("fail", f"Unknown callback query action from {call.message.chat.id} ({call.message.chat.username}, {db.get_value(call.message.chat.id, 'id')})")

# ping command
@bot.message_handler(commands=['ping'])
def bot_ping(message):
    # check user
    checkUser(message.chat.id, message.chat.username)

    log("info", f"/ping - {message.chat.id} ({message.chat.username}, {db.get_value(message.chat.id, 'id')})")
    # check for spam
    if is_spam(db.get_value(message.chat.id, 'last_ping_request_time'), 5):
        log("warn", f"Too many requests from {message.chat.id}! ({message.chat.username}, {db.get_value(message.chat.id, 'id')})")
        bot.send_message(message.chat.id, 'Вы слишком часто используете команду <b>ping</b>!', parse_mode='HTML')
        return
    cur_bot_message = bot.send_message(message.chat.id, f'Бот <b>работает</b>!\n\nТекущее состояние сайта: <b>Ожидание ответа...</b>\n<u>Адрес</u>: <i>{cfg["links"]["index"]}</i>\n<u>Код статуса</u>: <i>---</i>\n<u>Время отклика</u>: <i>-.--- сек.</i>', parse_mode='HTML')
    db.update_value(message.chat.id, 'last_ping_request_time', time.time())
    try:
        # try to get website response
        response = requests.get(f'{cfg["links"]["index"]}', timeout=5)
        # website is working
        bot.edit_message_text(f'Бот <b>работает</b>!\n\nТекущее состояние сайта: <b>Работает!</b>\n<u>Адрес</u>: <i>{cfg["links"]["index"]}</i>\n<u>Код статуса</u>: <i>{response.status_code}</i>\n<u>Время отклика</u>: <i>{round(response.elapsed.microseconds / 1000) / 1000} сек.</i>', message.chat.id, cur_bot_message.id, parse_mode='HTML')
        log("ok", f"/ping - elapsed time: {response.elapsed.microseconds / 1000} ms")
    except Exception as exception:
        if type(exception) == requests.ConnectTimeout:
            # removing useless text
            e = str(exception).split('ConnectionPool(')[1].split('): Max retries')[0]       # host='...', port=...
            timeout = str(exception).split('connect timeout=')[1].removesuffix(')\'))')     # set timeout in seconds
            log("fail", f"Connection timed out ({timeout}): {e}")
        else:
            log("fail", f"/ping - {exception}")
        # website is down
        bot.edit_message_text(f'Бот <b>работает</b>!\n\nТекущее состояние сайта: <b>Не отвечает!</b>\n<u>Адрес</u>: <i>{cfg["links"]["index"]}</i>\n<u>Код статуса</u>: <i>---</i>\n<u>Время отклика</u>: <i>-.--- сек.</i>', message.chat.id, cur_bot_message.id, parse_mode='HTML')

# ADMIN / DEBUG COMMANDS - ONLY WORKS IF SENDER IS IN ADMIN LIST (cfg -> admins)

# announcement command
command_announ = "announcement"
# ex.
# /announcement
# text
# \ANN_END
# INCLUDE
# \MODE_END
# 1234567890

@bot.message_handler(commands=[f'{command_announ}'])
def announcement(message, file_id = ''):
    # check if in admin list
    if (str(message.chat.id) not in cfg["admins"]):
        return
    
    # get text of message
    if (file_id != ''):
        # message has image
        ann_mes = str(message.caption)
        log("trash", f"Announcement image file_id: {file_id}")
    else:
        ann_mes = str(message.text)
    # check receiving mode ( INCLUDE / EXCLUDE )
    if '\\ANN_END\n' not in ann_mes:
        log("fail", "'\\ANN_END\\n' not specified!")
        return
    elif '\\MODE_END\n' not in ann_mes:
        log("fail", "'\\MODE_END\\n' not specified!")
        return

    # get sending mode
    ann_mode = ann_mes.split("\\ANN_END\n")[1].splitlines()[0]
    if ann_mode != "INCLUDE" and ann_mode != "EXCLUDE":
        log("fail", "Invalid mode! must be INCLUDE or EXCLUDE")
        return
    # get IDs of announcement receivers
    ann_ids = ann_mes.split("\\MODE_END\n")[1].splitlines()
    temp_ann_ids = ann_ids
    # get actual message
    ann_mes = ann_mes.removeprefix(f"/{command_announ}\n").split("\\ANN_END")[0].removesuffix("\\ANN_END").strip()
    if ann_mes == "":
        log("fail", "No announcement text found!")
        return

    # update ann_ids list to all known IDs without excluded IDs
    if ann_mode == "EXCLUDE":
        # get all IDs
        ann_ids = db.get_all_values('user_id')
        ann_ids.reverse()
        # format all IDs
        for i in range(len(ann_ids)):
            ann_ids[i] = str(ann_ids[i]).removeprefix('(').removesuffix(',)')

        # remove excluded IDs from list
        for ex_id in temp_ann_ids:
            try:
                ann_ids.remove(ex_id)
            except:
                # excluded ID not found
                log("warn", f"{ex_id} not found in database!")
    
    # log   :exploding_head:
    log("trash", f"Sending an announcement to:\n{str(ann_ids)}")

    # send to all receivers
    for id in ann_ids:
        try:
            # check if message has image
            if (file_id != ''):
                # message has image - send it too
                bot.send_photo(id, file_id, ann_mes, parse_mode='HTML')
            else:
                bot.send_message(id, ann_mes, parse_mode='HTML', disable_web_page_preview=True)
        except:
            # failed to send to some user ( chat not found most likely )
            log("warn", f"Failed to send announcement to {id}")
    
    # distribution complete
    log("ok", f"Sent announcement:\n{ann_mes}")

# handle messages with photos
@bot.message_handler(content_types=['photo'])
def photo_handler(message):
    # announcement with image
    if message.caption and f'/{command_announ}' in message.caption:
        announcement(message, message.photo[-1].file_id)

log("trash", "Bot launched")
# Launching bot polling
bot.polling(timeout=20, long_polling_timeout = 10)

# Stopping bot (there is actually nothing to stop, just close database (useless because program will exit anyway))
db.close()
log("trash", "Bot stopped")
