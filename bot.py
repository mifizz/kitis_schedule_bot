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

def log(tag='u', color='b', text='undefined'):
    # writing in log and printing in console
    colors = {
        'r':'\033[31m',
        'g':'\033[32m',
        'y':'\033[33m',
        'b':'\033[36m'
    }
    tags = {
        't':'start',
        'g':'group',
        's':'sched',
        'p':'ping?',
        'e':'error',
        'o':'other',
        'u':'undef'
    }

    if args_colored:
        output = '\033[90m' + time.asctime() + '\033[0m ' + colors[color] + '[' + tags[tag] + ']\033[0m > ' + text
        print(output)
    else:
        output = '['+ tags[tag] + '] > ' + text
        print(output)
    logger.info(output)

    if args_notify and tag == 'e':
        post_ntfy('e', 'error occured', f'{text}', 'h')

logger.info('-----------------------------------------')

# notifications via ntfy
post_topic = ''
def post_ntfy(tag='i', title='title undefined', text='text undefined', priority='d'):
    global args_notify
    tags = {
        'i':'speech_balloon',
        'w':'warning',
        'e':'x'
    }
    priorities = {
        'u':'urgent',
        'h':'high',
        'd':'default',
        'l':'low',
        'm':'min'
    }

    post_req = requests.post(f"https://ntfy.sh/{post_topic}",
        data=f"{text}",
        headers={
            "Title": f"{title}",
            "Priority": f"{priorities[priority]}",
            "Tags": f"{tags[tag]}"
        })
    print(post_req.status_code)
    if post_req.status_code != 200:
        args_notify = False
        log('e', 'r', f'error occurred: can\'t access "ntfy.sh/{post_topic}" (status code: {post_req.status_code}). Notifications are now disabled.')

# Exception handler
class BotExceptionHandler(tb.ExceptionHandler):
    def handle(self, exception):
        log('e', 'r', f"error occurred: {exception}")
        return exception

# Arguments and flags
args_token = ''
args_colored = False
args_notify = False

# list of all existing flags
args_list = {'-h', '--help', '-t', '--token', '-c', '--colored'}

sys.argv.remove(sys.argv[0]) # Removing filename from arguments list

# help flag
if '-h' in sys.argv or '--help' in sys.argv:
    print('-h or --help\t - show usage help\n-c or --colored\t - sets colored log output (cat)\n-t or --token\t - sets bot token from next agrument')
    exit(0)

# token flag
if '-t' in sys.argv:
    try:
        args_token = sys.argv[sys.argv.index('-t') + 1]
        sys.argv.remove(sys.argv[sys.argv.index('-t') + 1])
        sys.argv.remove('-t')
    except Exception as e:
        log('e', 'r', f'error occurred while getting arguments: {e}')
        exit(1)
elif '--token' in sys.argv:
    try:
        args_token = sys.argv[sys.argv.index('--token') + 1]
        sys.argv.remove(sys.argv[sys.argv.index('--token') + 1])
        sys.argv.remove('--token')
    except Exception as e:
        log('e', 'r', f'error occurred while getting arguments: {e}')
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
        log('e', 'r', f'error occurred while getting arguments: {e}')
        exit(1)
elif '--notifications' in sys.argv:
    try:
        args_notify = True
        post_topic = sys.argv[sys.argv.index('--notifications') + 1]
        sys.argv.remove(sys.argv[sys.argv.index('--notifications') + 1])
        sys.argv.remove('--notifications')
    except Exception as e:
        log('e', 'r', f'error occurred while getting arguments: {e}')
        exit(1)

# check for unknown arguments
if len(sys.argv) > 0 and not sys.argv[0] in args_list:
    log('e', 'r', f'unknown argument "{sys.argv[0]}". aborting...')
    exit(1)

# Loading token and initializing bot
dotenv.load_dotenv()
if args_token != '':
    TOKEN = args_token
elif os.getenv('TOKEN'):
    TOKEN = os.getenv('TOKEN')
else:
    log('e', 'r', 'error occurred: no token given')
    exit(1)
try:
    bot = tb.TeleBot(TOKEN, exception_handler=BotExceptionHandler())
except Exception as e:
    log('e', 'r', f'error occurred: {e}')
    exit(1)

# Connecting to database
db = database('db.db')

# Some variables :)
bells_monday = {
    '1 Пара':'8:30-9:00',
    '2 Пара':'9:10-10:30',
    '3 Пара':'10:40-12:00',
    '4 Пара':'12:20-13:40',
    '5 Пара':'13:50-15:10',
    '6 Пара':'15:20-16:40',
    '7 Пара':'16:50-18:10'
}
bells = {
    '1 Пара':'8:30-10:00',
    '2 Пара':'10:10-11:40',
    '3 Пара':'12:10-13:40',
    '4 Пара':'13:50-15:20',
    '5 Пара':'15:30-17:00',
    '6 Пара':'17:10-18:40',
    '7 Пара':'18:50-20:20'
}
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

cq_action = 'none' # Action id for callback query
cur_bot_message = tb.types.Message

def get_url(group):
    url = 'http://94.72.18.202:8083/raspisanie/www/cg'
    url += url_dict[group] + '.htm'
    return url

def get_schedule(url, group):
    result = 'Расписание для группы <b>' + group + '</b>\n'
    try:
        response = requests.get(url, timeout=5)
    except Exception as e:
        raise
    if response.status_code == 200:
        html_content = response.content
        soup = BeautifulSoup(html_content, 'html.parser')

        is_monday = False
        td_next_is_lesson_time = False
        table = soup.find('table', class_='inf')
        for tr in table.find_all('tr'):
            temp_subgroup_found = False
            subgroup = ''
            for td in tr.find_all('td'):
                #print(td)                  #debug
                
                has_subgroup = False
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

                if td.text == '1' or td.text == '2' or td.text == '3' or td.text == '4' or td.text == '5' or td.text == '6' or td.text == '7':
                    cur_lesson_number = td.text
        result += '\n<i>' + soup.find('div', class_='ref').text.removeprefix(' ').removesuffix(' ') + '</i>' # Date and time of last schedule change
    else:
        log('s', 'r', f'error: failed to fetch website! // status code: {response.status_code}') # this line of code will probably never execute :\
        raise
    return result

def gm_groups():
    markup = InlineKeyboardMarkup()
    markup.row_width = 3
    group_keys = list(url_dict.keys())
    IKB_list = list()

    for n in range(len(group_keys)):
        IKB_list.append(InlineKeyboardButton(group_keys[n], callback_data=group_keys[n]))
    
    markup.add(*IKB_list)
    return markup

def is_schedule_spam(prev_time):
    return (time.time() - prev_time) < 5

def is_group_spam(prev_time):
    return (time.time() - prev_time) < 5

# Start message command
@bot.message_handler(commands=['start'])
def start(message):
    log('t', 'b', f'start received // sender id: {message.chat.id}, username: {message.chat.username}')
    bot.send_message(message.chat.id, "Привет, это бот для просмотра расписания КИТиС!\nДля начала выбери свою группу с помощью команды /group, а после этого используй команду /schedule, чтобы посмотреть расписание выбранной группы!")

    if db.user_exists(message.chat.id):
        log('t', 'g', f'user exists // id: {message.chat.id}, username: {message.chat.username}, db_id: {db.get_db_id(message.chat.id)}')
    else:
        log('t', 'y', f'user is not in database // id: {message.chat.id}, username: {message.chat.username}')
        db.add_user(message.chat.id, message.chat.username)
        log('t', 'g', f'added user to database // id: {message.chat.id}, username: {message.chat.username}, db_id: {db.get_db_id(message.chat.id)}')

# Schedule command
@bot.message_handler(commands=['schedule'])
def schedule(message):
    log('s', 'b', f'schedule request // id: {message.chat.id}, username: {message.chat.username}, db_id: {db.get_db_id(message.chat.id)}')    # DEBUG
    
    if not db.get_group(message.chat.id):
        log('s', 'y', f'request rejected: group is empty! // id: {message.chat.id}, username: {message.chat.username}, db_id: {db.get_db_id(message.chat.id)}')     # DEBUG
        bot.send_message(message.chat.id, 'Сначала выберите группу! - /group')
        return
    if is_schedule_spam(db.get_schedule_request_time(message.chat.id)):
        log('s', 'y', f'request rejected: too many requests in 5 seconds! // id: {message.chat.id}, username: {message.chat.username}, db_id: {db.get_db_id(message.chat.id)}')     # DEBUG
        bot.send_message(message.chat.id, 'Вы слишком часто запрашиваете расписание! Подождите немного и попробуйте снова...')
        return
    
    request_notification = bot.send_message(message.chat.id, "Запрашиваю данные...\n\n<i>Если Вы видите этот текст больше 10 секунд, значит скорее всего что-то пошло не так...</i>", parse_mode='HTML')
    group = db.get_group(message.chat.id)
    
    try:
        result = get_schedule(get_url(group), group)
    except Exception as e:
        bot.edit_message_text("Не удалось получить расписание! Попробуйте позже...", message.chat.id, request_notification.id)
        log('e', 'r', f'error occurred: {e}')
        return
    bot.edit_message_text(result, message.chat.id, request_notification.id, parse_mode='HTML')
    db.update_schedule_request_time(message.chat.id)
    log('s', 'g', f'sent schedule // id: {message.chat.id}, username: {message.chat.username}, db_id: {db.get_db_id(message.chat.id)}')     # DEBUG

# One time schedule command (scheduleother)
@bot.message_handler(commands=['scheduleother'])
def scheduleother(message):
    global cq_action, cur_bot_message
    
    log('s', 'b', f'schedule request (one-time) // id: {message.chat.id}, username: {message.chat.username}, db_id: {db.get_db_id(message.chat.id)}')    # DEBUG
    if is_schedule_spam(db.get_schedule_request_time(message.chat.id)):
        log('s', 'y', f'request rejected (one-time): too many requests in 5 seconds! // id: {message.chat.id}, username: {message.chat.username}, db_id: {db.get_db_id(message.chat.id)}')     # DEBUG
        bot.send_message(message.chat.id, 'Вы слишком часто запрашиваете расписание! Подождите немного и попробуйте снова...')
        return
    cur_bot_message = bot.send_message(message.chat.id, "Выберите группу (группа не сохраняется):", reply_markup=gm_groups())
    db.update_schedule_request_time(message.chat.id)
    cq_action = 'sched_other'

# Group pickup command
@bot.message_handler(commands=['group'])
def group_pickup(message):
    global cq_action

    log('g', 'b', f'group pickup request // id: {message.chat.id}, username: {message.chat.username}, db_id: {db.get_db_id(message.chat.id)}')
    if is_group_spam(db.get_group_request_time(message.chat.id)):
        log('g', 'y', f'request rejected: too many requests in 5 seconds! // id: {message.chat.id}, username: {message.chat.username}, db_id: {db.get_db_id(message.chat.id)}')
        bot.send_message(message.chat.id, 'Вы слишком часто используете команду смены группы!\nВы можете менять группу используя уже присланную в предыдущих сообщениях таблицу с группами!')
        return
    bot.send_message(message.chat.id, "Выберите группу:", reply_markup=gm_groups())
    db.update_group_request_time(message.chat.id)
    log('g', 'b', f'sent group pickup message // id: {message.chat.id}, username: {message.chat.username}, db_id: {db.get_db_id(message.chat.id)}')
    cq_action = 'group_pickup'

# Callback query handler (buttons in bot messages)
@bot.callback_query_handler(func=lambda call: True)
def callback_query(call):
    global cq_action
    # Group pickup request
    if cq_action == 'group_pickup':
        db.set_group(call.message.chat.id, call.data)
        bot.send_message(call.message.chat.id, f"Вы выбрали группу {db.get_group(call.message.chat.id)}!")
        # Closing callback query (Unfreezing buttons)
        bot.answer_callback_query(call.id)
        if db.user_has_group(call.message.chat.id):
            log('g', 'g', f'picked group {db.get_group(call.message.chat.id)} // id: {call.message.chat.id}, username: {call.message.chat.username}, db_id: {db.get_db_id(call.message.chat.id)}')
        else:
            log('g', 'r', f'something went wrong // id: {call.message.chat.id}, username: {call.message.chat.username}, db_id: {db.get_db_id(call.message.chat.id)}')
        cq_action = 'group_pickup'
    
    # Schedule request (one-time)
    elif cq_action == 'sched_other':
        temp_group = call.data
        bot.answer_callback_query(call.id)

        bot.delete_message(call.message.chat.id, cur_bot_message.id)
        request_notification = bot.send_message(call.message.chat.id, "Запрашиваю данные...\n\n<i>Если Вы видите этот текст больше 10 секунд, значит скорее всего что-то пошло не так...</i>", parse_mode='HTML')

        try:
            result = get_schedule(get_url(temp_group), temp_group)
        except Exception as e:
            bot.edit_message_text("Не удалось получить расписание! Попробуйте позже...", call.message.chat.id, request_notification.id)
            log('e', 'r', f'error occurred: {e}')
            cq_action = 'none'
            return
        bot.edit_message_text(result, call.message.chat.id, request_notification.id, parse_mode='HTML')
        log('s', 'g', f'sent schedule (one-time), group {temp_group} // id: {call.message.chat.id}, username: {call.message.chat.username}, db_id: {db.get_db_id(call.message.chat.id)}')     # DEBUG
        cq_action = 'group_pickup'
    
    # Callback query is empty
    elif cq_action == 'none':
        bot.answer_callback_query(call.id)
        bot.send_message(call.message.chat.id, 'Не могу выполнить запрос!')
        log('b', 'u', 'empty callback query request')
    # Unknown callback query action
    else:
        log('g', 'r', f'something went wrong // id: {call.message.chat.id}, username: {call.message.chat.username}, db_id: {db.get_db_id(call.message.chat.id)}')

@bot.message_handler(commands=['ping'])
def bot_ping(message):
    log('p', 'b', f'ping request // id: {message.chat.id}, username: {message.chat.username}, db_id: {db.get_db_id(message.chat.id)}')
    cur_bot_message = bot.send_message(message.chat.id, f'Бот <b>работает</b>!\n\nТекущее состояние сайта: <b>Ожидание ответа...</b>\n<u>Адрес</u>: <i>http://94.72.18.202:8083/raspisanie/www/index.htm</i>\n<u>IP</u>: <i>94.72.18.202</i>\n<u>Порт</u>: <i>8083</i>\n<u>Код статуса</u>: <i>---</i>\n<u>Время отклика</u>: <i>-.--- сек.</i>', parse_mode='HTML')
    try:
        response = requests.get('http://94.72.18.202:8083/raspisanie/www/', timeout=5)
        bot.edit_message_text(f'Бот <b>работает</b>!\n\nТекущее состояние сайта: <b>Работает!</b>\n<u>Адрес</u>: <i>http://94.72.18.202:8083/raspisanie/www/index.htm</i>\n<u>IP</u>: <i>94.72.18.202</i>\n<u>Порт</u>: <i>8083</i>\n<u>Код статуса</u>: <i>{response.status_code}</i>\n<u>Время отклика</u>: <i>{round(response.elapsed.microseconds / 1000) / 1000} сек.</i>', message.chat.id, cur_bot_message.id, parse_mode='HTML')
        log('p', 'g', f'successfully pinged website! // status code: {response.status_code}, elapsed time: {response.elapsed.microseconds / 1000} ms')
    except Exception as e:
        bot.edit_message_text(f'Бот <b>работает</b>!\n\nТекущее состояние сайта: <b>Не отвечает!</b>\n<u>Адрес</u>: <i>http://94.72.18.202:8083/raspisanie/www/index.htm</i>\n<u>IP</u>: <i>94.72.18.202</i>\n<u>Порт</u>: <i>8083</i>\n<u>Код статуса</u>: <i>---</i>\n<u>Время отклика</u>: <i>-.--- сек.</i>', message.chat.id, cur_bot_message.id, parse_mode='HTML')
        log('p', 'r', f'can\'t connect to website! // exception: {e}')

# Launching bot polling
log('o', 'b', 'bot launched')
bot.polling(timeout=20, long_polling_timeout = 10)

# Stopping bot
if args_notify:
    post_ntfy('w', 'stopped', 'bot stopped working.\ncheck log.log for more information.', 'h')

log('o', 'b', 'bot stopped working')
log('o', 'b', 'closing database...')
db.close()
log('o', 'b', 'finished')
