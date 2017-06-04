#!/usr/bin/env python2
# -*- coding: utf-8 -*-

from __future__ import print_function
import os
import sys
import time
import yaml
from collections import namedtuple
from matplotlib import pyplot

from holtek_data_readout import Co2Device
from slack_reporter import configure_slack
from notification_by_level import HystereseNotifierFromConfig, DataExtractor


OBSERVATION_TIME_INTERVAL = 5
COLLECTION_TIME_INTERVAL = 0.05


AVAILABLE_QUANTITIES = [
    DataExtractor(
        config_key="temperature",
        label="Temperature",
        extract=lambda data: data.temperature),
    DataExtractor(
        config_key="co2_level",
        label="CO2 level",
        extract=lambda data: data.co2_level)]


def current_time():
    return int(time.time())


class GraphCollector(object):

    def __init__(self, image_reporter, data_extractors=[], data_count=20):
        self._data_extractors = data_extractors
        self._data_count = data_count
        self._data = []

    def notify(self, data):
        self._data.append(data)
        if len(self._data) >= self._data_count:
            self.plot_data()

    def plot_data(self):
        print("debug creating next plot")
        x_data = range(len(self._data))
        for extractor in self._data_extractors:
            y_data = list(map(extractor.extract, self._data))
            pyplot.plot(x_data, y_data)
            pyplot.title(extractor.label)
            pyplot.show()
        self._data = []


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
                observer = HystereseNotifierFromConfig(slack, data_extractor, config[data_extractor.config_key])
                observers.append(observer)
                print("debug Enabled watching {0}".format(data_extractor.label))

    if "plotting" in config:
        graph_notifier = GraphCollector(None, AVAILABLE_QUANTITIES)
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
