#!/usr/bin/env python2

from __future__ import print_function

# based on code by henryk ploetz
# https://hackaday.io/project/5301-reverse-engineering-a-low-cost-usb-co-monitor/log/17909-all-your-base-are-belong-to-us

import fcntl
import os
import requests
import sys
import time
import yaml
from collections import namedtuple

TIME_INTERVAL = 5


EnvironmentData = namedtuple("EnvironmentData", ["temperature", "co2_level"])
Boundary = namedtuple("Boundary", ["threshold", "message"])


def hex_format(d):
    return " ".join("%02X" % e for e in d)


def current_time():
    return int(time.time())


class Co2Device(object):

    def __init__(self, device_path):
        self._device_path = device_path
        self._values = {}
        self._device_key = [0xc4, 0xc6, 0xc0, 0x92, 0x40, 0x23, 0xdc, 0x96]

    def decrypt(self, data):
        cstate = [0x48, 0x74, 0x65, 0x6D, 0x70, 0x39, 0x39, 0x65]
        shuffle = [2, 4, 0, 7, 1, 6, 5, 3]

        phase1 = [0] * 8
        for i, o in enumerate(shuffle):
            phase1[o] = data[i]

        phase2 = [0] * 8
        for i in range(8):
            phase2[i] = phase1[i] ^ self._device_key[i]

        phase3 = [0] * 8
        for i in range(8):
            phase3[i] = ((phase2[i] >> 3) | (phase2[(i - 1 + 8) % 8] << 5)) & 0xff

        ctmp = [0] * 8
        for i in range(8):
            ctmp[i] = ((cstate[i] >> 4) | (cstate[i] << 4)) & 0xff

        out = [0] * 8
        for i in range(8):
            out[i] = (0x100 + phase3[i] - ctmp[i]) & 0xff

        return out

    def open_monitor_device(self):
        self._co2_monitor_device_handle = open(self._device_path, "a+b", 0)
        HIDIOCSFEATURE_9 = 0xC0094806
        set_report = "\x00" + "".join(chr(e) for e in self._device_key)
        fcntl.ioctl(self._co2_monitor_device_handle, HIDIOCSFEATURE_9, set_report)

    def read_device_data(self):
        data = list(ord(chunk) for chunk in self._co2_monitor_device_handle.read(8))
        decrypted = self.decrypt(data)

        if decrypted[4] != 0x0d or (sum(decrypted[:3]) & 0xff) != decrypted[3]:
            print(hex_format(data), " => ", hex_format(decrypted), "Checksum error")
        else:
            op = decrypted[0]
            val = decrypted[1] << 8 | decrypted[2]
            self._values[op] = val

            if (0x50 in self._values) and (0x42 in self._values):
                co2_level = self._values[0x50]
                temperature = (self._values[0x42] / 16.0 - 273.15)
                if not (co2_level > 5000 or co2_level < 0):
                    return EnvironmentData(co2_level=co2_level, temperature=temperature)

        return None


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


class HystereseNotifier(object):

    def __init__(self, reporter, data_extractor, lower_boundary, upper_boundary):
        self._reporter = reporter
        self._above_upper = False
        self._lower_boundary = lower_boundary
        self._upper_boundary = upper_boundary
        self._data_extractor = data_extractor

    def notify_value(self, value):
        if not self._above_upper and value > self._upper_boundary.threshold:
            self._above_upper = True
            self._reporter.send_message(self._upper_boundary.message.format(value))
        elif self._above_upper and value <= self._lower_boundary.threshold:
            self._above_upper = False
            self._reporter.send_message(self._lower_boundary.message.format(value))

    def notify(self, data):
        self.notify_value(self._data_extractor(data))


def HystereseNotifierFromConfig(reporter, data_extractor, config):
    return HystereseNotifier(reporter, data_extractor,
                             lower_boundary=Boundary(threshold=config["lower_threshold"],
                                                     message=config["lower_message"]),
                             upper_boundary=Boundary(threshold=config["upper_threshold"],
                                                     message=config["upper_message"]))


def get_config(config_file_path):
    with open(config_file_path, 'r') as stream:
        return yaml.load(stream)


def main(device_path, config_file_path):
    config = get_config(config_file_path)

    monitor_device = Co2Device(device_path)
    monitor_device.open_monitor_device()

    observers = []

    if "slack" in config:
        slack = SlackReporter(config["slack"])
        print("debug Enabled sending slack messages")
        if "temperature" in config:
            temperature_observer = HystereseNotifierFromConfig(slack, lambda data: data.temperature, config["temperature"])
            observers.append(temperature_observer)
            print("debug Enabled watching temperature")
        if "co2_level" in config:
            co2_observer = HystereseNotifierFromConfig(slack, lambda data: data.co2_level, config["co2_level"])
            observers.append(co2_observer)
            print("debug Enabled watching CO2 level")

    stamp = current_time()

    while True:
        data = monitor_device.read_device_data()
        print("debug current data: {0}".format(data))

        if data and (current_time() - stamp > TIME_INTERVAL):
            for o in observers:
                o.notify(data)
                stamp = current_time()

if __name__ == "__main__":
    script_base_dir = os.path.dirname(os.path.realpath(sys.argv[0])) + "/"
    config_file_path = script_base_dir + "config.yaml"

    device_path = sys.argv[1]

    main(device_path, config_file_path)
