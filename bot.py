import requests, os, time, sys, logging, dotenv
import telebot as tb
from bs4 import BeautifulSoup
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
from db import database # local class from db.py

# Initializing logger
logger = logging.getLogger(__name__)
logging.basicConfig(filename='log.log',
                    format='%(message)s', 
                    level=logging.INFO)

def log(tag='u', color='b', text='undefined', will_notify=False, post_title='untitled', post_tag='i'):
    # writing in log and printing in console
    colors = {
        'r':'\033[31m', # red
        'g':'\033[32m', # green
        'y':'\033[33m', # yellow
        'b':'\033[36m', # blue
        'w':'\033[90m'  # gray
    }
    tags = {
        't':'start', # start tag
        'g':'group', # group tag
        's':'sched', # schedule tag
        'p':'ping?', # ping tag
        'a':'anncm', # announcement tag
        'e':'error', # important error tag
        'o':'other', # tag for other information
        'u':'undef'  # undefined tag
    }

    if args_colored:
        output = '\033[90m' + time.asctime() + '\033[0m ' + colors[color] + '[' + tags[tag] + ']\033[0m > ' + text
        print(output)
    else:
        output = '['+ tags[tag] + '] > ' + text
        print(output)
    logger.info(output)

    # send notification if enabled
    if args_notify and will_notify:
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
post_topic = ''
def post_ntfy(tag='i', title='untitled', text='none', priority='l'):
    global args_notify
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

    post_req = requests.post(f'https://ntfy.sh/{post_topic}',
        data=f'{text}',
        headers={
            'Title': f'{title}',
            'Priority': f'{priorities[priority]}',
            'Tags': f'{tags[tag]}'
        })
    print(post_req.status_code)
    if post_req.status_code != 200:
        args_notify = False
        log('e', 'r', f'exception at post_ntfy() // can\'t access \'ntfy.sh/{post_topic}\' (status code: {post_req.status_code}). Notifications are now disabled.')

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
                log('e', 'r', f'read timed out ({timeout}) // {e}', True, f'read timed out ({timeout}) // {e}')
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
            log('e', 'r', f'error: {exception}, type: {type(exception)}', True, 'you cooked', 'e')
        return exception

# Arguments and flags
args_token = ''         # -t or --token
args_colored = False    # -c or --colored
args_notify = False     # -n or --notifications

# list of all existing flags
args_list = {'-h', '--help', '-t', '--token', '-c', '--colored'}

sys.argv.remove(sys.argv[0]) # Removing filename from arguments list

# help flag
if '-h' in sys.argv or '--help' in sys.argv:
    print('-h or --help\t\t- show usage help\n-c or --colored\t\t- sets colored log output (cat)\n-t or --token\t\t- set bot token (following argument is token itself)\n-n or --notifications\t- get error notifications (following argument is ntfy.sh topic, eg. \'kitis_bot_notifications\' without quotes)')
    exit(0)

# token flag
if '-t' in sys.argv:
    try:
        args_token = sys.argv[sys.argv.index('-t') + 1]
        sys.argv.remove(sys.argv[sys.argv.index('-t') + 1])
        sys.argv.remove('-t')
    except Exception as e:
        log('e', 'r', f'exception at \'-t in sys.argv\' // {e}')
        exit(1)
elif '--token' in sys.argv:
    try:
        args_token = sys.argv[sys.argv.index('--token') + 1]
        sys.argv.remove(sys.argv[sys.argv.index('--token') + 1])
        sys.argv.remove('--token')
    except Exception as e:
        log('e', 'r', f'exception at \'--token in sys.argv\' // {e}')
        exit(1)

# colored log flag
if '-c' in sys.argv or '--colored' in sys.argv:
    args_colored = True
    if '-c' in sys.argv:
        sys.argv.remove('-c')
    elif '--colored' in sys.argv:
        sys.argv.remove('--colored')

# notifications flag
if '-n' in sys.argv:
    try:
        args_notify = True
        post_topic = sys.argv[sys.argv.index('-n') + 1]
        sys.argv.remove(sys.argv[sys.argv.index('-n') + 1])
        sys.argv.remove('-n')
    except Exception as e:
        log('e', 'r', f'exception at \'-n in sys.argv\' // {e}')
        exit(1)
elif '--notifications' in sys.argv:
    try:
        args_notify = True
        post_topic = sys.argv[sys.argv.index('--notifications') + 1]
        sys.argv.remove(sys.argv[sys.argv.index('--notifications') + 1])
        sys.argv.remove('--notifications')
    except Exception as e:
        log('e', 'r', f'exception at \'--notifications in sys.argv\' // {e}')
        exit(1)

# check for unknown arguments
if len(sys.argv) > 0 and not sys.argv[0] in args_list:
    log('e', 'r', f'exception: unknown argument \'{sys.argv[0]}\'. aborting...')
    exit(1)

# load .env file if present
dotenv.load_dotenv()
# get token from argument if present
if args_token != '':
    TOKEN = args_token
# get token from .env file if present
elif os.getenv('TOKEN'):
    TOKEN = os.getenv('TOKEN')
# no token given -> abort
else:
    log('e', 'r', 'error: no token given. aborting...')
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
# every link for group schedule contain a specific number in it
# eg. for 'http://94.72.18.202:8083/raspisanie/www/cg237.htm' that number is 237
# so there is a dictionary with all groups and numbers for them
url_dict = { 
        'СОД23-1':'130',
        'СОД23-2К':'131',
        'СОД24-1':'227',
        'СОД24-2К':'228',
        'С21-1':'140',
        'С21-2':'141',
        'С21-4К':'143',
        'С22-1':'145',
        'С22-2':'146',
        'С22-3К':'147',
        'С23-1':'149',
        'С23-2':'150',
        'С23-3К':'151',
        'С24-1':'229',
        'С24-2':'231',
        'С24-3К':'230',
        'УМД 22-1':'154',
        'УМД23-1':'155',
        'УМД24-1':'233',
        'ИМс24-1':'244',
        'СА21-1':'158',
        'СА21-2К':'159',
        'СА22-1':'160',
        'СА22-2':'161',
        'СА23-1':'162',
        'СА23-2':'163',
        'СА24-1':'234',
        'СА24-2':'235',
        'ИСа 22-1':'164',
        'ИСа23-1':'165',
        'ИСа24-1':'239',
        'ИСп 21-1':'166',
        'ИСп 21-2К':'167',
        'ИСп 22-1':'168',
        'ИСп23-1':'173',
        'ИСп23-2К':'174',
        'ИСп24-1':'237',
        'ИСп24-2К':'240',
        'ИСр 22-1':'177',
        'ИСр23-1':'178',
        'ИСр24-1':'241',
        'ИСс 22-1':'179',
        'ИСс24-1':'238',
        'СВ22-1К':'181',
        'СВ23-1':'182',
        'СВ23-2К':'183',
        'СВ24-1':'242',
        'СВ24-2К':'245',
        'М22-1':'186',
        'М23-1':'187',
        'М24-1':'243',
}
groups_count = len(url_dict)

cq_action = 'none' # action id for callback query
cur_bot_message = tb.types.Message # last message bot sent (for editing or deleting message)

# get full link for schedule request
def get_url(group):
    url = 'http://94.72.18.202:8083/raspisanie/www/cg'
    url += url_dict[group] + '.htm'
    return url

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
        result += '\n<i>' + soup.find('div', class_='ref').text.removeprefix(' ').removesuffix(' ') + '</i>'
    else:
        log('s', 'r', f'error: failed to fetch website! // status code: {response.status_code}') # i might just delete this whole if-else section and replace it with some good readable code 8) 
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

# Start message command
@bot.message_handler(commands=['start'])
def start(message):
    log('t', 'b', f'start received // sender id: {message.chat.id}, username: {message.chat.username}')
    bot.send_message(message.chat.id, 'Привет, это бот для просмотра расписания КИТиС!\nДля начала выбери свою группу с помощью команды /group, а после этого используй команду /schedule, чтобы посмотреть расписание выбранной группы!')

    # check if user exists
    if db.user_exists(message.chat.id):
        log('t', 'g', f'user exists // id: {message.chat.id}, username: {message.chat.username}, db_id: {db.get_value(message.chat.id, 'id')}')
    # add user to database if there is not
    else:
        log('t', 'y', f'user is not in database // id: {message.chat.id}, username: {message.chat.username}')
        db.add_user(message.chat.id, message.chat.username)
        log('t', 'g', f'added user to database // id: {message.chat.id}, username: {message.chat.username}, db_id: {db.get_value(message.chat.id, 'id')}')

# Schedule command
@bot.message_handler(commands=['schedule'])
def schedule(message):
    log('s', 'b', f'schedule request // id: {message.chat.id}, username: {message.chat.username}, db_id: {db.get_value(message.chat.id, 'id')}')
    
    # check if group is set
    if not db.get_value(message.chat.id, 'user_group'):
        log('s', 'y', f'request rejected: group is empty! // id: {message.chat.id}, username: {message.chat.username}, db_id: {db.get_value(message.chat.id, 'id')}')
        bot.send_message(message.chat.id, 'Сначала выберите группу! - /group')
        return
    # check if using commands too fast (spamming)
    if is_spam(db.get_value(message.chat.id, 'last_schedule_request_time'), 5):
        log('s', 'y', f'request rejected: too many requests in 5 seconds! // id: {message.chat.id}, username: {message.chat.username}, db_id: {db.get_value(message.chat.id, 'id')}')
        bot.send_message(message.chat.id, 'Вы слишком часто запрашиваете расписание! Подождите немного и попробуйте снова...')
        return
    
    request_notification = bot.send_message(message.chat.id, 'Запрашиваю данные...\n\n<i>Если Вы видите этот текст больше 10 секунд, значит скорее всего что-то пошло не так...</i>', parse_mode='HTML')
    
    # try to get and send schedule
    group = db.get_value(message.chat.id, 'user_group')
    try:
        result = get_schedule(get_url(group), group)
        bot.edit_message_text(result, message.chat.id, request_notification.id, parse_mode='HTML')
        db.update_value(message.chat.id, 'last_schedule_request_time', time.time())
        log('s', 'g', f'sent schedule // id: {message.chat.id}, username: {message.chat.username}, db_id: {db.get_value(message.chat.id, 'id')}')
    except Exception as e:
        bot.edit_message_text('Не удалось получить расписание! Попробуйте позже...', message.chat.id, request_notification.id)
        raise

# One time schedule command (scheduleother)
@bot.message_handler(commands=['scheduleother'])
def scheduleother(message):
    global cq_action, cur_bot_message
    
    log('s', 'b', f'schedule request (one-time) // id: {message.chat.id}, username: {message.chat.username}, db_id: {db.get_value(message.chat.id, 'id')}')
    # check if using commands too fast (spamming)
    if is_spam(db.get_value(message.chat.id, 'last_schedule_request_time'), 5):
        log('s', 'y', f'request rejected (one-time): too many requests in 5 seconds! // id: {message.chat.id}, username: {message.chat.username}, db_id: {db.get_value(message.chat.id, 'id')}')
        bot.send_message(message.chat.id, 'Вы слишком часто запрашиваете расписание! Подождите немного и попробуйте снова...')
        return
    cur_bot_message = bot.send_message(message.chat.id, 'Выберите группу (группа не сохраняется):', reply_markup=kb_markup)
    db.update_value(message.chat.id, 'last_schedule_request_time', time.time())
    cq_action = 'sched_other'

# Group pickup command
@bot.message_handler(commands=['group'])
def group_pickup(message):
    global cq_action

    log('g', 'b', f'group pickup request // id: {message.chat.id}, username: {message.chat.username}, db_id: {db.get_value(message.chat.id, 'id')}')
    bot.send_message(message.chat.id, 'Выберите группу:', reply_markup=kb_markup)
    cq_action = 'group_pickup'

# Callback query handler (buttons in bot messages)
@bot.callback_query_handler(func=lambda call: True)
def callback_query(call):
    global cq_action
    # Group pickup request
    if cq_action == 'group_pickup':
        # check if using commands too fast (spamming)
        if is_spam(db.get_value(call.message.chat.id, 'last_group_request_time'), 3):
            log('g', 'y', f'request rejected: too many requests in 3 seconds! // id: {call.message.chat.id}, username: {call.message.chat.username}, db_id: {db.get_value(call.message.chat.id, 'id')}')
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
            log('g', 'g', f'picked group {db.get_value(call.message.chat.id, 'user_group')} // id: {call.message.chat.id}, username: {call.message.chat.username}, db_id: {db.get_value(call.message.chat.id, 'id')}')
        # why the fuck it did not set a group :sob:
        else:
            log('g', 'r', f'what the actual fuck happened (group is not set after trying to set it) // id: {call.message.chat.id}, username: {call.message.chat.username}, db_id: {db.get_value(call.message.chat.id, 'id')}')
        cq_action = 'group_pickup'
    
    # Schedule request (one-time)
    elif cq_action == 'sched_other':
        temp_group = call.data
        # Closing callback query (Unfreezing buttons)
        bot.answer_callback_query(call.id)

        bot.delete_message(call.message.chat.id, cur_bot_message.id)
        request_notification = bot.send_message(call.message.chat.id, 'Запрашиваю данные...\n\n<i>Если Вы видите этот текст больше 10 секунд, значит скорее всего что-то пошло не так...</i>', parse_mode='HTML')

        # try to get schedule
        try:
            result = get_schedule(get_url(temp_group), temp_group)
            bot.edit_message_text(result, call.message.chat.id, request_notification.id, parse_mode='HTML')
            log('s', 'g', f'sent schedule (one-time), group {temp_group} // id: {call.message.chat.id}, username: {call.message.chat.username}, db_id: {db.get_value(call.message.chat.id, 'id')}')
            cq_action = 'group_pickup'
        except Exception as e:
            bot.edit_message_text('Не удалось получить расписание! Попробуйте позже...', call.message.chat.id, request_notification.id)
            cq_action = 'group_pickup'
            raise
    
    # Callback query is empty wtf
    elif cq_action == 'none':
        bot.answer_callback_query(call.id)
        bot.send_message(call.message.chat.id, 'Не могу выполнить запрос!')
        log('u', 'y', f'empty callback query action // id: {call.message.chat.id}, username: {call.message.chat.username}, db_id: {db.get_value(call.message.chat.id, 'id')}')
    # Unknown callback query action (you are cooked up)
    else:
        log('u', 'y', f'unknown callback query action // id: {call.message.chat.id}, username: {call.message.chat.username}, db_id: {db.get_value(call.message.chat.id, 'id')}')

# ping command
@bot.message_handler(commands=['ping'])
def bot_ping(message):
    log('p', 'b', f'ping request // id: {message.chat.id}, username: {message.chat.username}, db_id: {db.get_value(message.chat.id, 'id')}')
    # check for spam
    if is_spam(db.get_value(message.chat.id, 'last_ping_request_time'), 5):
        log('p', 'y', f'request rejected: too many requests in 5 seconds! // id: {message.chat.id}, username: {message.chat.username}, db_id: {db.get_value(message.chat.id, 'id')}')
        bot.send_message(message.chat.id, 'Вы слишком часто используете команду <b>ping</b>!', parse_mode='HTML')
        return
    cur_bot_message = bot.send_message(message.chat.id, f'Бот <b>работает</b>!\n\nТекущее состояние сайта: <b>Ожидание ответа...</b>\n<u>Адрес</u>: <i>http://94.72.18.202:8083/raspisanie/www/index.htm</i>\n<u>IP</u>: <i>94.72.18.202</i>\n<u>Порт</u>: <i>8083</i>\n<u>Код статуса</u>: <i>---</i>\n<u>Время отклика</u>: <i>-.--- сек.</i>', parse_mode='HTML')
    db.update_value(message.chat.id, 'last_ping_request_time', time.time())
    try:
        # try to get website response
        response = requests.get('http://94.72.18.202:8083/raspisanie/www/', timeout=5)
        # website is working
        bot.edit_message_text(f'Бот <b>работает</b>!\n\nТекущее состояние сайта: <b>Работает!</b>\n<u>Адрес</u>: <i>http://94.72.18.202:8083/raspisanie/www/index.htm</i>\n<u>IP</u>: <i>94.72.18.202</i>\n<u>Порт</u>: <i>8083</i>\n<u>Код статуса</u>: <i>{response.status_code}</i>\n<u>Время отклика</u>: <i>{round(response.elapsed.microseconds / 1000) / 1000} сек.</i>', message.chat.id, cur_bot_message.id, parse_mode='HTML')
        log('p', 'g', f'successfully pinged website! // status code: {response.status_code}, elapsed time: {response.elapsed.microseconds / 1000} ms')
    except Exception as exception:
        if type(exception) == requests.ConnectTimeout:
            # removing useless text
            e = str(exception).split('ConnectionPool(')[1].split('): Max retries')[0]       # host='...', port=...
            timeout = str(exception).split('connect timeout=')[1].removesuffix(')\'))')     # set timeout in seconds
            log('p', 'r', f'connection timed out ({timeout}) // {e}')
        else:
            log('p', 'r', f'exception at bot_ping() // {exception}')
        # website is down
        bot.edit_message_text(f'Бот <b>работает</b>!\n\nТекущее состояние сайта: <b>Не отвечает!</b>\n<u>Адрес</u>: <i>http://94.72.18.202:8083/raspisanie/www/index.htm</i>\n<u>IP</u>: <i>94.72.18.202</i>\n<u>Порт</u>: <i>8083</i>\n<u>Код статуса</u>: <i>---</i>\n<u>Время отклика</u>: <i>-.--- сек.</i>', message.chat.id, cur_bot_message.id, parse_mode='HTML')

# ADMIN / DEBUG COMMANDS - ONLY WORKS IF SENDER IS IN ADMIN LIST
# read admin list from file
admin_list = []
if os.path.exists('admin.list'):
    with open('admin.list', 'r', encoding='utf-8') as file:
        admin_list = file.read().splitlines()
# admin.list file doesn't exist
else:
    log('e', 'r', "you must create 'admin.list' file first with at least 1 telegram user id (admin user id)!\nwrite -1 in that file if you don't want to add any admin.")
    exit(1)

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
def bot_ping(message, file_id = ''):
    # check if in admin list
    if (str(message.chat.id) not in admin_list):
        return
    
    # get text of message
    if (file_id != ''):
        # message has image
        ann_mes = str(message.caption)
        log('a', 'w', f'announcement image file_id: {file_id}')
    else:
        ann_mes = str(message.text)
    # check receiving mode ( INCLUDE / EXCLUDE )
    ann_mode = ann_mes.split("\\ANN_END\n")[1].splitlines()[0]
    # get IDs of announcement receivers
    ann_ids = ann_mes.split("\\MODE_END\n")[1].splitlines()
    temp_ann_ids = ann_ids
    # get actual message
    ann_mes = ann_mes.removeprefix(f"/{command_announ}\n").split("\\ANN_END")[0].removesuffix("\\ANN_END").strip()

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
        bot_ping(message, message.photo[-1].file_id)

log('o', 'w', 'bot launched')
# Launching bot polling
bot.polling(timeout=20, long_polling_timeout = 10)

# Stopping bot (there is actually nothing to stop, just close database (useless because program will exit anyway))
# get notification that bot stopped working for some reason
if args_notify:
    post_ntfy('w', 'stopped', 'bot stopped working.\ncheck log.log for more information.', 'h')

log('o', 'w', 'bot stopped working')
log('o', 'w', 'closing database...')
db.close()
log('o', 'w', 'finished')
