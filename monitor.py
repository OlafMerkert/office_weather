#!/usr/bin/env python2
# -*- coding: utf-8 -*-

from __future__ import print_function
import os
import sys
import time
import yaml

from Co2Device import Co2Device
from SlackReporter import configure_slack
from HystereseNotifier import HystereseNotifierFromConfig, DataExtractor
from GraphCollector import GraphCollector


OBSERVATION_TIME_INTERVAL = 5
COLLECTION_TIME_INTERVAL = 2


AVAILABLE_QUANTITIES = [
    DataExtractor(
        config_key="temperature",
        label="Temperature",
        unit="deg C",
        min_value=10,
        max_value=35,
        extract=lambda data: data.temperature),
    DataExtractor(
        config_key="co2_level",
        label="CO2 level",
        unit="ppm",
        min_value=400,
        max_value=1000,
        extract=lambda data: data.co2_level)]


def current_time():
    return int(time.time())

def get_config(config_file_path):
    with open(config_file_path, 'r') as stream:
        return yaml.load(stream)

def main(device_path, config_file_path):
    config = get_config(config_file_path)

    monitor_device = Co2Device(device_path)
    monitor_device.open_monitor_device()

    observers = []
    collectors = []
    slack = configure_slack(config)
    if slack:
        for data_extractor in AVAILABLE_QUANTITIES:
            if data_extractor.config_key in config:
                observer = HystereseNotifierFromConfig(slack,
                                                       data_extractor,
                                                       config[data_extractor.config_key])
                observers.append(observer)
                print("debug Enabled watching {0}".format(data_extractor.label))

    if "plotting" in config:
        graph_notifier = GraphCollector(slack,
                                        AVAILABLE_QUANTITIES,
                                        config["plotting"])
        collectors.append(graph_notifier)

    stamp = current_time()

    print("debug observers: {0}, collectors: {1}".format(observers, collectors))

    while True:
        data = monitor_device.read_device_data()
        print("debug current data: {0}".format(data))

        if data and (current_time() - stamp > OBSERVATION_TIME_INTERVAL):
            for o in observers:
                o.notify(data)
                stamp = current_time()
        if data and (current_time() - stamp > COLLECTION_TIME_INTERVAL):
            for c in collectors:
                c.notify(data)


if __name__ == "__main__":
    script_base_dir = os.path.dirname(os.path.realpath(sys.argv[0])) + "/"
    config_file_path = script_base_dir + "config.yaml"

    device_path = sys.argv[1]

    main(device_path, config_file_path)
