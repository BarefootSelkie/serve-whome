
function draw(members)
{

    members.sort((a,b) => a["memberName"].toLowerCase() > b["memberName"].toLowerCase())

    var listEl = document.getElementById("members")

    members.forEach(member => {
        var memberEl = document.createElement("li")

        var nameDiv = document.createElement("div")
        nameDiv.classList.add("name")
        nameDiv.appendChild(document.createTextNode(member["memberName"]))
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