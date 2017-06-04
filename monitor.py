#!/usr/bin/env python2
# -*- coding: utf-8 -*-

from __future__ import print_function
import os
import sys
import time
import yaml
from collections import namedtuple
import tempfile
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
        self._image_reporter = image_reporter
        self._data_extractors = data_extractors
        self._data_count = data_count
        self._data = []

    def notify(self, data):
        self._data.append(data)
        if len(self._data) >= self._data_count:
            self.plot_data()

    def plot_data(self):
        print("debug creating next plot")
        assert len(self._data_extractors) == 2

        def plot_extractor(axis, extractor, color, style):
            y_data = list(map(extractor.extract, self._data))
            axis.plot(x_data, y_data, color + style)
            axis.set_ylabel(extractor.label, color=color)
            axis.tick_params("y", colors=color)

        x_data = range(len(self._data))
        figure, axis0 = pyplot.subplots()
        plot_extractor(axis0, self._data_extractors[0], "r", "-")

        axis1 = axis0.twinx()
        plot_extractor(axis1, self._data_extractors[1], "b", "--")

        figure.tight_layout()
        self._data = []
        with tempfile.TemporaryFile(suffix="png") as image_file:
            print("debug send plot directly to reporter")
            pyplot.savefig(image_file, format="png")
            image_file.seek(0)
            self._image_reporter.send_image_by_handle(image_file)
        # pyplot.show()


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
        graph_notifier = GraphCollector(slack, AVAILABLE_QUANTITIES,
                                        data_count=config["plotting"]["data_count"])
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
