#!/usr/bin/env python3

import requests
import yaml
import logging

# Logging setup
logging.basicConfig(format="%(asctime)s : %(message)s", filename="log-switchout.log", encoding='utf-8', level=logging.INFO)

# Load config file
try:
    with open("./config-serve-whome.yaml", "r") as read_file:
        config = yaml.safe_load(read_file)
except:
    logging.critical("Settings file missing")
    exit()

systemid = config["pluralkit"]["systemID"]
pktoken = config["pluralkit"]["token"]

logging.info("Attempting to swtich out")
try:
    requests.post("https://api.pluralkit.me/v2/systems/" + systemid + "/switches",  headers={'Authorization':pktoken}, json={'members':[]})
except requests.exceptions.RequestException as e:
    # Fail silently
    logging.warning("Unable to swtich out")
    logging.warning(e) 
    