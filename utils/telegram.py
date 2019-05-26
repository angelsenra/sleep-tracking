#! python3
import json
import logging
import os
import urllib.parse
import urllib.request

APPNAME = os.environ["APPNAME"]
BOT_ID = int(os.environ["TELEGRAM_BOT_ID"])
MY_ID = int(os.environ["TELEGRAM_PERSONAL_ID"])
TELEGRAM_TOKEN = os.environ["TELEGRAM_TOKEN"]
URL = f"https://{APPNAME}.herokuapp.com/{TELEGRAM_TOKEN}"
logger = logging.getLogger("Telegram")


class Bot:
    def __init__(self, token=TELEGRAM_TOKEN):
        self.url = f"https://api.telegram.org/bot{token}/"

    def call(self, method, **kw):
        data = urllib.parse.urlencode(kw).encode()
        r = urllib.request.urlopen(self.url + method, data=data).read()
        return json.loads(r)

    def forward_message(self, chat_id, from_chat_id, message_id):
        return self.call("forwardMessage", chat_id=chat_id,
                         from_chat_id=from_chat_id, message_id=message_id)

    def report(self, text, **kw):
        logger.info(text)
        return self.send_message(MY_ID, text, disable_notification=True, **kw)

    def set_webhook(self, url=URL):
        self.report(f"Webhook set at {url}")
        return self.call("setWebhook", url=url)

    def send_message(self, chat_id, text, **kw):
        return self.call("sendMessage", chat_id=chat_id, text=text,
                         parse_mode="Markdown", **kw)


if __name__ == "__main__":
    Bot().report("Creating app")
