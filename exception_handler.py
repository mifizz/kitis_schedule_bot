import requests, telebot, time, re
from typing import Literal
from logger import log
import kitis_api as api
import regex_helper as rh

TOKEN = ""

def set_token(token: str) -> None:
    """Set the bot token globally"""
    global TOKEN
    TOKEN = token

class BotExceptionHandler(telebot.ExceptionHandler):
    """Custom exception handler. Handles Telegram and requests exceptions"""
    last_error_time: float = 0.0
    log_error_cooldown: float = 20.0

    def handle(self, exception) -> Literal[False]:
        """Main handle method."""
        if isinstance(exception, telebot.apihelper.ApiException):
            self._handle_telegram_exception(exception)
        elif isinstance(exception, requests.exceptions.RequestException):
            self._handle_requests_exception(exception)
        else:
            self._handle_generic_exception(exception)
        return False

    def _log_exception(self, text: str, ntfy_title: str) -> None:
        text = self._sanitize_token(text)
        if not self._error_spam():
            self.last_error_time = time.time()
            log("fail", text, True, ntfy_title, 'e')
        else:
            log("fail", text)

    def _error_spam(self) -> bool:
        return time.time() - self.last_error_time < self.log_error_cooldown

    def _sanitize_token(self, text: str) -> str:
        """Replace bot token in exception message with <BOT_TOKEN>"""
        return text.replace(TOKEN, "<BOT_TOKEN>") if TOKEN else text

    def _handle_telegram_exception(self, e: telebot.apihelper.ApiException) -> None:
        """Handle Telegram API exceptions"""
        text: str = "empty exception message"
        if isinstance(e, telebot.apihelper.ApiTelegramException):
            text = f"TgAPI Telegram ({e.error_code}): {e.description}"
        elif isinstance(e, telebot.apihelper.ApiHTTPException):
            text = f"TgAPI HTTP ({e.result.status_code}): {e.result.reason}"
        elif isinstance(e, telebot.apihelper.ApiInvalidJSONException):
            match = rh.extract_regex(r"Response body:\n(.+)", str(e))
            text = f"TgAPI Invalid JSON:\n{match[0]}" if match else f"TgAPI Invalid JSON: {e}"
        else:
            match = rh.extract_regex(r"A request to the Telegram API was unsuccessful. (.+)", str(e))
            text = f"TgAPI: {match[0]}" if match else f"TgAPI: {e}"
        self._log_exception(text, "Telegram API error")

    def _handle_requests_exception(self, e: requests.exceptions.RequestException) -> None:
        """Handle requests exceptions"""
        e_type: str = type(e).__name__
        text: str = "empty exception message"
        if isinstance(e, requests.exceptions.Timeout):
            match = rh.extract_regex(r"host='([^']+)'.*timeout=(\d+)", str(e))
            text = f"{e_type} ({match[1]}): {match[0]}" if match else f"{e_type}: {e}"
        elif isinstance(e, requests.exceptions.ConnectionError):
            match = rh.extract_regex(r"host='([^']+)'.*url: (\S+)", str(e))
            text = f"{e_type}: {match[0]}{match[1]}" if match else f"{e_type}: {e}"
        else:
            text = f"{type(e).__name__}: {e}"
        self._log_exception(text, "Requests error")

    def _handle_generic_exception(self, e: Exception) -> None:
        """Handle all other uncaught exceptions"""
        self._log_exception(f"{type(e).__name__}: {e}", "Uncaught exception")
