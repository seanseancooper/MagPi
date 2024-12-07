import glob
import os
import json
import logging.config

CONFIG_PATH = os.path.dirname(os.path.abspath(__file__))
LOG_PATH = os.path.join(CONFIG_PATH, '../../logs')

if not os.path.exists(LOG_PATH):
    os.mkdir(LOG_PATH)

logging.config.fileConfig(CONFIG_PATH + "/logging.conf",
                          defaults={"LOG_PATH": LOG_PATH},
                          disable_existing_loggers=False)


# def readConfig(config_file, config, non_config_files=None):
def readConfig(config_file, config):

    # if non_config_files is None:
    #     non_config_files = []

    if isinstance(config, dict):

        # # read ALL configs except... configurable as DEFAULT_NON_CONFIG_FILES
        # non_config_files.extend([os.path.basename(config_file), 'view.json', 'controller.json'])
        # configs = glob.glob(CONFIG_PATH + "/*.json")
        # [configs.remove(CONFIG_PATH + '/' + non_config) for non_config in non_config_files]

        with open(CONFIG_PATH + '/' + config_file, "r") as f:
            data = json.load(f)

            for category, settings in data.items():
                for setting in settings:
                    config[list(setting.keys()).pop(0)] = list(setting.values()).pop(0)
