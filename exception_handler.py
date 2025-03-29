import requests, time
import telebot as tb
from logger import log

TOKEN: str = None

def set_token(bot_token: str):
    global TOKEN
    TOKEN = bot_token

class BotExceptionHandler(tb.ExceptionHandler):
    last_apiexception_time = 0.0
    last_readtimeout_time = 0.0
    def handle(self, exception):
        # API HTTP exception
        if type(exception) == tb.apihelper.ApiTelegramException:
            # get error code
            error_code = str(exception).split("Error code: ")[1].split(". Description")[0]

            # check if 502 or 429 error occurrs again within 20 seconds
            if (error_code == "502" or error_code == "429") and time.time() - self.last_apiexception_time > 20:
                log("fail", f"HTTP request error ({error_code})", True, f"HTTP request returned {error_code}", "e")
                self.last_apiexception_time = time.time()
            elif (error_code == "502" or error_code == "429"):
                log("trash", f"HTTP request error ({error_code})")
            # other tg api exceptions
            else:
                log("fail", f"{exception}", True, f"telegram api error ({error_code})", 'e')
        # connection timeout exception
        elif type(exception) == requests.ConnectTimeout:
            # removing useless text
            e = str(exception).split("ConnectionPool(")[1].split("): Max retries")[0]       # host='...', port=...
            timeout = str(exception).split("connect timeout=")[1].removesuffix(")\'))")     # set timeout in seconds
            log("fail", f"connection timed out ({timeout}) // {e}")
        # read timeout exception
        elif type(exception) == requests.ReadTimeout:
            # check if read timeout error occurrs again within 60 seconds
            if time.time() - self.last_readtimeout_time > 60:
                # removing useless text
                e = str(exception).split("ConnectionPool(")[1].split("): Read")[0]          # host='...', port=...
                timeout = str(exception).split("read timeout=")[1].removesuffix(')')        # set timeout in seconds
                log("fail", f"read timed out ({timeout}): {e}", True, f"read timed out ({timeout}) // {e}")
                self.last_readtimeout_time = time.time()
            else:
                log("trash", "read timed out again")
        # telegram api HTTPConnectionPool error (network is unreachable)
        elif str(exception).count(f"{TOKEN}") > 0:
            e = str(exception)
            e = e.replace(f"{TOKEN}", "<BOT_TOKEN>")
            log("fail", f"{e}", True, "Telegram API HTTPConnectionPool", 'e')
        # other exceptions
        # if you got these you probably cooked up
        else:
            log("fail", f"\"{exception}\", exception type: {type(exception)}", True, 'you cooked', 'e')
        return exception