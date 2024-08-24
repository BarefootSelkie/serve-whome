

async function run() {
  var element = document.getElementById("data")
  var zeropoint = "2000-01-01T00:00:00Z"

  var memberSeen = {}
  try {
    const response = await fetch("./memberSeen.json");
    if (!response.ok) {
      throw new Error(`Response status: ${response.status}`);
    }

    memberSeen = await response.json();
  } catch (error) {
    console.error(error.message);
  }

  var lastSwitch = {}
  try {
    const response = await fetch("./lastSwitch.json");
    if (!response.ok) {
      throw new Error(`Response status: ${response.status}`);
    }

    lastSwitch = await response.json();
  } catch (error) {
    console.error(error.message);
  }

  var memberList = {}
  try {
    const response = await fetch("./memberList.json");
    if (!response.ok) {
      throw new Error(`Response status: ${response.status}`);
    }

    memberList = await response.json();
  } catch (error) {
    console.error(error.message);
  }

  var currentFronters = lastSwitch["members"]

  memberList.forEach((member) => {
    if (member["memberId"] == currentFronters[0])
    {
      var rsFrontedSeconds = rsSinceLastIn(currentFronters[0], memberSeen)
      var humanRsFronted = new Date(rsFrontedSeconds * 1000).toISOString().slice(11, 16);
      element.innerHTML = member["memberName"] + ": " 
        + humanRsFronted + " = " + hsTimeHuman(hsSinceLastIn(currentFronters[0], memberSeen))
    }
  });

  setTimeout(run, 60 * 1000)

}