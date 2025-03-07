import requests, os, datetime, time, sys, logging, dotenv, argparse, toml, subprocess
import telebot as tb
from bs4 import BeautifulSoup
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
from db import database # local class from db.py

# Initializing logger
logger = logging.getLogger(__name__)
logging.basicConfig(filename='log.log',
                    format='%(message)s', 
                    level=logging.INFO)

def log(tag='u', color='w', text='undefined', will_notify=False, post_title='untitled', post_tag='i'):
    # writing in log and printing in console
    colors = {
        'r':'\033[31m', # red
        'g':'\033[32m', # green
        'y':'\033[33m', # yellow
        'b':'\033[36m', # blue
        'w':'\033[90m', # gray
        'o':'\033[93m'  # orange
    }
    tags = {
        't':'start', # start tag
        'g':'group', # group tag
        's':'sched', # schedule tag
        'p':'ping?', # ping tag
        'd':'updtm', # update time tag
        'a':'anncm', # announcement tag
        'e':'error', # error tag
        'w':'warng', # warning tag
        'o':'other', # tag for other information
        'u':'undef'  # undefined tag
    }

    if args.colored:
        output = '\033[90m' + time.asctime() + '\033[0m ' + colors[color] + '[' + tags[tag] + ']\033[0m > ' + text
        print(output)
    else:
        output = '['+ tags[tag] + '] > ' + text
        print(output)
    logger.info(output)

    # send notification if enabled
    if args.notifications and will_notify:
        match post_tag:
            # info
            case 'i':
                post_ntfy('i', post_title, f'{text}', 'l')
            # warning
            case 'w':
                post_ntfy('w', post_title, f'{text}', 'd')
            # error
            case 'e':
                post_ntfy('e', post_title, f'{text}', 'h')

logger.info('-----------------------------------------')

# notifications via ntfy
def post_ntfy(tag='i', title='untitled', text='none', priority='l'):
    global use_ntfy
    tags = {
        'i':'speech_balloon',   # info tag
        'w':'warning',          # warning tag
        'e':'x'                 # error tag
    }
    priorities = {
        'u':'urgent',           # highest priority
        'h':'high',             # high priority
        'd':'default',          # default priority
        'l':'low',              # low priority
        'm':'min'               # lowest priority
    }

    post_req = requests.post(f'https://ntfy.sh/{args.notifications}',
        data=f'{text}',
        headers={
            'Title': f'{title}',
            'Priority': f'{priorities[priority]}',
            'Tags': f'{tags[tag]}'
        })
    # print(post_req.status_code)
    if post_req.status_code != 200:
        use_ntfy = False
        log('e', 'r', f'post_ntfy(): can\'t access \'ntfy.sh/{args.notifications}\' (status code: {post_req.status_code}). Notifications are now disabled.')

# Exception handler
class BotExceptionHandler(tb.ExceptionHandler):
    last_apiexception_time = 0.0
    last_readtimeout_time = 0.0
    def handle(self, exception):
        # API HTTP exception
        if type(exception) == tb.apihelper.ApiTelegramException:
            # get error code
            error_code = str(exception).split('Error code: ')[1].split('. Description')[0]

            # check if 502 or 429 error occurrs again within 20 seconds
            if (error_code == '502' or error_code == '429') and time.time() - self.last_apiexception_time > 20:
                log('e', 'r', f'HTTP request error ({error_code})', True, f'HTTP request returned {error_code}', 'e')
                self.last_apiexception_time = time.time()
            elif (error_code == '502' or error_code == '429'):
                log('e', 'w', f'HTTP request error ({error_code})')
            # other tg api exceptions
            else:
                log('e', 'r', f'{exception}', True, f'telegram api error ({error_code})', 'e')
        # connection timeout exception
        elif type(exception) == requests.ConnectTimeout:
            # removing useless text
            e = str(exception).split('ConnectionPool(')[1].split('): Max retries')[0]       # host='...', port=...
            timeout = str(exception).split('connect timeout=')[1].removesuffix(')\'))')     # set timeout in seconds
            log('e', 'r', f'connection timed out ({timeout}) // {e}')
        # read timeout exception
        elif type(exception) == requests.ReadTimeout:
            # check if read timeout error occurrs again within 60 seconds
            if time.time() - self.last_readtimeout_time > 60:
                # removing useless text
                e = str(exception).split('ConnectionPool(')[1].split('): Read')[0]          # host='...', port=...
                timeout = str(exception).split('read timeout=')[1].removesuffix(')')        # set timeout in seconds
                log('e', 'r', f'read timed out ({timeout}): {e}', True, f'read timed out ({timeout}) // {e}')
                self.last_readtimeout_time = time.time()
            else:
                log('e', 'w', 'read timed out again')
        # telegram api HTTPConnectionPool error (network is unreachable)
        elif str(exception).count(f"{TOKEN}") > 0:
            e = str(exception)
            e = e.replace(f"{TOKEN}", "<BOT_TOKEN>")
            log('e', 'r', f"{e}", True, "Telegram API HTTPConnectionPool", 'e')
        # other exceptions
        # if you got these you probably cooked up
        else:
            log('e', 'r', f'"{exception}", exception type: {type(exception)}', True, 'you cooked', 'e')
        return exception

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
arg_parser.add_argument('-f', '--config', help='path to config file')

# parse arguments and do somenthing with them
args = arg_parser.parse_args()

# use notifications if -n/--notifications argument provided
use_ntfy = False
if args.notifications:
    use_ntfy = True

# load config
# use config provided via args
if args.config:
    cfg = toml.load(args.config)
# use default config file
elif os.path.exists('config.toml'):
    cfg = toml.load('config.toml')
# create new config file
else:
    log('w', 'o', 'config.toml not found! creating new config file and using it for now')
    conf_default = {
        "groups": {
            "url_main":     "http://94.72.18.202:8083/cg.htm",
            "url_start":    "http://94.72.18.202:8083/"
        },
        "lists": {
            "admins": []
        },
        "ping": {
            "url": "http://94.72.18.202:8083/index.htm"
        }
    }
    with open('config.toml', 'w', encoding='utf-8') as file:
        toml.dump(conf_default, file)
    cfg = toml.load('config.toml')

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
    log('e', 'r', 'no token given. aborting...')
    exit(1)
# initialize bot
try:
    bot = tb.TeleBot(TOKEN, exception_handler=BotExceptionHandler())
except Exception as e:
    log('e', 'r', f'can\'t initialize bot: {e}. aborting...')
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
# url_dict contains relative links that are used to 
# get full url of group schedule
# parse groups into toml file and use it as groups url dictionary
log('o', 'w', 'running group parser...')
group_parser = subprocess.run([sys.executable, "group_parser.py"])
if group_parser.returncode == 0:
    log('o', 'w', 'successfully parsed groups into groups.toml')
else:
    log('e', 'r', f'group parser returned error code {group_parser.returncode}. aborting...')
    exit(group_parser.returncode)

url_dict = toml.load('groups.toml')["groups"]
groups_count = len(url_dict)

# get full link for schedule request
def get_url(group):
    return cfg["groups"]["url_start"] + url_dict[group]

# i hope u can guess what does this method do :)
# maybe i will add more comments to this (i am lazy)
def get_schedule(url, group):
    result = 'Расписание для группы <b>' + group + '</b>\n'
    # try to connect to website
    response = requests.get(url, timeout=5)
    if response.status_code == 200:
        # get all html code
        html_content = response.content
        soup = BeautifulSoup(html_content, 'html.parser')

        is_monday = False
        td_next_is_lesson_time = False
        table = soup.find('table', class_='inf')
        for tr in table.find_all('tr'):
            temp_subgroup_found = False
            subgroup = ''
            for td in tr.find_all('td'):
                has_subgroup = False

                ################# SUBGROUP #################
                if not temp_subgroup_found and tr.find('td', class_='nul') != None:
                    has_subgroup = True
                    temp_tr = tr.find('td', class_='ur')
                    if temp_tr != None:
                        if temp_tr.find_next_sibling('td', class_='nul') != None:
                            subgroup = ' <b>(1-я подгруппа)</b>'
                        else:
                            subgroup = ' <b>(2-я подгруппа)</b>'
                        temp_subgroup_found = True
                
                #################  LESSON  #################
                if td.find('a', class_='z1') != None:
                    if not is_monday:
                        result += '<u>' + cur_lesson_number + ' Пара' + '</u> - <i>' + bells[str(cur_lesson_number + ' Пара')] + '</i>'
                    else:
                        result += '<u>' + cur_lesson_number + ' Пара' + '</u> - <i>' + bells_monday[str(cur_lesson_number + ' Пара')] + '</i>'
                    result += ' - ' + td.find('a', class_='z1').text + subgroup
                    if td.find('a', class_='z2') != None:
                        result +=  ' - <i>' + td.find('a', class_='z2').text + '</i>'
                    else:
                        result += ' - <i>Кабинет не указан</i>'
                    result += '\n'
                
                # don't even ask why is this so shitty
                ##################  DAYS  ##################
                if td['class'][0] == 'hd':
                    if td.text.find('Пн') >= 0:
                        result += '\n' + '--------------------------\n\n' + td.text.removesuffix('Пн') + ' - <b>Понедельник</b>\n\n<u>Подъём флага</u> - <i>8:15-8:25</i>\n'
                        is_monday = True
                    elif td.text.find('Вт') >= 0:
                        result += '\n' + '--------------------------\n\n' + td.text.removesuffix('Вт') + ' - <b>Вторник</b>\n\n'
                        is_monday = False
                    elif td.text.find('Ср') >= 0:
                        result += '\n' + '--------------------------\n\n' + td.text.removesuffix('Ср') + ' - <b>Среда</b>\n\n'
                    elif td.text.find('Чт') >= 0:
                        result += '\n' + '--------------------------\n\n' + td.text.removesuffix('Чт') + ' - <b>Четверг</b>\n\n'
                    elif td.text.find('Пт') >= 0:
                        result += '\n' + '--------------------------\n\n' + td.text.removesuffix('Пт') + ' - <b>Пятница</b>\n\n'
                    elif td.text.find('Сб') >= 0:
                        result += '\n' + '--------------------------\n\n' + td.text.removesuffix('Сб') + ' - <b>Суббота</b>\n'

                # get number of current lesson
                if td.text == '1' or td.text == '2' or td.text == '3' or td.text == '4' or td.text == '5' or td.text == '6' or td.text == '7':
                    cur_lesson_number = td.text
        # last schedule update time
        updatetime_group = response.headers.get('Last-Modified')
        updatetime_group_dt = datetime.datetime.strptime(updatetime_group, '%a, %d %b %Y %H:%M:%S GMT')
        updatetime_group_dt += datetime.timedelta(hours=2)
        result += '\n--------------------------\n<i>Последнее обновление: ' + updatetime_group_dt.strftime('%d.%m.%Y в %H:%M:%S') + '</i>'
    else:
        log('s', 'r', f'failed to fetch website! status code: {response.status_code}') # i might just delete this whole if-else section and replace it with some good readable code 8) 
        raise
    return result

# generate markup keyboard for group selection
def gm_groups():
    markup = InlineKeyboardMarkup()
    markup.row_width = 3
    group_keys = list(url_dict.keys())
    IKB_list = list()

    for n in range(len(group_keys)):
        IKB_list.append(InlineKeyboardButton(group_keys[n], callback_data=group_keys[n]))
    
    markup.add(*IKB_list)
    return markup
kb_markup = gm_groups()

# check spam for certain commands
def is_spam(prev_use_time: float, cooldown: float):
    return (time.time() - prev_use_time) < cooldown

# check user
def checkUser(uid : str, uname : str):
    # check if user already exists
    if db.user_exists(uid):
        if db.get_value(uid, 'username') != uname:
            db.update_value(uid, 'username', uname)
            log('o', 'w', f'updated {uid} username: {uname}')
    # otherwise add new user to database
    else:
        db.add_user(uid, uname)
        log('o', 'y', f'added {uid} ({uname}) to database')

# Start message command
@bot.message_handler(commands=['start'])
def start(message):
    log('t', 'b', f'request from {message.chat.id} ({message.chat.username})')
    bot.send_message(message.chat.id, 'Привет, это бот для просмотра расписания КИТиС!\nДля начала выбери свою группу с помощью команды /group, а после этого используй команду /schedule, чтобы посмотреть расписание выбранной группы!')
    # check user
    checkUser(message.chat.id, message.chat.username)

# Schedule command
@bot.message_handler(commands=['schedule'])
def schedule(message):
    # check user
    checkUser(message.chat.id, message.chat.username)

    log('s', 'b', f'request from {message.chat.id} ({message.chat.username}, {db.get_value(message.chat.id, 'id')})')
    
    # check if group is set
    if not db.get_value(message.chat.id, 'user_group'):
        log('s', 'y', f'request failed: {message.chat.id} group is empty! ({message.chat.username}, {db.get_value(message.chat.id, 'id')})')
        bot.send_message(message.chat.id, 'Сначала выберите группу! - /group')
        return
    # check if using commands too fast (spamming)
    if is_spam(db.get_value(message.chat.id, 'last_schedule_request_time'), 5):
        log('s', 'y', f'request failed: too many requests from {message.chat.id}! ({message.chat.username}, {db.get_value(message.chat.id, 'id')})')
        bot.send_message(message.chat.id, 'Вы слишком часто запрашиваете расписание! Подождите немного и попробуйте снова...')
        return
    
    request_notification = bot.send_message(message.chat.id, 'Запрашиваю данные...\n\n<i>Если Вы видите этот текст больше 10 секунд, значит скорее всего что-то пошло не так...</i>', parse_mode='HTML')
    
    # try to get and send schedule
    group = db.get_value(message.chat.id, 'user_group')
    try:
        result = get_schedule(get_url(group), group)
        bot.edit_message_text(result, message.chat.id, request_notification.id, parse_mode='HTML')
        db.update_value(message.chat.id, 'last_schedule_request_time', time.time())
        log('s', 'g', f'sent schedule to {message.chat.id} ({message.chat.username}, {db.get_value(message.chat.id, 'id')})')
    except Exception as e:
        bot.edit_message_text('Не удалось получить расписание! Попробуйте позже...', message.chat.id, request_notification.id)
        raise

# One time schedule command (scheduleother)
@bot.message_handler(commands=['scheduleother'])
def scheduleother(message):
    # check user
    checkUser(message.chat.id, message.chat.username)

    log('s', 'b', f'request from {message.chat.id} ({message.chat.username}, {db.get_value(message.chat.id, 'id')})')
    # check if using commands too fast (spamming)
    if is_spam(db.get_value(message.chat.id, 'last_schedule_request_time'), 5):
        log('s', 'y', f'request failed: too many requests from {message.chat.id}! ({message.chat.username}, {db.get_value(message.chat.id, 'id')})')
        bot.send_message(message.chat.id, 'Вы слишком часто запрашиваете расписание! Подождите немного и попробуйте снова...')
        return
    bot.send_message(message.chat.id, 'Выберите группу (группа не сохраняется):', reply_markup=kb_markup)
    db.update_value(message.chat.id, 'last_schedule_request_time', time.time())

# Group pickup command
@bot.message_handler(commands=['group'])
def group_pickup(message):
    # check user
    checkUser(message.chat.id, message.chat.username)

    log('g', 'b', f'request from {message.chat.id} ({message.chat.username}, {db.get_value(message.chat.id, 'id')})')
    bot.send_message(message.chat.id, 'Выберите группу:', reply_markup=kb_markup)

# Callback query handler (buttons in bot messages)
@bot.callback_query_handler(func=lambda call: True)
def callback_query(call):
    cq_action = ''
    if 'группа не сохраняется' in call.message.text:
        cq_action = 'sched_other'
    elif 'Выберите группу:' in call.message.text:
        cq_action = 'group_pickup'
    
    # Group pickup request
    if cq_action == 'group_pickup':
        # check if using commands too fast (spamming)
        if is_spam(db.get_value(call.message.chat.id, 'last_group_request_time'), 3):
            log('g', 'y', f'request failed: too many requests from {call.message.chat.id}! ({call.message.chat.username}, {db.get_value(call.message.chat.id, 'id')})')
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
            log('g', 'g', f'set {db.get_value(call.message.chat.id, 'user_group')} group for {call.message.chat.id} ({call.message.chat.username}, {db.get_value(call.message.chat.id, 'id')})')
        # why the fuck it did not set a group :sob:
        else:
            log('g', 'r', f'what the actual fuck happened (group for {call.message.chat.id} is not set after trying to set it) ({call.message.chat.username}, {db.get_value(call.message.chat.id, 'id')})')
    
    # Schedule request (one-time)
    elif cq_action == 'sched_other':
        temp_group = call.data
        # Closing callback query (Unfreezing buttons)
        bot.answer_callback_query(call.id)

        bot.delete_message(call.message.chat.id, call.message.id)
        request_notification = bot.send_message(call.message.chat.id, 'Запрашиваю данные...\n\n<i>Если Вы видите этот текст больше 10 секунд, значит скорее всего что-то пошло не так...</i>', parse_mode='HTML')

        # try to get schedule
        try:
            result = get_schedule(get_url(temp_group), temp_group)
            bot.edit_message_text(result, call.message.chat.id, request_notification.id, parse_mode='HTML')
            log('s', 'g', f'sent {temp_group} schedule to {call.message.chat.id} ({call.message.chat.username}, {db.get_value(call.message.chat.id, 'id')})')
        except Exception as e:
            bot.edit_message_text('Не удалось получить расписание! Попробуйте позже...', call.message.chat.id, request_notification.id)
            raise
    
    # Callback query is empty wtf
    elif cq_action == '':
        bot.answer_callback_query(call.id)
        bot.send_message(call.message.chat.id, 'Не могу выполнить запрос!')
        log('u', 'y', f'empty callback query action from {call.message.chat.id} ({call.message.chat.username}, {db.get_value(call.message.chat.id, 'id')})')
    # Unknown callback query action (you are cooked up)
    else:
        log('u', 'y', f'unknown callback query action from {call.message.chat.id} ({call.message.chat.username}, {db.get_value(call.message.chat.id, 'id')})')

# ping command
@bot.message_handler(commands=['ping'])
def bot_ping(message):
    # check user
    checkUser(message.chat.id, message.chat.username)

    log('p', 'b', f'request from {message.chat.id} ({message.chat.username}, {db.get_value(message.chat.id, 'id')})')
    # check for spam
    if is_spam(db.get_value(message.chat.id, 'last_ping_request_time'), 5):
        log('p', 'y', f'request failed: too many requests from {message.chat.id}! ({message.chat.username}, {db.get_value(message.chat.id, 'id')})')
        bot.send_message(message.chat.id, 'Вы слишком часто используете команду <b>ping</b>!', parse_mode='HTML')
        return
    cur_bot_message = bot.send_message(message.chat.id, f'Бот <b>работает</b>!\n\nТекущее состояние сайта: <b>Ожидание ответа...</b>\n<u>Адрес</u>: <i>{cfg["ping"]["url"]}</i>\n<u>Код статуса</u>: <i>---</i>\n<u>Время отклика</u>: <i>-.--- сек.</i>', parse_mode='HTML')
    db.update_value(message.chat.id, 'last_ping_request_time', time.time())
    try:
        # try to get website response
        response = requests.get(f'{cfg["ping"]["url"]}', timeout=5)
        # website is working
        bot.edit_message_text(f'Бот <b>работает</b>!\n\nТекущее состояние сайта: <b>Работает!</b>\n<u>Адрес</u>: <i>{cfg["ping"]["url"]}</i>\n<u>Код статуса</u>: <i>{response.status_code}</i>\n<u>Время отклика</u>: <i>{round(response.elapsed.microseconds / 1000) / 1000} сек.</i>', message.chat.id, cur_bot_message.id, parse_mode='HTML')
        log('p', 'g', f'success: elapsed time - {response.elapsed.microseconds / 1000} ms')
    except Exception as exception:
        if type(exception) == requests.ConnectTimeout:
            # removing useless text
            e = str(exception).split('ConnectionPool(')[1].split('): Max retries')[0]       # host='...', port=...
            timeout = str(exception).split('connect timeout=')[1].removesuffix(')\'))')     # set timeout in seconds
            log('p', 'r', f'connection timed out ({timeout}): {e}')
        else:
            log('p', 'r', f'request failed: {exception}')
        # website is down
        bot.edit_message_text(f'Бот <b>работает</b>!\n\nТекущее состояние сайта: <b>Не отвечает!</b>\n<u>Адрес</u>: <i>{cfg["ping"]["url"]}</i>\n<u>Код статуса</u>: <i>---</i>\n<u>Время отклика</u>: <i>-.--- сек.</i>', message.chat.id, cur_bot_message.id, parse_mode='HTML')

# ADMIN / DEBUG COMMANDS - ONLY WORKS IF SENDER IS IN ADMIN LIST (cfg -> lists -> admins)

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
    if (str(message.chat.id) not in cfg["lists"]["admins"]):
        return
    
    # get text of message
    if (file_id != ''):
        # message has image
        ann_mes = str(message.caption)
        log('a', 'w', f'announcement image file_id: {file_id}')
    else:
        ann_mes = str(message.text)
    # check receiving mode ( INCLUDE / EXCLUDE )
    if '\\ANN_END\n' not in ann_mes:
        log('a', 'r', '\'\\ANN_END\\n\' not specified!')
        return
    elif '\\MODE_END\n' not in ann_mes:
        log('a', 'r', '\'\\MODE_END\\n\' not specified!')
        return

    # get sending mode
    ann_mode = ann_mes.split("\\ANN_END\n")[1].splitlines()[0]
    if ann_mode != "INCLUDE" and ann_mode != "EXCLUDE":
        log('a', 'r', 'invalid mode! must be INCLUDE or EXCLUDE')
        return
    # get IDs of announcement receivers
    ann_ids = ann_mes.split("\\MODE_END\n")[1].splitlines()
    temp_ann_ids = ann_ids
    # get actual message
    ann_mes = ann_mes.removeprefix(f"/{command_announ}\n").split("\\ANN_END")[0].removesuffix("\\ANN_END").strip()
    if ann_mes == "":
        log('a', 'r', 'no announcement text found!')
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
                log('a', 'y', f'user {ex_id} not found in database!')
    
    # log   :exploding_head:
    log('a', 'w', f'sending an announcement to {str(ann_ids)}')

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
            log('a', 'r', f'failed to send announcement to {id}')
    
    # distribution complete
    log('a', 'g', f'sent announcement:\n{ann_mes}')

# handle messages with photos
@bot.message_handler(content_types=['photo'])
def photo_handler(message):
    # announcement with image
    if message.caption and f'/{command_announ}' in message.caption:
        announcement(message, message.photo[-1].file_id)

log('o', 'w', 'bot launched')
# Launching bot polling
bot.polling(timeout=20, long_polling_timeout = 10)

# Stopping bot (there is actually nothing to stop, just close database (useless because program will exit anyway))
# get notification that bot stopped working for some reason
if use_ntfy:
    post_ntfy('w', 'stopped', 'bot stopped working.\ncheck log.log for more information.', 'h')

log('o', 'w', 'bot stopped working')
log('o', 'w', 'closing database...')
db.close()
log('o', 'w', 'finished')
