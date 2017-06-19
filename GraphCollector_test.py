# -*- coding: utf-8 -*-

from GraphCollector import GraphCollector, IMAGE_FILE_FORMAT
from HystereseNotifier_test import dummy_data, dummy_extractor, dummy_extractor2
from pathlib import Path
from shutil import copyfileobj

TEST_DATA_COUNT = 10

TEST_IMAGE_DIRECTORY = Path("test/images/GraphCollector/")

def fake_config():
    return {
        "plot_title": "Test plot",
        "data_count": TEST_DATA_COUNT,
    }

class FakeReporter:

    def __init__(self):
        self.fake_plot_titles = []
        TEST_IMAGE_DIRECTORY.mkdir(parents=True, exist_ok=True)

    def send_image_by_handle(self, image_file, title):
        self.fake_plot_titles.append(title)
        image_output_path = TEST_IMAGE_DIRECTORY / Path("{0}.{1}".format(title, IMAGE_FILE_FORMAT))
        with open(str(image_output_path), "wb") as output_file:
            copyfileobj(image_file, output_file)


class describe_GraphCollector:

    def setup_collector(self):
        reporter = FakeReporter()
        config = fake_config()
        collector = GraphCollector(reporter, [dummy_extractor, dummy_extractor2], config)

        return reporter, collector

    def it_does_not_generate_plots_on_insufficient_data(self):
        reporter, collector = self.setup_collector()
        for i in range(TEST_DATA_COUNT - 1):
            collector.notify(dummy_data(0))

        assert reporter.fake_plot_titles == []

    def it_generates_plots_on_sufficient_data(self):
        reporter, collector = self.setup_collector()

        for i in range(10 * TEST_DATA_COUNT + 2):
            collector.notify(dummy_data(1))

        assert reporter.fake_plot_titles[0] == "Test plot"
        assert len(reporter.fake_plot_titles) == 10

        for i in range(TEST_DATA_COUNT - 2):
            collector.notify(dummy_data(0.5 * i))

        assert len(reporter.fake_plot_titles) == 11
