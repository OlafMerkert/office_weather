# -*- coding: utf-8 -*-

from __future__ import print_function
from collections import namedtuple


DataExtractor = namedtuple("DataExtractor",
                           ["config_key",
                            "label",
                            "unit",
                            "min_value",
                            "max_value",
                            "extract"])

Boundary = namedtuple("Boundary", ["threshold", "message"])


class HystereseNotifier(object):

    def __init__(self, reporter, data_extractor, lower_boundary, upper_boundary):
        self._reporter = reporter
        self._above_upper = False
        self._lower_boundary = lower_boundary
        self._upper_boundary = upper_boundary
        self._data_extractor = data_extractor
        self._above_is_below = upper_boundary < lower_boundary

    def is_above(self, value, threshold):
        if self._above_is_below:
            return value < threshold
        else:
            return value > threshold

    def notify_value(self, value):
        if not self._above_upper and self.is_above(value, self._upper_boundary.threshold):
            self._above_upper = True
            self._reporter.send_message(self._upper_boundary.message.format(value))
        elif self._above_upper and not self.is_above(value, self._lower_boundary.threshold):
            self._above_upper = False
            self._reporter.send_message(self._lower_boundary.message.format(value))

    def notify(self, data):
        self.notify_value(self._data_extractor(data))


def HystereseNotifierFromConfig(reporter, data_extractor, config):
    return HystereseNotifier(reporter, data_extractor.extract,
                             lower_boundary=Boundary(threshold=config["lower_threshold"],
                                                     message=config["lower_message"]),
                             upper_boundary=Boundary(threshold=config["upper_threshold"],
                                                     message=config["upper_message"]))
