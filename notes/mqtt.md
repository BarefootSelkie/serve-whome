# mqtt notes

home assistant needs a broadcast message to tell it that it should be listening to something and treating it as a device

## Mosquitto pub examples

**Config topic**
mosquitto_pub -h 192.168.1.10 -p 1883 -u whome -P whome -t homeassistant/sensor/whome-lmrvs-front/config -m '{"name": "First Front","state_topic": "whome-<systemid>/front","unique_id": "whome-<systemid>-front","device":{"identifiers": ["whome-<systemid>"],"name": "WhoMe: <systemname>"}}'

**Set topic**
mosquitto_pub -h 192.168.1.10 -p 1883 -u whome -P whome -t whome-<systemid>/front -m 'Test Switch'

## config topics

homeassistant/sensor/whome-<systemid>-name/config
{
  "name": "Name",
  "state_topic": "whome-<systemid>/front",
  "unique_id": "whome-<systemid>-front",
  "device":
  {
    "identifiers": ["whome-<systemid>"],
    "name": "WhoMe: <systemname>",
    "manfacturer": "github/barefootselkie",
    "model": "Serve-WhoMe",
    "sw_version": "0.1"
  }
}

homeassistant/sensor/whome-<systemid>-pronouns/config
{
  "name": "Pronouns",
  "state_topic": "whome-<systemid>/pronouns",
  "unique_id": "whome-<systemid>-pronouns",
  "device":
  {
    "identifiers": ["whome-<systemid>"]
  }
}

homeassistant/sensor/whome-<systemid>-lastout/config
{
  "name": "Last Seen",
  "state_topic": "whome-<systemid>/lastseen",
  "unique_id": "whome-<systemid>-lastseen",
  "device_class": "timestamp",
  "device":
  {
    "identifiers": ["whome-<systemid>"]
  }
}

homeassistant/sensor/whome-<systemid>-lastin/config
{
  "name": "Last In",
  "state_topic": "whome-<systemid>/lastin",
  "unique_id": "whome-<systemid>-lastin",
  "device_class": "timestamp"
  "device":
  {
    "identifiers": ["whome-<systemid>"]
  }
}