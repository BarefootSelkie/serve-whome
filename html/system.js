
function draw(members)
{

    var listEl = document.getElementById("members")

    members.forEach(member => {
        var memberEl = document.createElement("li")
        var name = document.createTextNode(member["name"])
        memberEl.appendChild(name)
        listEl.appendChild(memberEl)
    });
}

fetch("./memberList.json")
  .then((response) => response.json())
  .then((json) => draw(json));