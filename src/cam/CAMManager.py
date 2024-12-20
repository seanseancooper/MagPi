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
        self.thread = None

        self.multibutton = {}
        self.statistics = {}                    # not used!

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

    def init_plugin(self, pluginClass, direction):  # ?? what does this arm-twisting buy me ??
        self.plugin = pluginClass()
        self.plugin.plugin_name = self.config['PLUGIN_NAME']
        self.plugin.plugin_args_capture_src = self.cam_direction(direction)
        self.plugin.get_config()

    def kill_plugin(self):  # too much work to shutdown, this is.
        self.plugin.stop_streamservice()
        self.plugin.tracker = None
        self.plugin = None

    def cam_direction(self, direction):
        if not str(self.config['FORWARD_TEST_URL']) > '':
            return self.config[direction.upper() + '_VIDEO_URL']
        return self.config['FORWARD_TEST_URL']

    def cam_reload(self, direction):
        self.kill_plugin()
        self.init_plugin(ShowxatingBlackviewPlugin, direction)  # TODO: make plugin configurable
        if not self.thread:
            self.thread = threading.Thread(target=self.plugin.run, name='BVPlugin').start()
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
        self.kill_plugin()

    def run(self):
        self.init_plugin(ShowxatingBlackviewPlugin, "FORE")
        if not self.thread:
            # this doesn't do what I thought it does. No thread!
            t_thread = threading.Thread(target=self.plugin.run, name='BVPlugin').start()
            self.thread = t_thread
            pass
