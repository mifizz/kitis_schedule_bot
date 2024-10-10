# КИТиС schedule bot
See schedule for any group in КИТиС in telegram bot. This bot uses user database so you can choose your group once with **/group** command. There is no need to select the same group twice, you can use **/schedule** command to get schedule for your group whenever you want (except when schedule website is down).

# How to use
Firstly, you need to clone this repo to your PC or download source code (Code -> Download zip) and unzip it anywhere.

## Creating telegram bot
Next you need to create a new bot in telegram with [Bot Father](https://t.me/BotFather). After you created bot you need to set it up. Type /mybots command in Bot Father and choose bot you created. There you need to select Edit Bot -> Edit Commands and paste this (you may change descriptions for commands how you want):
```
schedule - THIS IS COMMAND FOR REQUESTING SCHEDULE
group - THIS IS COMMAND FOR CHOOSING YOUR GROUP
```
You may also want to change your bot name, description, etc. You can do all this with Bot Father

After you set up your new bot you need to get your bot token. To do this you need to select Edit Bot -> API Token. There you can copy your bot token.

## Launching bot
Before you can launch bot you need to install dependencies. They are listed in [dependencies](#dependencies) section

Finally, you need to launch your bot with your API token. You currently have 2 options for launching bot:
1. Create *.env* file in the same directory as all *.py* files located. Here you need to write this string and change **YOUR TOKEN HERE** to your bot token (you MUST keep quotes).
```
TOKEN='YOUR TOKEN HERE'
```

And then launch your bot with python:
```
python bot.py
```

2. You can launch your bot without creating *.env* file. When you launching bot you can just type your API token as command line argument:
```
python bot.py YOUR_TOKEN_HERE
```

Note that in some systems you need to replace **python** with **python3**.

# Dependencies
For this bot to work, you need to install some libraries with **pip**.
```
pip install requests telebot python-dotenv beautifulsoup4
```
