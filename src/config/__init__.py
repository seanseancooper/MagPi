import os
import logging.config

CONFIG_PATH = os.path.dirname(os.path.abspath(__file__))
LOG_PATH = os.path.join(CONFIG_PATH, '../../logs')

if not os.path.exists(LOG_PATH):
    os.mkdir(LOG_PATH)

logging.config.fileConfig(CONFIG_PATH + "/logging.conf", defaults={"LOG_PATH": LOG_PATH}, disable_existing_loggers=False)


def readConfig(config_file, config):

    if isinstance(config, dict):
        with open(config_file, "r") as f:
            import json
            data = json.load(f)

            for category, settings in data.items():
                setting_list = {}

                for setting in settings:
                    setting_list[list(setting.keys()).pop(0)] = list(setting.values()).pop(0)

                    key = list(setting.keys()).pop(0)
                    value = list(setting.values()).pop(0)
                    config[key] = value
