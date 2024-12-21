import threading
import logging

from src.cam.Showxating.ShowxatingBlackviewPlugin import ShowxatingBlackviewPlugin
from src.config.__init__ import readConfig

cam_logger = logging.getLogger('cam_logger')


class CAMManager(threading.Thread):

    def __init__(self):
        super().__init__()
        self.config = {}
        self.plugin = None

        self.multibutton = {}
        self.statistics = {}                    # not used!

        self.streamservice = None
        self.streamservice_alive = None
        self.streamservice_thread = None

    def __str__(self):
        return f"CAMManager {str(self.config)}"

    def configure(self, config_file):
        readConfig(config_file, self.config)

        self.multibutton = {
            "OFF": self.config['MULTIBUTTON_OFF'],
            "SYM": self.config['MULTIBUTTON_SYM'],
            "ANA": self.config['MULTIBUTTON_ANA'],
            "ALL": self.config['MULTIBUTTON_ALL']
        }

    def _start_streamservice(self):
        self.streamservice_alive = True
        self.streamservice_thread = threading.Thread(target=self.streamservice, name='StreamService')
        self.streamservice_thread.daemon = True
        self.streamservice_thread.start()

    def _stop_streamservice(self):
        self.streamservice_alive = False
        self.streamservice_thread.join()

    def init_plugin(self, pluginClass, direction):
        self.plugin = pluginClass
        self.plugin.plugin_name = self.config['PLUGIN_NAME']
        self.plugin.plugin_args_capture_src = self.cam_direction(direction)
        self.plugin.get_config()

    def cam_direction(self, direction):
        if not str(self.config['FORWARD_TEST_URL']) > '':
            return self.config[direction.upper() + '_VIDEO_URL']
        return self.config['FORWARD_TEST_URL']

    def cam_reload(self, direction):
        self.plugin.stop()
        plugin = ShowxatingBlackviewPlugin()
        self.init_plugin(plugin, direction)  # TODO: make plugin configurable
        self.plugin.start()
        return 'OK'

    def cam_multibutton(self, mode):
        """ set mode of ShowxatingBlackviewPlugin """
        try:
            self.plugin.has_symbols, self.plugin.has_analysis, label = self.multibutton[mode]
            return label
        except KeyError:
            pass

    def set_plugin_field(self, field, value):
        self.plugin.set_field(field, value)
        return True

    def stop(self):
        self.plugin.stop()

    def main(self):
        plugin = ShowxatingBlackviewPlugin()
        self.init_plugin(plugin, "FORE")
        self.plugin.start()

        try:
            self.plugin.join()
        except KeyboardInterrupt:
            pass
        self.plugin.join()

    def run(self):
        self.main()
