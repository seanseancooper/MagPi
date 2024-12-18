import threading
import logging
import time

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
        self.plugin.streamservice.force_stop()
        self.plugin.plugin_process_frames = False
        time.sleep(.01)

        self.plugin.streamservice = None
        self.plugin.tracker = None
        self.plugin.parent_thread = None

        self.plugin = None  # ?? thread ownership ??

    def cam_direction(self, direction):  # ?? crash happens w/o change of direction ??
        if not str(self.config['FORWARD_TEST_URL']) > '':
            return self.config[direction.upper() + '_VIDEO_URL']
        return self.config['FORWARD_TEST_URL']

    def cam_reload(self, direction):
        self.kill_plugin()
        self.init_plugin(ShowxatingBlackviewPlugin, direction)  # TODO: make plugin configurable
        self.plugin.run()  # ?? this may be part of the issue, run() called twice??

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
        #  how this is being run, may be the issue.
        #  the existing makes it 'owned' by the main thread; not a daemon.
        #  perhaps use:
        #  thread = threading.Thread(target=self.plugin.run, daemon=True)
        #  thread.start
        #  self.plugin = thread <-- camMgr thread attribute is not None.
        #  > thread management: any excessive threads.
        #  ?? will the plugin crash in a similar manner if not started by the camMgr ??

        self.plugin.run()  # ?? is this being called 2x on reload() ??

