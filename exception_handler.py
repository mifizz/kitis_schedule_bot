import requests, telebot, time
from typing import Literal
from logger import log
import kitis_api as api

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
        sanitized_message = self._sanitize_token(str(exception))

        if isinstance(exception, telebot.apihelper.ApiException):
            self._handle_telegram_exception(exception, sanitized_message)
        elif isinstance(exception, requests.exceptions.RequestException):
            self._handle_requests_exception(exception, sanitized_message)
        else:
            self._handle_generic_exception(exception, sanitized_message)
        return False

    def _error_spam(self) -> bool:
        return time.time() - self.last_error_time < self.log_error_cooldown

    def _sanitize_token(self, mes: str) -> str:
        """Replace bot token in exception message with <BOT_TOKEN>"""
        return mes.replace(TOKEN, "<BOT_TOKEN>") if TOKEN else mes

    def _handle_telegram_exception(self, e: telebot.apihelper.ApiException, mes: str) -> None:
        """Handle Telegram API exceptions"""
        # i will expand it later because i'm too lazy right now
        exception_type: str = type(e).__name__
        if not self._error_spam():
            log("fail", f"{exception_type}: {mes}", True, "Telegram API error", 'e')
            self.last_error_time = time.time()
        else:
            log("trash", f"{exception_type}: {mes}")

    def _handle_requests_exception(self, e: requests.exceptions.RequestException, mes: str) -> None:
        """Handle requests exceptions"""
        # i will expand it later because i'm too lazy right now
        exception_type: str = type(e).__name__
        if not self._error_spam():
            log("fail", f"{exception_type}: {mes}", True, "Requests error", 'e')
            self.last_error_time = time.time()
        else:
            log("trash", f"{exception_type}: {mes}")
        pass

    def _handle_generic_exception(self, e: Exception, mes: str) -> None:
        """Handle all other uncaught exceptions"""
        exception_type: str = type(e).__name__
        if not self._error_spam():
            log("fail", f"{exception_type}: {mes}", True, "Uncaught exception", 'e')
            self.last_error_time = time.time()
        else:
            log("trash", f"{exception_type}: {mes}")
