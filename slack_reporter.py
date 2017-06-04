# -*- coding: utf-8 -*-

from __future__ import print_function
import requests


class SlackReporter(object):

    def __init__(self, config):
        self._config = config
        self.load_config(config)

    def load_config(self, config):
        if "webhook" in config:
            self._webhook_url = config["webhook"]
            self._channel = config["channel"]
            self._botName = config["botname"]
            self._icon = config["icon"]
        else:
            raise "Did not find slack configuration object"

    def enabled_p(self):
        return (hasattr(self, "_webhook_url") and
                hasattr(self, "_channel") and
                hasattr(self, "_botName") and
                hasattr(self, "_icon"))

    def send_message(self, message):
        if (message and self.enabled_p()):
            # print("debug sending message to slack: {0}".format(message))
            payload = {
                'channel': self._channel,
                'username': self._botName,
                'text': message,
                'icon_emoji': self._icon
            }
            requests.post(self._webhook_url, json=payload)
