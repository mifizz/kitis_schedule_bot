[En](#китис-schedule-bot-en) / [Ru](#бот-расписания-китис-ru)

# КИТиС schedule bot (en)
See schedule for any group in КИТиС in telegram bot. This bot uses user database so you can choose your group once with **/group** command. There is no need to select the same group twice, you can use **/schedule** command to get schedule for your group whenever you want (except when schedule website is down).

## How to make your own
Firstly, you need to clone this repo to your PC or download source code (Code -> Download zip) and unzip it anywhere.

### Creating telegram bot
Next you need to create a new bot in telegram with [Bot Father](https://t.me/BotFather). After you created bot you need to set it up. Type **/mybots** command in Bot Father and choose bot you created. There you need to select Edit Bot -> Edit Commands and paste this (you may change descriptions for commands how you want):
```
schedule - THIS IS COMMAND FOR REQUESTING SCHEDULE
group - THIS IS COMMAND FOR CHOOSING YOUR GROUP
```
You may also want to change your bot name, description, etc. You can do all this with Bot Father

After you set up your new bot you need to get your bot token. To do this you need to select Edit Bot -> API Token. There you need to copy your bot token.

### Launching bot
Before you can launch bot you need to install dependencies. They are listed in [dependencies](#dependencies) section

Finally, you can launch your bot using API token. You currently have 2 options of doing this:
1. Create *.env* file in the same directory as all *.py* files located. Here you need to paste this string and change **YOUR TOKEN HERE** to your bot token (token MUST be in quotes):
```
TOKEN='YOUR TOKEN HERE'
```

And then launch your bot with python:
```
python bot.py
```

2. You can launch your bot without creating *.env* file. Use *-t* or *--token* flag with token afterwards instead when launching bot:
```
python bot.py -t YOUR_TOKEN_HERE
```

Note that in some systems you need to replace **python** with **python3**.

### Logging
You can see debug information in your terminal when bot is running. You can also view *log.log* file to see old debug output.
If you want colored debug output in your terminal or if you are using **cat** to see *log.log* file you may use *-c* or *--colored* flag when launching bot, eg.
```
python bot.py -c
```

## Dependencies
For this bot to work, you need to install some libraries with **pip** (just paste this command and press Enter).
```
pip install requests telebot python-dotenv beautifulsoup4
```

# Бот расписания КИТиС (ru)
Смотрите расписание для любой группы КИТиС в телеграм боте. Этот бот использует базу данных пользователей, поэтому Вы можете один раз выбрать свою группу с помощью команды **/group**. Второй раз выбирать группу не нужно, так что Вы когда угодно можете использовать команду **/schedule**, чтобы посмотреть расписание для выбранной Вами группы (кроме случаев, когда сайт с расписанием не работает).

## Как сделать собственного бота 
Для начала, Вам надо склонировать этот репозиторий на свой компьютер или скачать исходный код (Code -> Download zip) и разархивировать где-нибудь на Вашем компьютере.

### Создание телеграм бота
Дальше Вам нужно создать нового телеграм бота с помощью [Bot Father](https://t.me/BotFather). После того, как Вы создали бота, Вам нужно его настроить. Введите команду **/mybots** в Bot Father и выберите бота, которого Вы только что создали. Здесь Вам нужно выбрать Edit Bot -> Edit Commands и вставить следующий текст (Вы можете изменить описание команд как Вам хочется):
```
schedule - ЭТО КОМАНДА ДЛЯ ПОЛУЧЕНИЯ РАСПИСАНИЯ
group - ЭТО КОМАНДА ДЛЯ ВЫБОРА ГРУППЫ
```
Также Вы можете поменять название, описание бота и т.д. Всё это Вы можете сделать с помощью Bot Father.

После того, как Вы настроили своего телеграм бота, Вам нужно получить токен бота. Для этого выберите Edit Bot -> API Token. Здесь Вы необходимо скопировать токен.

### Запуск бота
Перед тем, как запустить бота, Вам нужно установить зависимости. Они указаны в разделе [Зависимости](#зависимости).

Наконец, Вы можете запустить бота используя API токен. На данный момент есть 2 способа сделать это:
1. Создайте файл *.env* в той же директории, где находятся все *.py* файлы. В этом файле вам нужно вставить эту строчку, поменяв **ВАШ ТОКЕН** на Ваш токен бота (токен ДОЛЖЕН быть в кавычках):
```
TOKEN='ВАШ ТОКЕН'
```

И после этого запустить бота с помощью python:
```
python bot.py
```

2. Вы можете запустить бота без создания файла *.env*. Для этого при запуске бота укажите флаг *-t* или *--token*, а после токен бота:
```
python bot.py -t ВАШ_ТОКЕН
```

Учтите, что в некоторых системах Вам нужно использовать **python3** вместо **python**.

### Логи
Вы можете видеть отладочную информацию в вашем терминале, когда бот запущен. Вы также можете посмотреть старые отладочные выводы бота в файле *log.log*.
Если Вы хотите видеть цветной отладочный вывод бота в терминале или если Вы используете **cat** для просмотра логов, при запуске бота добавьте флаг *-c* или *--colored*. Например:
```
python bot.py -c
```

## Зависимости
Чтобы бот работал, Вам нужно установить следующие библиотеки с помощью **pip** (просто вставьте следующую команду и нажмите Enter):
```
pip install requests telebot python-dotenv beautifulsoup4
```
