from os import path
import json


# Default config class
class DefaultConfig(object):
    # Default configuration

    PORT = 50000
    MODES = ["manual"]


# Merge default config with actual config in a single file
Config = DefaultConfig
if path.exists("config.json"):
    conf = json.load(open("config.json", "r"))

    for prop in conf:
        setattr(Config, prop.upper(), conf[prop])
