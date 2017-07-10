# -*- coding: utf-8 -*-

from HystereseNotifier import DataExtractor, HystereseNotifierFromConfig
from collections import namedtuple
from datetime import datetime, timedelta

Dummy = namedtuple("Dummy", ["timestamp", "value", "other_value"])

dummy_extractor = DataExtractor(config_key="some_value",
                                label="Some Value",
                                unit="GB",
                                min_value=-10,
                                max_value=20,
                                extract=lambda x: x.value)

dummy_extractor2 = DataExtractor(config_key="some_other_value",
                                 label="Some Other Value",
                                 unit="EUR",
                                 min_value=-1,
                                 max_value=10,
                                 extract=lambda x: x.other_value)

timestamp_start = datetime(year=2017, month=10, day=12, hour=8, minute=10, second=30)
timestamp_offset = timedelta(seconds=5)

def mock_timestamp():
    global timestamp_start
    timestamp_start += timestamp_offset
    return timestamp_start

def dummy_data(value):
    return Dummy(timestamp=mock_timestamp(), value=value, other_value=0)

def fake_config():
    return {
        "lower_threshold": 20,
        "lower_message": "lower:{0}",
        "upper_threshold": 40,
        "upper_message": "upper:{0}",
    }

class FakeReporter:

    def __init__(self):
        self.fake_messages = []

    def send_message(self, message):
        self.fake_messages.append(message)

class describe_HystereseNotifier:

    def setup_notifier(self):
        reporter = FakeReporter()
        config = fake_config()
        notifier = HystereseNotifierFromConfig(reporter, dummy_extractor, config)
        return reporter, notifier

    def it_reports_nothing_when_values_are_within_range(self):
        reporter, notifier = self.setup_notifier()

        for value in [20, 21, 22, 30, 40]:
            notifier.notify(dummy_data(value))

        assert reporter.fake_messages == []

    def it_reports_nothing_when_values_are_lower(self):
        reporter, notifier = self.setup_notifier()

        for value in [20, 19, 10, 30]:
            notifier.notify(dummy_data(value))

        assert reporter.fake_messages == []

    def it_reports_only_once_when_values_are_higher(self):
        reporter, notifier = self.setup_notifier()

        for value in [40, 42, 50, 40]:
            notifier.notify(dummy_data(value))

        assert reporter.fake_messages == ["upper:42"]

    def it_reports_once_when_values_were_higher_and_then_lower_again(self):
        reporter, notifier = self.setup_notifier()

        for value in [40, 42, 30, 20, 19]:
            notifier.notify(dummy_data(value))

        assert reporter.fake_messages == ["upper:42", "lower:20"]

    def it_reports_when_values_go_higher_and_lower_repeatedly(self):
        reporter, notifier = self.setup_notifier()

        for value in [30, 42, 50, 40, 20, 19, 31, 44, 34, 18]:
            notifier.notify(dummy_data(value))

        assert reporter.fake_messages == ["upper:42",
                                          "lower:20",
                                          "upper:44",
                                          "lower:18"]

    def it_reports_nothing_when_only_another_value_changes(self):
        reporter, notifier = self.setup_notifier()

        for other_value in [30, 42, 50, 40, 20, 19, 31, 44, 34, 18]:
            notifier.notify(Dummy(timestamp=mock_timestamp(), value=30, other_value=other_value))

        assert reporter.fake_messages == []
