"""Slack notifier"""
# pylint: disable=logging-fstring-interpolation
import abc
import datetime
import json
import logging
import os
import sys
from typing import List, Dict

import requests
from retrying import retry

LIMIT: int = 2000
POST_TIMEOUT: int = 10  # sec
MAX_FAILURE_ATTEMPTS: int = 3
WAIT_AFTER_FAILURE: int = 5000

_logger = logging.getLogger(__name__)

LEVELS: dict = {
    'info': {
        'level': 'INFO',
        'text_icon': ':large_blue_circle:',
        'icon_emoji': 'information_source:',
    },
    'warning': {
        'level': 'WARNING',
        'text_icon': ':large_yellow_circle:',
        'icon_emoji': ':warning:',
    },
    'error': {
        'level': 'ERROR',
        'text_icon': ':red_circle:',
        'icon_emoji': ':red_circle:',
    }
}

LEVELS_TEAMS: dict = {
    'info': {
        'level': 'INFO',
        'text_icon': '&#x2139;&#xFE0F;',
    },
    'warning': {
        'level': 'WARNING',
        'text_icon': '&#128310;',
    },
    'error': {
        'level': 'ERROR',
        'text_icon': '&#128308;',
    }
}


class NotifierError(Exception):
    """Exception raised if there is an error with notifier"""


def split_text_into_chunks(text: str, max_length: int) -> List[str]:
    """
    Splits a text into chunks of maximum length max_length.

    Parameters:
    text (str): The text to be split.
    max_length (int): The maximum length of each chunk.

    Returns:
    list: A list of text chunks, each of maximum length max_length.
    """
    chunks = []
    for i in range(0, len(text), max_length):
        chunks.append(text[i:i + max_length])
    return chunks


class AbstractNotifier(metaclass=abc.ABCMeta):
    """Abstract class for notifier"""

    @property
    @abc.abstractmethod
    def url(self):
        """Abstract property that must be implemented by subclasses."""

    @abc.abstractmethod
    def set_body(
            self,
            level: str,
            text: str,
            chunk_id: int,
            echo: [str, list] = None
    ) -> Dict:
        """setting body of message"""

    def info(self, text: str, echo: [str, list] = None) -> None:
        """Sends an info level message."""
        self.send_log_message('info', text, echo)

    def warning(self, text: str, echo: [str, list] = None) -> None:
        """Sends a warning level message."""
        self.send_log_message('warning', text, echo)

    def error(self, text: str, echo: [str, list] = None) -> None:
        """Sends an error level message."""
        self.send_log_message('error', text, echo)

    def send_log_message(
            self, level: str, text: str, echo: [str, list] = None
    ) -> None:
        """
        Helper method to send log messages.
        """
        if not text:
            _logger.warning("No text provided, exiting")
            return

        try:
            split_text = split_text_into_chunks(text, LIMIT)

            chunk_id = 1
            for text_chunk in split_text:
                body = self.set_body(level, text_chunk, chunk_id, echo)
                self.send_message(self.url, body)
                chunk_id += 1

        except NotifierError as exc:
            _logger.error(f"Notifier failed "
                          f"after {MAX_FAILURE_ATTEMPTS} attempts: {exc}")

    @retry(
        stop_max_attempt_number=MAX_FAILURE_ATTEMPTS,
        wait_fixed=WAIT_AFTER_FAILURE)
    def send_message(self, url, body: Dict) -> None:
        """Sends a message to the specified URL
        with the given headers and body."""

        byte_length = str(sys.getsizeof(body))
        headers = {
            'Content-Type': "application/json",
            'Content-Length': byte_length
        }

        try:
            response = requests.post(url=url,
                                     data=json.dumps(body),
                                     headers=headers,
                                     timeout=POST_TIMEOUT)

            if response.status_code != 200:
                msg = (f"Failed to send message, "
                       f"status code: {response.status_code}")
                _logger.error(msg)
                raise NotifierError(msg)

        except requests.exceptions.RequestException as exc:
            exc_name = exc.__class__.__name__
            _logger.error(f"Failed to send the message ({exc_name}), retrying")
            raise NotifierError(f"{exc_name} -> {exc}") from exc

        # pylint: disable=broad-exception-caught
        except Exception as exc:
            exc_name = exc.__class__.__name__
            _logger.error(f"Unexpected error: {exc_name} "
                          f"when sending message, retrying")
            raise NotifierError(f"{exc_name} -> {exc}") from exc


class SlackNotifier(AbstractNotifier):
    """
    subclass for sending logger like notifications to Slack channel
    need to generate url address in "incoming WebHooks app"

    :param url: url address generated from incoming webHooks app
    :param name: use __name__ method
    :param username: name of user who "sending" the message
    """

    def __init__(self, url: str, name: str = None, username: str = None):
        self._url = url

        if username is None:
            self.username = os.path.basename(__file__)
        else:
            self.username = username

        if name is None:
            self.name = __name__
        else:
            self.name = name

    @property
    def url(self):
        return self._url

    def set_body(
            self,
            level: str,
            text: str,
            chunk_id: int,
            echo: [str, list] = None
    ) -> Dict[str, str]:
        """sets body for message based on level"""

        level_text = LEVELS[level]['level']
        text_icon = LEVELS[level]['text_icon']
        icon_emoji = LEVELS[level]['icon_emoji']
        date = datetime.datetime.now()

        if echo is not None:
            if isinstance(echo, list):
                echo = ' '.join([f'@{x}' for x in echo])
            else:
                echo = f'@{echo}'
        else:
            echo = ''

        message_text = (f"{text_icon} {echo} {date} [{self.name}]"
                        f" {level_text}:\n{text}")

        # if there are more chunk of one message
        # do not log icons, username etc.
        if chunk_id > 1:
            message_text = text

        return {
            "username": self.username,
            "icon_emoji": icon_emoji,
            "blocks": [
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": message_text
                    }
                }
            ]
        }


class TeamsNotifier(AbstractNotifier):
    """
    subclass for sending logger like notifications to Teams channel
    need to generate url address in "incoming WebHooks app"

    :param url: url address generated from incoming webHooks app
    :param name: use __name__ method
    :param username: name of user who "sending" the message
    """

    def __init__(self, url: str, name: str = None, username: str = None):
        self._url = url

        if username is None:
            self.username = os.path.basename(__file__)
        else:
            self.username = username

        if name is None:
            self.name = __name__
        else:
            self.name = name

    @property
    def url(self):
        return self._url

    def set_body(
            self,
            level: str,
            text: str,
            chunk_id: int,
            echo: [str, list] = None
    ) -> Dict[str, str]:
        """sets body for message based on level"""

        level_text = LEVELS_TEAMS[level]['level']
        text_icon = LEVELS_TEAMS[level]['text_icon']
        date = datetime.datetime.now()

        return {
            'text': f"{text_icon} {date} [{self.name}] "
                    f" {level_text}:  {text}"
        }
