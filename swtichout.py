#!/usr/bin/env python3

import requests
import json
import logging

# Logging setup
logging.basicConfig(format="%(asctime)s : %(message)s", filename="log.log", encoding='utf-8', level=logging.INFO)

# Load settings from files and set settings varibles
try:
    with open("data/apikeys.json", "r") as read_file:
        apikeys = json.load(read_file)
except:
    logging.critical("API Keys missing")
    exit()

systemid = apikeys["pluralkit"]["systemID"]
pktoken = apikeys["pluralkit"]["token"]

logging.info("Attempting to swtich out")
try:
    requests.post("https://api.pluralkit.me/v2/systems/" + systemid + "/switches",  headers={'Authorization':pktoken}, json={'members':[]})
except requests.exceptions.RequestException as e:
    # Fail silently
    logging.warning("Unable to swtich out")
    logging.warning(e) 
    