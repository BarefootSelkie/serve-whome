#!/usr/bin/env python3

import logging
import yaml
import json
import os
import requests
import http.server
import socketserver
import socket
import threading
import time
import argparse
import datetime
import pktools

# Logging setup
logging.basicConfig(format="%(asctime)s : %(message)s", filename="pktserve.log", encoding='utf-8', level=logging.INFO)

# Load settings
try:
    with open("./config-pkts.yaml", "r") as read_file:
        config = yaml.safe_load(read_file)
except:
    logging.critical("Settings file missing")
    exit()

systemid = config["pluralkit"]["systemID"]
pktoken = config["pluralkit"]["token"]
zeropoint = config["pluralkit"]["zeropoint"]
rebuildRequired = False
updateRequired = False

# Web server setup

PORT = 8080

class Handler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=os.path.expanduser(config["data"]), **kwargs)
    def log_message(self, format, *args):
        return
    
def startWebServer():
    with socketserver.TCPServer(("", PORT), Handler) as httpd:
        httpd.serve_forever()

# argparse setup
parser = argparse.ArgumentParser()

parser.add_argument("-u", "--update", action="store_true", help="Update system, member, & group data")
parser.add_argument("-r", "--rebuild", action="store_true", help="Rebuild all data")

### Data store loading functions ###
# Loads in data stores and make globals from them
class pktState:
    def __init__(self):
        self.pkSystem = None
        self.pkMembers = None
        self.pkGroups = None
        self.lastSwitch = None
        self.memberSeen = {}
        self.dataLocation = os.path.expanduser(config["data"])

    def loadPkSystem(self):
        try:
            with open(self.dataLocation + "/pkSystem.json", "r") as lsFile:
                self.pkSystem = json.load(lsFile)
        except:
            logging.critical("Member data missing")
            exit()
    def loadPkMembers(self):
        try:
            with open(self.dataLocation + "/pkMembers.json", "r") as lsFile:
                self.pkMembers = json.load(lsFile)
        except:
            logging.critical("Member data missing")
            exit()
    def loadPkGroups(self):
        try:
            with open(self.dataLocation + "/pkGroups.json", "r") as lsFile:
                self.pkGroups = json.load(lsFile)
        except:
            logging.critical("Group data missing")
            exit()
    def loadLastSwitch(self):
        try:
            with open(self.dataLocation + "/lastSwitch.json", "r") as lsFile:
                self.lastSwitch = json.load(lsFile)
        except:
            logging.critical("Last switch data missing")
            exit()
    def loadMemberSeen(self):
        try:
            with open(self.dataLocation + "/memberSeen.json", "r") as lsFile:
                self.memberSeen = json.load(lsFile)
        except:
            logging.critical("Last seen data missing")
            exit()

    # Given a batch of switches, updates the MemberSeen data
    # Returns: timestamp of the oldest switch that was input
    def updateMemberSeen(self, switches):
        # Switches are currently in reverse chronological order - make them in chronological order instead
        switches.reverse()

        previousSwitch = None
        for thisSwitch in switches:
            
            # Skip the first switch in a batch
            if previousSwitch is None:
                previousSwitch = thisSwitch
                continue

            for pkid in previousSwitch["members"]:
                pkid = pkid.strip()
                if id not in thisSwitch["members"]:
                    # A system member has left as of this switch
                    if self.memberSeen[pkid]["lastOut"] < thisSwitch["timestamp"]:
                        self.memberSeen[pkid]["lastOut"] = thisSwitch["timestamp"]

            for pkid in thisSwitch["members"]:
                pkid = pkid.strip()
                if pkid not in previousSwitch["members"]:
                    # A system member has joined as of this switch
                    if self.memberSeen[pkid]["lastIn"] < thisSwitch["timestamp"]:
                        self.memberSeen[pkid]["lastIn"] = thisSwitch["timestamp"]
            
            previousSwitch = thisSwitch

        # Return timestamp for the switch that we are up-to-date after
        return switches[1]["timestamp"]

    ### Data store building functions ###

    # Get the raw system data from the PluralKit API and save it to disk
    def buildPkSystem(self):
        logging.info("( buildPkSystem )")
        try:
            r = requests.get("https://api.pluralkit.me/v2/systems/" + systemid, headers={'Authorization':pktoken})
            with open(os.path.expanduser(config["data"]) + "/pkSystem.json", "w") as systemFile:
                systemFile.write(r.text)
        except Exception as e:
            logging.warning("PluralKit requests.get ( buildPkSystem )")
            logging.warning(e) 

    # Get the raw data about system members from the PluralKit API and save it to disk
    def buildPkMembers(self):
        logging.info("( buildPkMembers )")
        try:
            r = requests.get("https://api.pluralkit.me/v2/systems/" + systemid + "/members", headers={'Authorization':pktoken})
            with open(os.path.expanduser(config["data"]) + "/pkMembers.json", "w") as memberFile:
                memberFile.write(r.text)
        except Exception as e:
            logging.warning("PluralKit requests.get ( buildPkMembers )")
            logging.warning(e) 

    # Get the raw data about system groups from the PluralKit API and save it to disk
    def buildPkGroups(self):
        logging.info("( buildPkGroups )")
        try:
            r = requests.get("https://api.pluralkit.me/v2/systems/" + systemid + "/groups?with_members=true", headers={'Authorization':pktoken})
            with open(os.path.expanduser(config["data"]) + "/pkGroups.json", "w") as groupsFile:
                groupsFile.write(r.text)
        except Exception as e:
            logging.warning("PluralKit requests.get ( buildPkGroups )")
            logging.warning(e)

    # Get the raw data about the most recent switch from the PluralKit API and save it to disk
    def buildLastSwitch(self):
        logging.info("( buildLastSwtich )")
        try:
            r = requests.get("https://api.pluralkit.me/v2/systems/" + systemid + "/switches?limit=1", headers={'Authorization':pktoken})
            switches = r.json()
            with open(os.path.expanduser(config["data"]) + "/lastSwitch.json", "w") as outputFile:
                outputFile.write(json.dumps(switches[0]))
        except Exception as e:
            logging.warning("PluralKit requests.get ( buildPkSwitch )")
            logging.warning(e)

    # Pulls entire switch history from pluralkit and builds memberSeen from this
    # useful for initial setup of data, in normal use would call PullPeriodic() instead
    # This function writes the updated memberSeen to disk
    # returns: eventually, can take several minutes to run
    def buildMemberSeen(self):
        # Warn the user that this takes a long time
        print("Rebuilding swtiches, this can take several minutes")
        logging.info("( buildMemberSeen )")
                     
        self.loadPkMembers()

        # Pluralkit requires us to request switches in batches of at most 100 a time
        # Keep track of where we have currently got up to
        pointer = datetime.datetime.now().isoformat(timespec="seconds") + "Z"

        # Initiailise the MemberSeen object so that we have an entry for all system members
        for member in self.pkMembers:  
            self.memberSeen[member["id"].strip()] = {"lastIn": zeropoint, "lastOut": zeropoint}  

        # Keep requesting batches of switches from pluralkit
        while True:
            try:
                time.sleep(1) # flood protection
                logging.info("Getting switches before " + pointer)
                r = requests.get("https://api.pluralkit.me/v2/systems/" + systemid + "/switches?limit=100&before=" + pointer, headers={'Authorization':pktoken})
                switches = r.json()        
                # Stop if we've reached the very last switch
                if (len(switches) < 2): break
                # Otherwise, use the batch of data we just received to update MemberSeen
                pointer = self.updateMemberSeen(switches)
            except requests.exceptions.RequestException as e:
                # Fail silently
                logging.warning("Unable to fetch front history block " + pointer)
                logging.warning(e) 

        # Update the memberSeen file on the disk
        with open(self.dataLocation + "/memberSeen.json", "w") as output_file:
            output_file.write(json.dumps(self.memberSeen))
            ### Periodic data update functions ###

    # Update information about current fronters and when they most recently switched in and out
    # Returns: True if a switch has happened since last update, False otherwise
    def pullPeriodic(self):
        switchOccurred = False

        # Get data about the most recent switches
        try:
            logging.info("Getting most recent switches")
            r = requests.get("https://api.pluralkit.me/v2/systems/" + systemid + "/switches?limit=100", headers={'Authorization':pktoken})
            switches = r.json()

            if (len(switches) > 1):
                # 1) Check to see if a switch has occured
                if ("id" not in self.lastSwitch) or (switches[0].strip() != self.lastSwitch["id"].strip()):
                    switchOccurred = True
                    self.lastSwitch = switches[0]
                    with open(self.dataLocation + "/lastSwitch.json", "w") as output_file:
                        output_file.write(json.dumps(self.lastSwitch))

                    # 3) Update the information about when fronters were last seen      
                    self.updateMemberSeen(switches)
                    with open(self.dataLocation + "/memberSeen.json", "w") as output_file:
                        output_file.write(json.dumps(self.memberSeen))

        except Exception as e:
            # Fail silently
            logging.warning("Unable to fetch recent switches ( pullPeriodic )")
            logging.warning(e) 

        return switchOccurred


### Discord message sending ###
# Used for notifiying of swtiches and also for server startup

def sendMessage(messageText, mode):
    logging.info("Sending Discord message")
    message = {"content": messageText}
    try:
        requests.post("https://discord.com/api/webhooks/" + str(config["discord"][mode]["serverID"]) + "/" + config["discord"][mode]["token"], message)
    except Exception as e:
        logging.warning("Discord error ( sendMessage )")
        logging.warning(e) 

### Main Code ###

# Check for passed in args and set flags as required
args = parser.parse_args()
if args.update:
    updateRequired = True
if args.rebuild:
    rebuildRequired = True

# If there is no directory to store the data create it
if not os.path.exists(os.path.expanduser(config["data"])):
    logging.info("No data store, creating directory")
    os.mkdir(os.path.expanduser(config["data"]))

# Create an object to represent the state of the system
state = pktState()

# Check that each file exists
if not os.path.exists(os.path.expanduser(config["data"] + "/pkSystem.json")):
    state.buildPkSystem()
if not os.path.exists(os.path.expanduser(config["data"] + "/pkMembers.json")):
    state.buildPkMembers()
if not os.path.exists(os.path.expanduser(config["data"] + "/pkGroups.json")):
    state.buildPkGroups()
if not os.path.exists(os.path.expanduser(config["data"] + "/lastSwitch.json")):
    state.buildLastSwitch()
if not os.path.exists(os.path.expanduser(config["data"] + "/memberSeen.json")):
    state.buildMemberSeen()

# Start the web server
try:
    threading.Thread(target=startWebServer, daemon=True).start()
    hostname = socket.gethostname()
    ipAdr = socket.gethostbyname(hostname)
    message = "pktserve up\n" + "http://" + str(ipAdr) + ":" + str(PORT)
    sendMessage(message, "full")
except Exception as e:
    logging.warning("Web server error ( main )")
    logging.warning(e)
    exit()

reloadRequired = True

### Loop Starts Here ###    
minutePast = 0

while True:

    if reloadRequired:
        state.loadPkSystem()
        state.loadPkMembers()
        state.loadPkGroups()
        state.loadLastSwitch()
        state.loadMemberSeen()
        reloadRequired = False               

    # If an update is required or forced by arg do the update
    if updateRequired:
        logging.info("Updating pkSystem, pkMembers, pkGroups, lastSwtich")
        state.buildPkSystem()
        state.buildPkMembers()
        state.buildPkGroups()
        state.buildLastSwitch()
        updateRequired = False
        reloadRequired = True

    # If a rebuild is required or forced by arg do the update
    if rebuildRequired:
        state.buildMemberSeen()
        rebuildRequired = False
        reloadRequired = True

    # Don't do anyting if the minute hasn't changed
    if minutePast != time.localtime()[4]:
        minutePast = time.localtime()[4]

        if ( time.localtime()[4] % config["updateInterval"] ) == 0:
            updateNeeded = state.pullPeriodic()

            # If pullPeriodic returns true update the screen and unset updateNeeded
            if updateNeeded:
                
                # Check if not switched out
                if len(state.lastSwitch["members"]) > 0:

                    # Build and send full message
                    if config["discord"]["full"]["enabled"]:
                        
                        
                                            
                        index = len(state.lastSwitch["members"])
                        message = "Hi, "
                    
                        for id in state.lastSwitch["members"]:

                            logging.info("sending discord message for user " + id)
                            index = index - 1
                            member, privacy = pktools.getMember(id, state.pkMembers)
                            message = message + member["name"]

                            if member["pronouns"] is not None:
                                message = message + " ( " + member["pronouns"] + " )"
                            
                            message = message + "\nYou last fronted:\n" + str(pktools.rsLastSeen(id, state.memberSeen))[:-10] + " ago\n" + str(pktools.hsTimeShort(pktools.hsLastSeen(id, state.memberSeen))) 

                            message = message + "\nYou last fronted:\n" + str(state.memberSeen[id]["lastOut"]) 
                            
                            if index != 0:
                                message = message + "\n---\n"
                        
                        sendMessage(message, "full")
                    
                    # Build and send filtered message
                    if config["discord"]["filtered"]["enabled"]:
                        
                        index = len(state.lastSwitch["members"])
                        message = "Hi, "
                        
                        for id in state.lastSwitch["members"]:
                            index = index - 1
                            member, privacy = pktools.getMember(id, state.pkMembers)
                            if privacy:
                                member, privacy = pktools.getMember(config["pluralkit"]["defaultFronter"], state.pkMembers)

                            flagGroup = [i for i in state.pkGroups if i["id"].strip() == config["pluralkit"]["flagGroup"]][0]
    
                            message = message + member["name"]
                            if member["pronouns"] is not None:
                                message = message + " ( " + member["pronouns"] + " )"
                            if member["uuid"] in flagGroup["members"]:
                                message = message + " 🔞"
                            if index != 0:
                                message = message + ", "
                        
                        sendMessage(message, "filtered")
                        
                updateNeeded = False

    

    # At 4:00 run an update

    time.sleep(10)
    print("running")