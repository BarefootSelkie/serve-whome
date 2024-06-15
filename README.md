# servewhois.py

**WARNING: This will create a copy of your pluralkit system on your local network, make sure your firewall and security settings are good enough that you are happy doing this**

A server for locally storing and serving data from plural kit, designed for use with my einkwhois projects. 

## Data files

Data files are stored locally in **~/.servewhois**

**memberSeen** dictionary from shortCode to lastIn, lastOut, where lastIn is the most recent time a system member fronted when they were not already switched in, and lastOut is the most recent time a system member stopped fronting

**lastSwitch** switch object from pluralkit describing the most recent known switch

**pkMembers** full list of system members and information about these members pulled from PluralKit [see PluralKit documentation](https://pluralkit.me/api/models/)

**pkSwitches** backup of all switches pulled from PluralKit ( cureent only pulled by initialise and used for backup - future use in other stats )

**pkSystem** data pulled from PluralKit about the system itself (e.g. system name) [see PluralKit documentation](https://pluralkit.me/api/models/)

## Implimented functions

pullMemberSeen()

pullPeriodic() - gets info about the most recent switch, and updates the list of current fronters and stats, and a boolean to indicate if the current fronter information has changed


## Missing functions

pullSystem()
pullMembers()

allTime(member) - if member is included returns their total fronting time, if no member provided returns a list of all members and each of their total fronting time

allPercent(member) - returns a list of all members and their percentage of fronting

recientTime(member) - returns the amount of time that a member has fronted for in the last cycle

recientPercent(member) - returns the percentage of time a member has been fronting for in the last cycle

# swtichout.py

This is a very simple script that simply switches all fronters out when run, it is designed to be run by a cron job to switch out when I've fallen asleep, so that people don't log time when I'm actually just asleep.

### Cron job for switchout.py

``0 0 * * * cd /home/[user] && python3 ./switchout.py``

Will need to replace [user] with the username of the user that runs the server