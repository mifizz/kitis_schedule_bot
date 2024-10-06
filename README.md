# KITiS schedule bot
See schedule for any group in КИТиС in telegram bot

# Important!
For this bot to work, you need to enter your bot token into bot. There's currently 2 ways of doing that:
1. Create .env file in the same directory as all .py files located. Here you need to write this string and change 'YOUR TOKEN HERE' to your bot token.
```
TOKEN='YOUR TOKEN HERE'
```
2. Launch bot with your token in CLI arguments. eg:
```
python bot.py YOUR_TOKEN_HERE
```
(in some systems you need to replace **python** with **python3**)

# Dependencies
For this bot to work, you need to install some libraries with **pip**.
```
pip install requests telebot python-dotenv beautifulsoup4
```
