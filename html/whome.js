function run() {
  var element = document.getElementById("data")
  var zeropoint = "2000-01-01T00:00:00Z"
  element.innerHTML = hsTimeHuman(hsTimeNow(zeropoint))
}