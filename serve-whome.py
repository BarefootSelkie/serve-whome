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


# argparse setup
parser = argparse.ArgumentParser()

# avaible arguments
parser.add_argument("-r", "--rebuild", action="store_true", help="Rebuild all data")
parser.add_argument("-v", "--verbose", action="store_true", help="Enable info level logging")

# Check for passed in args and set flags as required
args = parser.parse_args()
if args.rebuild:
  rebuildRequired = True

# Logging setup
if args.verbose:
  logging.basicConfig(format="%(asctime)s : %(message)s", filename="log-serve-whome.log", encoding='utf-8', level=logging.INFO)
else:
  logging.basicConfig(format="%(asctime)s : %(message)s", filename="log-serve-whome.log", encoding='utf-8', level=logging.WARN)

# Load config
try:
  with open("./config-serve-whome.yaml", "r") as read_file:
    config = yaml.safe_load(read_file)
except:
  logging.critical("Settings file missing")
  exit()

systemid = config["pluralkit"]["systemID"]
pktoken = config["pluralkit"]["token"]
zeropoint = config["pluralkit"]["zeropoint"]
rebuildRequired = False
updateRequired = False

### Data store loading functions ###
# Loads in data stores and make globals from them
class pktState:
  def __init__(self):
    self.pkSystem = None
    self.pkMembers = None
    self.pkGroups = None
    self.lastSwitch = None
    self.currentFronters = None
    self.memberSeen = {}
    self.dataLocation = os.path.expanduser(config["data"])


### local file loading and saving ###

  def loadPkSystem(self):
    try:
      with open(self.dataLocation + "/pkSystem.json", "r") as lsFile:
        self.pkSystem = json.load(lsFile)
    except Exception as e:
      logging.critical("pktState - loadPkSystem")
      logging.critical(e)
      exit()
  
  def savePkSystem(self):
    with open(os.path.expanduser(config["data"]) + "/pkSystem.json", "w") as systemFile:
      systemFile.write(json.dumps(self.pkSystem))

  def loadPkMembers(self):
    try:
      with open(self.dataLocation + "/pkMembers.json", "r") as lsFile:
        self.pkMembers = json.load(lsFile)
    except Exception as e:
      logging.critical("pktState - loadPkMembers")
      logging.critical(e)
      exit()

  def savePkMembers(self):
     with open(os.path.expanduser(config["data"]) + "/pkMembers.json", "w") as memberFile:
      memberFile.write(json.dumps(self.pkMembers))

  def loadPkGroups(self):
    try:
      with open(self.dataLocation + "/pkGroups.json", "r") as lsFile:
        self.pkGroups = json.load(lsFile)
    except Exception as e:
      logging.critical("pktState - loadPkGroup")
      logging.critical(e)
      exit()

  def savePkGroups(self):
    with open(os.path.expanduser(config["data"]) + "/pkGroups.json", "w") as groupsFile:
      groupsFile.write(json.dumps(self.pkGroups))
  
  def loadLastSwitch(self):
    try:
      with open(self.dataLocation + "/lastSwitch.json", "r") as lsFile:
        self.lastSwitch = json.load(lsFile)
    except Exception as e:
      logging.critical("pktState - loadLastSwitch")
      logging.critical(e)
      exit()

  def saveLastSwitch(self):
    with open(os.path.expanduser(config["data"]) + "/lastSwitch.json", "w") as outputFile:
      outputFile.write(json.dumps(self.lastSwitch))
  
  def loadMemberSeen(self):
    try:
      with open(self.dataLocation + "/memberSeen.json", "r") as lsFile:
        self.memberSeen = json.load(lsFile)
    except Exception as e:
      logging.critical("pktState - loadMemberSeen")
      logging.critical(e)
      exit()

  def saveMemberSeen(self):
    with open(self.dataLocation + "/memberSeen.json", "w") as output_file:
      output_file.write(json.dumps(self.memberSeen))

  def loadMemberList(self):
    try:
      with open(self.dataLocation + "/memberList.json", "r") as lsFile:
        self.memberList = json.load(lsFile)
    except Exception as e:
      logging.critical("pktState - loadMemberList")
      logging.critical(e)
      exit()

  def saveMemberList(self):
    with open(self.dataLocation + "/memberList.json", "w") as output_file:
      output_file.write(json.dumps(self.memberList))

  # currentFronters is live data, so is never loaded from disc, but will be saved to be accessible via web requests
  def saveCurrentFronters(self):
    with open(self.dataLocation + "/currentFronters.json", "w") as output_file:
      output_file.write(json.dumps(self.currentFronters))


### api calls ###

  # Get the raw system data from the PluralKit API and store it to memory
  def makeApiCallPkSystem(self):
    logging.info("( makeApiCallPkSystem )")
    try:
      r = requests.get("https://api.pluralkit.me/v2/systems/" + systemid, headers={'Authorization':pktoken})
      self.pkSystem = json.loads(r.text)
    except Exception as e:
      logging.warning("PluralKit requests.get ( makeApiCallPkSystem )")
      logging.warning(e) 

  # Get the raw data about system members from the PluralKit API
  def makeApiCallPkMembers(self):
    logging.info("( makeApiCallPkMembers )")
    try:
      r = requests.get("https://api.pluralkit.me/v2/systems/" + systemid + "/members", headers={'Authorization':pktoken})
      self.pkMembers = json.loads(r.text)
    except Exception as e:
      logging.warning("PluralKit requests.get ( makeApiCallPkMembers )")
      logging.warning(e) 
  
  # Get the raw data about system groups from the PluralKit API
  def makeApiCallPkGroups(self):
    logging.info("( makeApiCallPkGroups )")
    try:
      r = requests.get("https://api.pluralkit.me/v2/systems/" + systemid + "/groups?with_members=true", headers={'Authorization':pktoken})
      self.pkGroups = json.loads(r.text)
    except Exception as e:
      logging.warning("PluralKit requests.get ( makeApiCallPkGroups )")
      logging.warning(e)

  # Get the raw data about the most recent switch from the PluralKit API
  def makeApiCallLastSwitch(self):
    logging.info("( makeApiCallLastSwitch )")
    try:
      r = requests.get("https://api.pluralkit.me/v2/systems/" + systemid + "/switches?limit=1", headers={'Authorization':pktoken})
      switches = r.json()
      self.lastSwitch = switches[0]
    except Exception as e:
      logging.warning("PluralKit requests.get ( makeApiCallPkSwitch )")
      logging.warning(e)


### Utility funcations ###

  def getGroupById(self, id):
    for group in state.pkGroups:
      if group["id"].strip() == id:
        return group
    return None

  # Return a dictionary of which group members are in
  def getGroupMemberships(self, groupType):
    output = {}
    for groupId in config["groups"][groupType]:
      group = self.getGroupById(groupId)
      for memberId in group["members"]:
        output[memberId] = group
    return output

  # Check to see if the member is set to visible
  def checkVisible(self, member):
    if member["privacy"]["visibility"] == "public":
      return True
    else:
      return False

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

      # Check to see which members have switched out in this switch  
      for pkid in previousSwitch["members"]:
        pkid = pkid.strip() # removes trailing spaces that pk sometimes adds
        if pkid not in thisSwitch["members"]:
          # A system member has left as of this switch
          if self.memberSeen[pkid]["lastOut"] < thisSwitch["timestamp"]:
            self.memberSeen[pkid]["lastOut"] = thisSwitch["timestamp"]

      # Check to see which members have switched in in this switch
      for pkid in thisSwitch["members"]:
        pkid = pkid.strip() # removes trailing spaces that pk sometimes adds
        if pkid not in previousSwitch["members"]:
          # A system member has joined as of this switch
          if self.memberSeen[pkid]["lastIn"] < thisSwitch["timestamp"]:
            self.memberSeen[pkid]["lastIn"] = thisSwitch["timestamp"]
      
      # Overwrite the out dated swtich with the new data
      previousSwitch = thisSwitch

    # Return timestamp for the switch that we are up-to-date after
    return switches[1]["timestamp"]

  # Pulls entire switch history from pluralkit and builds memberSeen from this, this is only used if the memberSeen.json is missing, if it is there it'll just use updateMemberSeen(), this will take several minutes to run thought due to amount of data and having to rate limit to not flood pk
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


### data sets for other WhoMe projects ###

  def updateCurrentFronters(self):
    self.currentFronters = {
      "switch": {
        "id": self.lastSwitch["id"],
        "timestamp": self.lastSwitch["timestamp"]
      },
      "system": {
        "name": self.pkSystem["name"],
        "pronouns": self.pkSystem["pronouns"]
      },
      "members": []
    }

    # 1) Find out what the card and element is for each system member
    cardlookup = self.getGroupMemberships("cards")
    elementlookup = self.getGroupMemberships("elements")

    # 2) Get details for each fronter
    for memberId in self.lastSwitch["members"]:
      member = [i for i in self.pkMembers if i["id"] == memberId][0]
      card = cardlookup[member["uuid"]] if member["uuid"] in cardlookup else None 
      element = elementlookup[member["uuid"]] if member["uuid"] in elementlookup else None 
      self.currentFronters["members"].append({
        "name": member["name"],
        "id": member["id"],
        "pronouns": member["pronouns"],
        "cardSuit": card["name"] if card is not None else "",
        "cardId": card["id"] if card is not None else "",
        "elementName": element["name"] if element is not None else "",
        "elementId": element["id"] if element is not None else "",
        "lastIn": self.memberSeen[memberId]["lastIn"],
        "lastOut": self.memberSeen[memberId]["lastOut"],
        "visible": self.checkVisible(member)
      })

  def buildMemberList(self):

    self.memberList = []

    # Make lookups for groups
    cardlookup = self.getGroupMemberships("cards")
    elementlookup = self.getGroupMemberships("elements")

    # Create the list of members to output
    for member in self.pkMembers:

      # check if this is a member that should not appear in the list
      if member["id"] in list(config["covers"].values()):
        # skip this member as they are just a 'cover' member
        continue

      card = cardlookup[member["uuid"]] if member["uuid"] in cardlookup else None 
      element = elementlookup[member["uuid"]] if member["uuid"] in elementlookup else None 
      self.memberList.append({
        "name": member["name"],
        "id": member["id"],
        "pronouns": member["pronouns"],
        "cardSuit": card["name"] if card is not None else "",
        "cardId": card["id"] if card is not None else "",
        "elementName": element["name"] if element is not None else "",
        "elementId": element["id"] if element is not None else "",
        "visible": self.checkVisible(member)
      })


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

      # Check to see if a list has been returned from the request
      if (len(switches) > 1):

        # 1) Check to see if a switch has occured
        if ("id" not in self.lastSwitch) or (switches[0]["id"] != self.lastSwitch["id"]):
          # 2) If it has, update the last switch file
          switchOccurred = True
          self.lastSwitch = switches[0]
          self.saveLastSwitch()

          # 3) Check whether there are any new members we don't know about yet
          for switch in switches:
            for member in switch["members"]:
              if member not in self.memberSeen.keys():
                logging.info("Unable to find member, rebuilding member data")
                self.makeApiCallPkMembers()
                self.savePkMembers()
                continue

          # 4) Update the information about when fronters were last seen, it's here as it needs the swtiches from the api request
          self.updateMemberSeen(switches)
          self.saveMemberSeen()
          
    except Exception as e:
      # Fail silently
      logging.warning("Unable to fetch recent switches ( pullPeriodic )")
      logging.warning(e)

    return switchOccurred


### Discord message sending ###
# Used for notifiying of switches and also for server startup
def messageShort():
  index = len(state.currentFronters["members"])
  message = "Hi, "
  
  for member in state.currentFronters["members"]:
    index = index - 1
    
    if member["visible"]:
      message = message + member["name"]
      if member["pronouns"] is not None:
        message = message + " ( " + member["pronouns"] + " )"
    else:
      message = message + state.pkSystem["name"]
      if "pronouns" in state.pkSystem and state.pkSystem["pronouns"] is not None:
        message = message + " ( " + state.pkSystem["pronouns"] + " )"

    if "cardSuit" in member and member["cardSuit"] is not None:
      message = message + " " + member["cardSuit"]

    match index:
      case 0: message = message
      case 1: message = message + ", and "
      case _: message = message + ", "
      
  return message

def messageLong():
  index = len(state.currentFronters["members"])
  message = "Hi, "

  for member in state.currentFronters["members"]:

    index = index - 1
    message = message + member["name"]

    if "pronouns" in state.pkSystem and member["pronouns"] is not None:
      message = message + " ( " + member["pronouns"] + " )"

    message = message + "\nYou last fronted:\n" + str(pktools.rsLastSeen(member["id"], state.memberSeen))[:-10] + " ago"

    message = message + "\nAt:\n" + datetime.datetime.fromisoformat(member["lastOut"]).strftime("%H:%M on %A ( %x )")

    message = message + "\nIn headpsace time:\n" + str(pktools.hsTimeHuman(pktools.hsLastSeen(member["id"], state.memberSeen))) 

    if index == 0:
      message = message + "\n---\n"
      message = message + "Current headspace time:\n" + str(pktools.hsTimeEasy(pktools.hsTimeNow(zeropoint)))
    else:
      message = message + "\n---\n"

  return message

def messageSend(messageText, mode):
  logging.info("Sending Discord message")
  message = {"content": messageText}
  try:
    requests.post("https://discord.com/api/webhooks/" + str(config["discord"][mode]["serverID"]) + "/" + config["discord"][mode]["token"], message)
  except Exception as e:
    logging.warning("Discord error ( sendMessage )")
    logging.warning(e)

### Main Code ###

# If there is no directory to store the data create it
if not os.path.exists(os.path.expanduser(config["data"])):
  logging.info("No data store, creating directory")
  os.mkdir(os.path.expanduser(config["data"]))
os.popen('cp ./html/* ' + os.path.expanduser(config["data"]))
os.popen('cp ./pktools/pktools.js ' + os.path.expanduser(config["data"]))

# Create an object to represent the state of the system
state = pktState()

# Check that each file exists
if not os.path.exists(os.path.expanduser(config["data"] + "/pkSystem.json")) or rebuildRequired:
  state.makeApiCallPkSystem()
  state.savePkSystem()
else:
  state.loadPkSystem()

if not os.path.exists(os.path.expanduser(config["data"] + "/pkMembers.json")) or rebuildRequired:
  state.makeApiCallPkMembers()
  state.savePkMembers()
else:
  state.loadPkMembers()

if not os.path.exists(os.path.expanduser(config["data"] + "/pkGroups.json")) or rebuildRequired:
  state.makeApiCallPkGroups()
  state.savePkGroups()
else:
  state.loadPkGroups()
if not os.path.exists(os.path.expanduser(config["data"] + "/lastSwitch.json")) or rebuildRequired:
  state.makeApiCallLastSwitch()
  state.saveLastSwitch()
else:
  state.loadLastSwitch()

if not os.path.exists(os.path.expanduser(config["data"] + "/memberSeen.json")) or rebuildRequired:
  state.buildMemberSeen()
  state.saveMemberSeen()
else:
  state.loadMemberSeen()

if not os.path.exists(os.path.expanduser(config["data"] + "/memberList.json")) or rebuildRequired:
  state.buildMemberList()
  state.saveMemberList()
else:
  state.loadMemberList()

### Loop Starts Here ###
minutePast = 0

while True:

  # If an update is required or forced by arg do the update
  if updateRequired:
    logging.info("Updating pkSystem, pkMembers, pkGroups, lastSwitch from pluralkit")
    time.sleep(1)
    state.makeApiCallPkSystem()
    state.savePkSystem()
    time.sleep(1)
    state.makeApiCallPkMembers()
    state.savePkMembers()
    time.sleep(1)
    state.makeApiCallPkGroups()
    state.savePkGroups()
    time.sleep(1)
    state.makeApiCallLastSwitch()
    state.saveLastSwitch()
    time.sleep(1)
    state.buildMemberList()
    state.saveMemberList()
    time.sleep(1)
    updateRequired = False

  # Don't do anyting if the minute hasn't changed
  if minutePast != time.localtime()[4]:
    minutePast = time.localtime()[4]

    # At 04:00 run an update
    if time.localtime()[4] == 0 and time.localtime()[3] == 4:
      updateRequired = True

    # If the current minute devided by the update intervate is ture
    if ( time.localtime()[4] % config["updateInterval"] ) == 0:

      # If pullPeriodic returns true we need to send Discord messages
      if state.pullPeriodic():
        
        # Update the current fronters file
        state.updateCurrentFronters()
        state.saveCurrentFronters()

        # Check if not switched out
        if len(state.lastSwitch["members"]) > 0:

          # Build and send full message
          if config["discord"]["full"]["enabled"]:
            message = messageLong()
            messageSend(message, "full")
          
          # Build and send filtered message
          if config["discord"]["filtered"]["enabled"]:
            message = messageShort()
            messageSend(message, "filtered")
            
  time.sleep(10)
