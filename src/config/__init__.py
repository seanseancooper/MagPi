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


def readConfig(config_file, config):

    if isinstance(config, dict):

        with open(CONFIG_PATH + '/' + config_file, "r") as f:
            data = json.load(f)

            for category, settings in data.items():
                for setting in settings:
                    config[list(setting.keys()).pop(0)] = list(setting.values()).pop(0)
