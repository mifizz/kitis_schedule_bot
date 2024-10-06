import requests, os, time
import telebot as tb
from dotenv import load_dotenv
from bs4 import BeautifulSoup
from telebot.types import *
from db import database

groups_count = 58
monday_bells = {
    '1 Пара':'9:10-10:30',
    '2 Пара':'10:40-12:00',
    '3 Пара':'12:20-13:40',
    '4 Пара':'13:50-15:10',
    '5 Пара':'15:20-16:40',
    '6 Пара':'16:50-18:10'
}
url_dict = { 
        'СОД23-1':'130',
        'СОД23-2К':'131',
        'СОД24-1':'227',
        'СОД24-2К':'228',
        'СОД22-1':'134',
        'СОД22-2К':'135',
        'С21-1':'140',
        'С21-2':'141',
        'С21-4К':'143',
        'С21УЗ':'144',
        'С22-1':'145',
        'С22-2':'146',
        'С22-3К':'147',
        'С22уз':'148',
        'С23-1':'149',
        'С23-2':'150',
        'С23-3К':'151',
        'С23УЗ':'152',
        'С24-1':'229',
        'С24-2':'231',
        'С24-3К':'230',
        'С24УЗ':'232',
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
        'СА24УЗ':'236',
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

def debug_message(type, color, text):
    output = '[ '
    match color:
        case 'red':
            output += '\033[31m'
        case 'green':
            output += '\033[32m'
        case 'yellow':
            output += '\033[33m'
        case 'blue':
            output += '\033[34m'
        case 'magenta':
            output += '\033[35m'
        case 'cyan':
            output += '\033[36m'
        case _:
            output += '\033[90m'
    
    output = output + type + '\033[0m ] ' + text
    print(output)

def get_url(group):
    url = 'http://94.72.18.202:8083/raspisanie/www/cg'
    url += url_dict[group] + '.htm'
    return url

def get_schedule(url, group):
    result = 'Группа - <b>' + group + '</b>\n'
    response = requests.get(url)

    if response.status_code == 200:
        html_content = response.content
        soup = BeautifulSoup(html_content, 'html.parser')

        is_monday = False
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
                    result += ' - ' + td.find('a', class_='z1').text + subgroup
                    if td.find('a', class_='z2') != None:
                        result +=  ' - <i>' + td.find('a', class_='z2').text + '</i>'
                    else:
                        result += ' - <i>Кабинет не указан</i>'
                    result += '\n'
                    #result += ' - ' + td.find('a', class_='z1').text + subgroup + ' - ' + td.find('a', class_='z2').text + ' (<i>' + td.find('a', class_='z3').text + '</i>)\n'        # LESSON WITH TEACHER

                ##################  TIME  ##################
                if td.text.find('Пара') > 0 and not is_monday:
                    lesson_time = td.text.split(':', maxsplit=1)
                    result += '<u>' + lesson_time[0] + '</u> - <i>' + lesson_time[1] + '</i>'
                elif td.text.find('Пара') > 0:
                    lesson_time = td.text.split(':', maxsplit=1)
                    result += '<u>' + lesson_time[0] + '</u> - <i>' + monday_bells[lesson_time[0]] + '</i>'
                
                ##################  DAYS  ##################
                if td.text.find('Пн') >= 0:
                    result += '\n' + '--------------------------\n\n' + td.text.removesuffix('Пн') + ' - <b>Понедельник</b>\n\n<u>Подъём флага</u> - <i>8:15-8:25</i>\n<u>Разговор о важном</u> - <i>8:30-9:00</i>\n'
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
                elif td.text.find('Вс') >= 0:
                    result += '\n' + '--------------------------\n\n' + td.text.removesuffix('Вс') + ' - <b>Воскресенье</b>'
    else:
        print("Failed to fetch the website.")
        exit()
    return result

def gm_groups():
    markup = InlineKeyboardMarkup()
    markup.row_width = 3
    group_keys = list(url_dict.keys())
    n = 0
    while n < groups_count - 1:
        markup.add(InlineKeyboardButton(group_keys[n], callback_data=group_keys[n]), InlineKeyboardButton(group_keys[n+1], callback_data=group_keys[n+1]), InlineKeyboardButton(group_keys[n+2], callback_data=group_keys[n+2]))
        n += 3
    markup.add(InlineKeyboardButton(group_keys[groups_count-1], callback_data=group_keys[groups_count-1]))
    return markup

def is_schedule_spam(prev_time):
    return (time.time() - prev_time) < 10

def is_group_spam(prev_time):
    return (time.time() - prev_time) < 5

# Loading token, initializing bot and connecting to database
load_dotenv()
TOKEN = os.getenv('TOKEN')
bot = tb.TeleBot(TOKEN)
db = database('db.db')

# Start message command
@bot.message_handler(commands=['start'])
def start(message):
    debug_message('SYSTEM  ', 'magenta', 'Got new start message!')
    bot.send_message(message.chat.id, "Привет, это бот для просмотра расписания КИТиС!\nДля начала выбери свою группу с помощью команды /group, а после этого используй команду /schedule, чтобы посмотреть расписание выбранной группы!")

    if db.user_exists(message.chat.id):
        debug_message('DATABASE', 'green', 'User exists ( id={}, user_id={} )'.format(str(db.get_db_id(message.chat.id)), message.chat.id))
    else:
        debug_message('DATABASE', 'yellow', 'User is not in database. Adding user to database...')
        db.add_user(message.chat.id, message.chat.username)
        debug_message('DATABASE', 'green', 'Successfully added user to database! ( id={}, user_id={} )'.format(str(db.get_db_id(message.chat.id)), message.chat.id))

# Schedule command
@bot.message_handler(commands=['schedule'])
def schedule(message):
    debug_message('REQUEST ', 'cyan', 'New schedule request!')    # DEBUG
    
    if not db.get_group(message.chat.id):
        debug_message('REQUEST ', 'red', 'Request rejected - group is empty!')     # DEBUG
        
        bot.send_message(message.chat.id, 'Сначала выберите группу! - /group')
        return
    if is_schedule_spam(db.get_schedule_request_time(message.chat.id)):
        debug_message('REQUEST ', 'red', 'Request rejected - too many requests in 10 seconds!')     # DEBUG

        bot.send_message(message.chat.id, 'Вы слишком часто запрашиваете расписание! Подождите немного и попробуйте снова...')
        return
    
    request_notification = bot.send_message(message.chat.id, "Запрашиваю данные...\n\n<i>Если Вы видите этот текст больше 10 секунд, значит скорее всего что-то пошло не так...</i>", parse_mode='HTML')
    group = db.get_group(message.chat.id)
    result = get_schedule(get_url(group), group)
    bot.edit_message_text(result, message.chat.id, request_notification.id, parse_mode='HTML')
    db.update_schedule_request_time(message.chat.id)
    debug_message('REQUEST ', 'green', 'Successfully sent schedule!')     # DEBUG

# Group pickup command
@bot.message_handler(commands=['group'])
def group_pickup(message):
    debug_message('REQUEST ', 'cyan', 'New group pickup request!')
    if is_group_spam(db.get_group_request_time(message.chat.id)):
        debug_message('REQUEST ', 'red', 'Request rejected - too many requests in 5 seconds!')
        bot.send_message(message.chat.id, 'Вы слишком часто используете команду смены группы!\nВы можете менять группу используя уже присланную в предыдущих сообщениях таблицу с группами!')
        return
    bot.send_message(message.chat.id, "Выберите группу:", reply_markup=gm_groups())
    db.update_group_request_time(message.chat.id)

# Callback query handler (buttons in bot messages)
@bot.callback_query_handler(func=lambda call: True)
def callback_query(call):
    debug_message('SYSTEM  ', 'magenta', 'Processing group pickup request...')

    db.set_group(call.message.chat.id, call.data)
    
    bot.send_message(call.message.chat.id, f"Вы выбрали группу {db.get_group(call.message.chat.id)}!")
    # Closing callback query (Unfreezing buttons)
    bot.answer_callback_query(call.id)
    if db.user_has_group(call.message.chat.id):
        debug_message('SYSTEM  ', 'green', ('Successfully picked group! ( ' + str(db.get_group(call.message.chat.id)) + ' )'))

# Launching bot polling
bot.infinity_polling(timeout=20, long_polling_timeout = 10, none_stop=True)
db.close()