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

  for (var member in memberList) {
    if (member["memberId"] == currentFronters[0])
    {
      element.innerHTML = member["memberName"]
    }
  }

}