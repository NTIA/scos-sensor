import logging

logger = logging.getLogger(__name__)


class SignalAnalyzerMonitor:
    def __init__(self):
        logger.debug("Initializing Signal Analyzer Monitor")
        self._signal_analyzer = None

    def register_signal_analyzer(self, sigan):
        """
        Registers the signal analyzer so other scos components may access it. The
        registered signal analyzer will be accessible by importing
        signal_analyzer_monitor from utils.component_registrar and accessing the
        signal_analyzer property.

        :param sigan: the instance of a SignalAnalyzerInterface to register.
        """
        logger.debug(f"Setting Signal Analyzer to {sigan}")
        self._signal_analyzer = sigan

    @property
    def signal_analyzer(self):
        """
        Provides access to the registered signal analyzer.

        :return: the registered instance of a SignalAnalyzerInterface.
        """
        return self._signal_analyzer
