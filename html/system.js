
function draw(members)
{
    // Sort members alphabetically by name
    members.sort((a,b) => a["name"].toLowerCase() > b["name"].toLowerCase())

    // Get the HTML element to put the members into
    var listEl = document.getElementById("members")

    // For each system member
    members.forEach(member => {
        // Make an HTML element to hold the details of this member
        var memberEl = document.createElement("li")

        // Make the member name
        var nameDiv = document.createElement("div")
        nameDiv.classList.add("name")
        var linkEl = document.createElement("a")
        linkEl.setAttribute("href", "https://dash.pluralkit.me/dash/m/" + member["id"])
        linkEl.appendChild(document.createTextNode(member["name"]))
        nameDiv.appendChild(linkEl)
        memberEl.appendChild(nameDiv)

        // Make the card suit
        var cardDiv = document.createElement("div")
        cardDiv.classList.add("card")
        cardDiv.appendChild(document.createTextNode(member["cardSuit"]))
        memberEl.appendChild(cardDiv)
        
        // Make the element
        var elementDiv = document.createElement("div")
        elementDiv.classList.add("element")
        elementDiv.appendChild(document.createTextNode(member["elementName"]))
        memberEl.appendChild(elementDiv)
        
        // Add the list item to the list
        listEl.appendChild(memberEl)
    });
}

fetch("./memberList.json")
  .then((response) => response.json())
  .then((json) => draw(json));