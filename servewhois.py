#!/usr/bin/env python3

import logging
import yaml
import json
import os
import requests
import time
import argparse
import datetime
from pktools import pktools

# Logging setup
logging.basicConfig(format="%(asctime)s : %(message)s", filename="servewhois.log", encoding='utf-8', level=logging.WARN)

# Load settings
try:
    with open("./config-servewhois.yaml", "r") as read_file:
        config = yaml.safe_load(read_file)
except:
    logging.critical("Settings file missing")
    exit()

systemid = config["pluralkit"]["systemID"]
pktoken = config["pluralkit"]["token"]
zeropoint = config["pluralkit"]["zeropoint"]
rebuildRequired = False
updateRequired = False

# argparse setup
parser = argparse.ArgumentParser()

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
        except Exception as e:
            logging.critical("pktState - loadPkSystem")
            logging.critical(e)
            exit()
    
    def loadPkMembers(self):
        try:
            with open(self.dataLocation + "/pkMembers.json", "r") as lsFile:
                self.pkMembers = json.load(lsFile)
        except Exception as e:
            logging.critical("pktState - loadPkMembers")
            logging.critical(e)
            exit()
    
    def loadPkGroups(self):
        try:
            with open(self.dataLocation + "/pkGroups.json", "r") as lsFile:
                self.pkGroups = json.load(lsFile)
        except Exception as e:
            logging.critical("pktState - loadPkGroup")
            logging.critical(e)
            exit()
    
    def loadLastSwitch(self):
        try:
            with open(self.dataLocation + "/lastSwitch.json", "r") as lsFile:
                self.lastSwitch = json.load(lsFile)
        except Exception as e:
            logging.critical("pktState - loadLastSwitch")
            logging.critical(e)
            exit()
    
    def loadMemberSeen(self):
        try:
            with open(self.dataLocation + "/memberSeen.json", "r") as lsFile:
                self.memberSeen = json.load(lsFile)
        except Exception as e:
            logging.critical("pktState - loadMemberSeen")
            logging.critical(e)
            exit()

### Data store building functions ###

    # Get the raw system data from the PluralKit API and store it to memory
    def getPkSystem(self):
        logging.info("( getPkSystem )")
        try:
            r = requests.get("https://api.pluralkit.me/v2/systems/" + systemid, headers={'Authorization':pktoken})
            self.pkSystem = json.loads(r.text)
        except Exception as e:
            logging.warning("PluralKit requests.get ( getPkSystem )")
            logging.warning(e) 

    def savePkSystem(self):
        with open(os.path.expanduser(config["data"]) + "/pkSystem.json", "w") as systemFile:
            systemFile.write(json.dumps(self.pkSystem))

    # Get the raw data about system members from the PluralKit API
    def getPkMembers(self):
        logging.info("( getPkMembers )")
        try:
            r = requests.get("https://api.pluralkit.me/v2/systems/" + systemid + "/members", headers={'Authorization':pktoken})
            self.pkMembers = json.loads(r.text)
        except Exception as e:
            logging.warning("PluralKit requests.get ( getPkMembers )")
            logging.warning(e) 
    
    def savePkMembers(self):
         with open(os.path.expanduser(config["data"]) + "/pkMembers.json", "w") as memberFile:
            memberFile.write(json.dumps(self.pkMembers))

    # Get the raw data about system groups from the PluralKit API
    def getPkGroups(self):
        logging.info("( getPkGroups )")
        try:
            r = requests.get("https://api.pluralkit.me/v2/systems/" + systemid + "/groups?with_members=true", headers={'Authorization':pktoken})
            self.pkGroups = json.loads(r.text)
        except Exception as e:
            logging.warning("PluralKit requests.get ( getPkGroups )")
            logging.warning(e)

    def savePkGroups(self):
        with open(os.path.expanduser(config["data"]) + "/pkGroups.json", "w") as groupsFile:
            groupsFile.write(json.dumps(self.pkGroups))

    # Get the raw data about the most recent switch from the PluralKit API
    def getLastSwitch(self):
        logging.info("( getLastSwitch )")
        try:
            r = requests.get("https://api.pluralkit.me/v2/systems/" + systemid + "/switches?limit=1", headers={'Authorization':pktoken})
            switches = r.json()
            self.lastSwitch = switches[0]
        except Exception as e:
            logging.warning("PluralKit requests.get ( getPkSwitch )")
            logging.warning(e)

    def saveLastSwitch(self):
        with open(os.path.expanduser(config["data"]) + "/lastSwitch.json", "w") as outputFile:
            outputFile.write(json.dumps(self.lastSwitch))

### Member Last Seen Logic ###

    # Given a batch of switches, updates the MemberSeen data
    # Returns: timestamp of the oldest switch that was input
    def updateMemberSeen(self, switches):

        # Ensure the MemberSeen object has an entry for all system members
        for member in self.pkMembers:
            if member["id"].strip() not in self.memberSeen.keys():
                self.memberSeen[member["id"].strip()] = {"lastIn": zeropoint, "lastOut": zeropoint}  

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

    # Pulls entire switch history from pluralkit and builds memberSeen from this
    # useful for initial setup of data, in normal use would call PullPeriodic() instead
    # This function writes the updated memberSeen to disk
    # returns: eventually, can take several minutes to run
    def buildMemberSeen(self):
        # Warn the user that this takes a long time
        print("Rebuilding switches, this can take several minutes")
        logging.info("( buildMemberSeen )")

        # Pluralkit requires us to request switches in batches of at most 100 a time
        # Keep track of where we have currently got up to
        pointer = datetime.datetime.now().isoformat(timespec="seconds") + "Z"

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

    def saveMemberSeen(self):
        # Update the memberSeen file on the disk
        with open(self.dataLocation + "/memberSeen.json", "w") as output_file:
            output_file.write(json.dumps(self.memberSeen))

    def getGroupById(self, id):
        for group in state.pkGroups:
            if group["id"].strip() == id:
                return group
        return None

    def buildMemberList(self):

        # 1) Make a dictionary (memberId -> card)
        cardlookup = {}
        for groupId in config["groups"]["cards"]:
            card = self.getGroupById(groupId)
            for memberId in card["members"]:
                cardlookup[memberId] = card

        # 2) Make a dictionary (member -> element)
        elementlookup = {}
        for groupId in config["groups"]["elements"]:
            element = self.getGroupById(groupId)
            for memberId in element["members"]:
                elementlookup[memberId] = element

        # 3) Create the list of members to output
        memberList = []
        for member in self.pkMembers:
            card = cardlookup[member["uuid"]] if member["uuid"] in cardlookup else None 
            element = elementlookup[member["uuid"]] if member["uuid"] in elementlookup else None 
            memberList.append({
                "memberName": member["name"],
                "memberId": member["id"],
                "memberPronouns": member["pronouns"],
                "cardsName": card["name"] if card is not None else "",
                "cardsId": card["id"] if card is not None else "",
                "elementName": element["name"] if element is not None else "",
                "elementId": element["id"] if element is not None else ""
            })

        # 4) Write the members list to a file
        with open(self.dataLocation + "/memberList.json", "w") as output_file:
            output_file.write(json.dumps(memberList))

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
                if ("id" not in self.lastSwitch) or (switches[0]["id"] != self.lastSwitch["id"]):
                    # 2) If it has, update the last switch file
                    switchOccurred = True
                    self.lastSwitch = switches[0]
                    with open(self.dataLocation + "/lastSwitch.json", "w") as output_file:
                        output_file.write(json.dumps(self.lastSwitch))

                    # 3) Check whether there are any new members we don't know about yet
                    for switch in switches:
                        for member in switch["members"]:
                            if member not in self.memberSeen.keys():
                                logging.info("Unable to find member, rebuilding member data")
                                self.getPkMembers()
                                continue

                    # 4) Update the information about when fronters were last seen      
                    self.updateMemberSeen(switches)
                    with open(self.dataLocation + "/memberSeen.json", "w") as output_file:
                        output_file.write(json.dumps(self.memberSeen))

        except Exception as e:
            # Fail silently
            logging.warning("Unable to fetch recent switches ( pullPeriodic )")
            logging.warning(e) 

        return switchOccurred

### Discord message sending ###
# Used for notifiying of switches and also for server startup

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
if args.rebuild:
    rebuildRequired = True

# If there is no directory to store the data create it
if not os.path.exists(os.path.expanduser(config["data"])):
    logging.info("No data store, creating directory")
    os.mkdir(os.path.expanduser(config["data"]))

# Create an object to represent the state of the system
state = pktState()

# Check that each file exists
if not os.path.exists(os.path.expanduser(config["data"] + "/pkSystem.json")) or rebuildRequired:
    state.getPkSystem()
    state.savePkSystem()
else:
    state.loadPkSystem()

if not os.path.exists(os.path.expanduser(config["data"] + "/pkMembers.json")) or rebuildRequired:
    state.getPkMembers()
    state.savePkMembers()
else:
    state.loadPkMembers()

if not os.path.exists(os.path.expanduser(config["data"] + "/pkGroups.json")) or rebuildRequired:
    state.getPkGroups()
    state.savePkGroups()
else:
    state.loadPkGroups()    
if not os.path.exists(os.path.expanduser(config["data"] + "/lastSwitch.json")) or rebuildRequired:
    state.getLastSwitch()
    state.saveLastSwitch()
else:
    state.loadLastSwitch()

if not os.path.exists(os.path.expanduser(config["data"] + "/memberSeen.json")) or rebuildRequired:
    state.buildMemberSeen()
    state.saveMemberSeen()
else:
    state.loadMemberSeen()

buildTest = False

### Loop Starts Here ###    
minutePast = 0

while True:  

    # Testing code, will be removed -sp
    if buildTest:
        state.buildMemberList()
        buildTest = False           

    # If an update is required or forced by arg do the update
    if updateRequired:
        logging.info("Updating pkSystem, pkMembers, pkGroups, lastSwitch from pluralkit")
        time.sleep(1)
        state.getPkSystem()
        state.savePkSystem()
        time.sleep(1)
        state.getPkMembers()
        state.savePkMembers()
        time.sleep(1)
        state.getPkGroups()
        state.savePkGroups()
        time.sleep(1)
        state.getLastSwitch()
        state.saveLastSwitch()
        time.sleep(1)
        updateRequired = False

    # Don't do anyting if the minute hasn't changed
    if minutePast != time.localtime()[4]:
        minutePast = time.localtime()[4]

        # At 04:00 run an update
        if time.localtime()[4] == 0 and time.localtime()[3] == 4:
            updateRequired = True

        if ( time.localtime()[4] % config["updateInterval"] ) == 0:

            # If pullPeriodic returns true we need to send Discord messages
            if state.pullPeriodic():
                
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
                            
                            if index == 0:
                                message = message + "\n---\n"
                                message = message + "Current headspace time:\n" + str(pktools.hsTimeEasy(pktools.hsTimeNow(zeropoint)))
                            
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
                        
    time.sleep(10)
#    print("running")