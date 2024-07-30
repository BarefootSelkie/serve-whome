fetch("https://127.0.0.1/memberList.json")
  .then((response) => response.json())
  .then((json) => console.log(json));