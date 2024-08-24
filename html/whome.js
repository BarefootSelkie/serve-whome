async function run() {
  var element = document.getElementById("data")
  var zeropoint = "2000-01-01T00:00:00Z"

  const url = "./lastSwitch.json";
  try {
    const response = await fetch(url);
    if (!response.ok) {
      throw new Error(`Response status: ${response.status}`);
    }

    const json = await response.json();
    console.log(json);
  } catch (error) {
    console.error(error.message);
  }

  element.innerHTML = hsTimeHuman(hsTimeNow(zeropoint))
}