# -*- coding: utf-8 -*-

from __future__ import print_function
import requests


class SlackReporter(object):

    def __init__(self, config):
        self._config = config
        self.load_config(config)

    def load_config(self, config):
        if "api_token" in config:
            self._api_token = config["api_token"]
            self._channel = config["channel"]
            self._botName = config["botname"]
            self._icon = config["icon"]
        elif "webhook" in config:
            self._webhook_url = config["webhook"]
            self._channel = config["channel"]
            self._botName = config["botname"]
            self._icon = config["icon"]
        else:
            raise "Did not find slack configuration object"

    def webhook_p(self):
        return (hasattr(self, "_webhook_url") and
                hasattr(self, "_channel") and
                hasattr(self, "_botName") and
                hasattr(self, "_icon"))

    def webapi_p(self):
        return (hasattr(self, "_api_token") and
                hasattr(self, "_channel") and
                hasattr(self, "_botName") and
                hasattr(self, "_icon"))

    def enabled_p(self):
        return (self.webapi_p() or self.webhook_p())

    def send_message_webhook(self, message):
        # print("debug sending message to slack: {0}".format(message))
        payload = {
            "channel": self._channel,
            "username": self._botName,
            "icon_emoji": self._icon,
            "text": message,
        }
        requests.post(self._webhook_url, json=payload)

    def send_message_api(self, message):
        payload = {
            "token": self._api_token,
            "channel": self._channel,
            "username": self._botName,
            "icon_emoji": self._icon,
            "text": message,
        }
        requests.post(url="https://slack.com/api/chat.postMessage",
                      data=payload)

    def send_message(self, message):
        if (message and self.webapi_p()):
            self.send_message_api(message)
        elif (message and self.webhook_p()):
            self.send_message_webhook(message)

    def send_image_by_handle(self, image_file, title=""):
        if (image_file and self.webapi_p()):
            payload = {
                "token": self._api_token,
                "channels": self._channel,
                "title": title,
            }
            files = {"file": image_file}
            requests.post(url="https://slack.com/api/files.upload",
                          data=payload,
                          files=files)

    def send_image(self, image_path, title=""):
        if image_path:
            with open(image_path, "rb") as image_file:
                self.send_image_by_handle(image_file, title)


def configure_slack(config):
    if "slack" in config:
        slack = SlackReporter(config["slack"])
        print("debug Enabled sending slack messages")
        return slack
