role = %d;

if (role > 0) {
  var mlogin = document.getElementById("mlogin");
  mlogin.action = "login";
  while (mlogin.firstChild) { mlogin.removeChild(mlogin.firstChild); }

  var number = document.createElement("div");
  number.className = "inlined";
  number.innerText = role.toString();
  mlogin.appendChild(number);

  var submit = document.createElement("input");
  submit.type = "submit";
  submit.value = "Logout";
  mlogin.appendChild(submit);
}

var menu = document.getElementById("menu");
var i = 0;
while (menu.children[i]) {
  var name = menu.children[i].className;
  if (name && (name.includes("level-2") && role < 2) ||
    (name.includes("level-3") && role < 3) ||
    (name.includes("level-4)" && role < 4))) {
    menu.removeChild(menu.children[i]);
    continue;
  }
  i++;
}