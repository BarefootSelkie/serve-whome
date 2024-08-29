# serve-whome.py

**WARNING: This will create a copy of your pluralkit system on your local network, make sure your firewall and security settings are good enough that you are happy doing this**

A server for locally storing and serving data from plural kit, designed for use with my WhoMe projects. 

## Setup

This assumes that this code is being run by a user called **serve**

Clone into home directory
`git clone `

Get the pktools submodule
`cd pktools`
`git submodule init`
`git submodule update`

Make data directory ( just in case, should make own )
`mkdir ~/.whome`

Make data directory accessible to web server
`chmod 0755 ~`

Install nginx
`apt install nginx`

Edit nginx
`sudo nano /etc/nginx/sites-available/default`

Change the server location root to
`root /home/serve/.whome;`

Restart nginx to apply config change
`sudo systemctl restart nginx`

Install python venv support
`sudo apt install python3-venv`

Create the python venv
`python3 -m venv .venv`

Switch to the venv
`source .venv/bin/activate`

Install required packages
`pip install -r requirements.txt`

Copy the service file to the correct location
`sudo cp servewhome.service /lib/systemd/system/`

Enable and start the service
`sudo systemctl enable servewhome.service`
`sudo systemctl start servewhome.service`

## Debugging

Critical errors will appear in the systemctl log which can be accessed using:
`sudo journalctl -u servewhome.service`

Other errors will appear in the log file:
`/home/serve/log-servewhome.log`

## Data files

Data files are stored locally in **~/.whome**

**memberSeen** dictionary from shortCode to lastIn, lastOut, where lastIn is the most recent time a system member fronted when they were not already switched in, and lastOut is the most recent time a system member stopped fronting

**lastSwitch** switch object from pluralkit describing the most recent known switch

**pkMembers** full list of system members and information about these members pulled from PluralKit [see PluralKit documentation](https://pluralkit.me/api/models/)

**pkSwitches** backup of all switches pulled from PluralKit ( cureent only pulled by initialise and used for backup - future use in other stats )

**pkSystem** data pulled from PluralKit about the system itself (e.g. system name) [see PluralKit documentation](https://pluralkit.me/api/models/)

## Implemented functions

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

``0 0 * * * cd /home/serve/serve-whome && python3 ./switchout.py``
