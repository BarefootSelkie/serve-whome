
function draw(members)
{

    members.sort((a,b) => a["memberName"].toLowerCase() > b["memberName"].toLowerCase())

    var listEl = document.getElementById("members")

    members.forEach(member => {
        var memberEl = document.createElement("li")

        var nameDiv = document.createElement("div")
        nameDiv.classList.add("name")
        var linkEl = document.createElement("a")
        linkEl.setAttribute("href", "https://dash.pluralkit.me/dash/m/" + member["memberId"])
        linkEl.appendChild(document.createTextNode(member["memberName"]))
        nameDiv.appendChild(linkEl)
        memberEl.appendChild(nameDiv)

        var cardDiv = document.createElement("div")
        cardDiv.classList.add("card")
        cardDiv.appendChild(document.createTextNode(member["cardsName"]))
        memberEl.appendChild(cardDiv)
        
        var elementDiv = document.createElement("div")
        elementDiv.classList.add("element")
        elementDiv.appendChild(document.createTextNode(member["elementName"]))
        memberEl.appendChild(elementDiv)
        
        listEl.appendChild(memberEl)
    });
}

fetch("./memberList.json")
  .then((response) => response.json())
  .then((json) => draw(json));