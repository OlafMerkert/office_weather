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


def decrypt(DEVICE_KEY, data):
    cstate = [0x48, 0x74, 0x65, 0x6D, 0x70, 0x39, 0x39, 0x65]
    shuffle = [2, 4, 0, 7, 1, 6, 5, 3]

    phase1 = [0] * 8
    for i, o in enumerate(shuffle):
        phase1[o] = data[i]

    phase2 = [0] * 8
    for i in range(8):
        phase2[i] = phase1[i] ^ DEVICE_KEY[i]

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


def hd(d):
    return " ".join("%02X" % e for e in d)


def now():
    return int(time.time())

slack_co2_notified = False
slack_temperature_notified = False

def notifySlack(co2_level, temperature, config):
    global slack_co2_notified, slack_temperature_notified
    upper_co2_threshold = config["slack"]["upper_co2_threshold"]
    lower_co2_threshold = config["slack"]["lower_co2_threshold"]

    upper_temperature_threshold = config["slack"]["upper_temperature_threshold"]
    lower_temperatue_threshold = config["slack"]["lower_temperatue_threshold"]

    if (co2_level > upper_co2_threshold) and (not slack_co2_notified):
        slack_co2_notified = True
        co2_message = "Bitte Fenster oeffnen, der CO2 Level ist bei {0}ppm.".format(co2_level)
    elif (co2_level < lower_co2_threshold):
        if (slack_co2_notified):
            co2_message = "Das Fenster kann geschlossen werden, der CO2 Level ist nur noch bei {0}ppm.".format(co2_level)
            slack_co2_notified = False
    else:
        co2_message = None

    send_slack_message(config, co2_message)

    if (temperature > upper_temperature_threshold) and (not slack_temperature_notified):
        slack_temperature_notified = True
        temperature_message = "Heiss hier drinnen, es sind {0} Grad Celsius. Klimaanlage anschalten!".format(temperature)
    elif (temperature < lower_temperatue_threshold):
        if (slack_temperature_notified):
            temperature_message = "Es ist wieder kuehler, nur noch {0} Grad Celsius. Die Klimaanlage kann wieder ausgeschaltet werden.'".format(temperature)
            slack_temperature_notified = False
    else:
        temperature_message = None

    send_slack_message(config, temperature_message)

def send_slack_message(config, message):
    if ((not message) or (not config) or ("webhook" not in config)):
        return
    webhook_url = config["webhook"]
    channel = config["channel"] if "channel" in config else "#general"
    botName = config["botname"] if "botname" in config else "CO2bot"
    icon = config["icon"] if "icon" in config else ":robot_face:"

    try:
        payload = {
            'channel': channel,
            'username': botName,
            'text': message,
            'icon_emoji': icon
        }
        requests.post(webhook_url, json=payload)
    except:
        print("Unexpected error:", sys.exc_info()[0])


def config(config_file=None):
    """Get config from file; if no config_file is passed in as argument
        default to "config.yaml" in script dir"""

    if config_file is None:
        script_base_dir = os.path.dirname(os.path.realpath(sys.argv[0])) + "/"
        config_file = script_base_dir + "config.yaml"

    with open(config_file, 'r') as stream:
        return yaml.load(stream)

DEVICE_KEY = [0xc4, 0xc6, 0xc0, 0x92, 0x40, 0x23, 0xdc, 0x96]

def open_monitor_device():
    co2_monitor_device_handle = open(sys.argv[1], "a+b", 0)
    HIDIOCSFEATURE_9 = 0xC0094806
    set_report = "\x00" + "".join(chr(e) for e in DEVICE_KEY)
    fcntl.ioctl(co2_monitor_device_handle, HIDIOCSFEATURE_9, set_report)

    return co2_monitor_device_handle

def read_device_data(co2_monitor_device_handle):
    data = list(ord(chunk) for chunk in co2_monitor_device_handle.read(8))
    decrypted = decrypt(DEVICE_KEY, data)
    values = {}
    if decrypted[4] != 0x0d or (sum(decrypted[:3]) & 0xff) != decrypted[3]:
        print(hd(data), " => ", hd(decrypted), "Checksum error")
    else:
        op = decrypted[0]
        val = decrypted[1] << 8 | decrypted[2]
        values[op] = val

        if (0x50 in values) and (0x42 in values):
            co2_level = values[0x50]
            temperature = (values[0x42] / 16.0 - 273.15)
            return (co2_level, temperature)

    return (None, None)


if __name__ == "__main__":

    try:
        config = config(config_file=sys.argv[2])
    except IndexError:
        config = config()

    # client = client(config)

    co2_monitor_device_handle = open_monitor_device()
    stamp = now()

    while True:
        (co2_level, temperature) = read_device_data(co2_monitor_device_handle)

        if co2_level and temperature:
            # check if it's a sensible value
            # (i.e. within the measuring range plus some margin)
            if (co2_level > 5000 or co2_level < 0):
                continue

            print("CO2: %4i TMP: %3.1f" % (co2_level, temperature))
            if now() - stamp > 5:
                print(">>>")
                if ("slack" in config):
                    notifySlack(temperature, co2_level, config)
                stamp = now()
