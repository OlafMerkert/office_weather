# -*- coding: utf-8 -*-

from __future__ import print_function
import tempfile
from matplotlib import pyplot

IMAGE_FILE_FORMAT = "png"


class GraphCollector(object):

    def __init__(self, image_reporter, data_extractors, config):
        self._image_reporter = image_reporter
        self._data_extractors = data_extractors
        self._data_count = config["data_count"]
        self._plot_title = config["plot_title"]
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
            axis.set_ylabel("{0} [{1}]".format(extractor.label, extractor.unit),
                            color=color)
            axis.set_ylim([extractor.min_value, extractor.max_value])
            axis.tick_params("y", colors=color)

        x_data = list(map(lambda x: x.timestamp, self._data))
        figure, axis0 = pyplot.subplots()
        plot_extractor(axis0, self._data_extractors[0], "r", "-")

        axis1 = axis0.twinx()
        plot_extractor(axis1, self._data_extractors[1], "b", "--")

        figure.tight_layout()
        self._data = []
        with tempfile.TemporaryFile(suffix=IMAGE_FILE_FORMAT) as image_file:
            print("debug send plot directly to reporter")
            pyplot.savefig(image_file, format=IMAGE_FILE_FORMAT)
            image_file.seek(0)
            self._image_reporter.send_image_by_handle(image_file, self._plot_title)
        # pyplot.show()
